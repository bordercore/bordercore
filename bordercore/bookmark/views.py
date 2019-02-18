import datetime
import json
import lxml.html as lh

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django_datatables_view.base_datatable_view import BaseDatatableView
import requests

from accounts.models import SortOrder
from bookmark.models import Bookmark, BookmarkTagUser
from bookmark.forms import BookmarkForm
from bookmark.tasks import snarf_favicon
from tag.models import Tag

SECTION = 'Bookmarks'


@login_required
def bookmark_list(request):

    bookmarks = []

    untagged_count = Bookmark.objects.filter(user=request.user, tags__isnull=True).count()

    return render(request, 'bookmark/index.html',
                  {'section': SECTION,
                   'bookmarks': bookmarks,
                   'cols': ['Date', 'url', 'title', 'id'],
                   'untagged_count': untagged_count})


@login_required
def bookmark_click(request, bookmark_id=None):

    b = Bookmark.objects.get(user=request.user, pk=bookmark_id) if bookmark_id else None
    b.daily['viewed'] = 'true'
    b.save()
    return redirect(b.url)


@login_required
def bookmark_edit(request, bookmark_id=None):

    action = 'Edit'

    b = Bookmark.objects.get(user=request.user, pk=bookmark_id) if bookmark_id else None

    if request.method == 'POST':
        if request.POST['Go'] in ['Edit', 'Add']:
            form = BookmarkForm(request.POST, instance=b, request=request)  # A form bound to the POST data
            if form.is_valid():
                newform = form.save(commit=False)
                newform.user = request.user
                newform.save()
                form.save_m2m()  # Save the many-to-many data for the form.
                snarf_favicon.delay(form.instance.url)
                messages.add_message(request, messages.INFO, 'Bookmark edited')
                return bookmark_list(request)
        elif request.POST['Go'] == 'Delete':
            b.delete()
            messages.add_message(request, messages.INFO, 'Bookmark deleted')
            return bookmark_list(request)

    elif bookmark_id:
        action = 'Edit'
        form = BookmarkForm(instance=b, request=request)

    else:
        action = 'Add'
        form = BookmarkForm(request=request)  # An unbound form

    return render(request, 'bookmark/edit.html',
                  {'section': SECTION,
                   'action': action,
                   'form': form})


@login_required
def bookmark_delete(request, bookmark_id=None):

    # First delete the bookmark from any tag lists
    info = BookmarkTagUser.objects.raw("SELECT * FROM bookmark_bookmarktaguser WHERE user_id = %s AND %s = ANY (bookmark_list)", [request.user.id, bookmark_id])
    for tag in info:
        tag.bookmark_list.remove(bookmark_id)
        tag.save()

    # Then delete the actual bookmark
    bookmark = Bookmark.objects.get(user=request.user, pk=bookmark_id)
    bookmark.delete()

    return HttpResponse(json.dumps('OK'), content_type="application/json")


@login_required
def snarf_link(request):

    from html.parser import HTMLParser
    h = HTMLParser()

    url = request.GET['url']
    title = h.unescape(request.GET['title'])

    # First verify that this url does not already exist
    try:
        b = Bookmark.objects.get(user=request.user, url=url)
        messages.add_message(request, messages.WARNING, 'Bookmark already exists and was added on %s' % b.created.strftime("%B %d, %Y"))
        return redirect('bookmark_edit', b.id)
    except ObjectDoesNotExist:
        b = Bookmark(is_pinned=False, user=request.user, url=url, title=title)
        b.save()
        snarf_favicon.delay(url)

    return redirect('bookmark_edit', b.id)


@login_required
def tag_search(request):

    tags = Tag.objects.filter(user=request.user, name__istartswith=request.GET.get('query', ''), bookmark__isnull=False).distinct('name')

    return HttpResponse(json.dumps([x.name for x in tags]), content_type="application/json")


def add_bookmarks_from_import(request, tag, bookmarks):
    """
    Add bookmarks with the provided tag. Ignore duplicates.
    """

    added_count = 0
    dupe_count = 0

    for link in bookmarks:
        try:
            Bookmark.objects.get(url=link["url"])
            dupe_count = dupe_count + 1
        except ObjectDoesNotExist:
            b = Bookmark(
                user=request.user,
                url=link["url"],
                title=link["title"],
                created=link["created"],
                modified=link["created"]
            )
            b.save()

            # Add the specified tag to the bookmark.
            # Create the tag if it doesn't exist.
            try:
                t = Tag.objects.get(name=tag)
            except ObjectDoesNotExist:
                t = Tag(name=tag)
                t.save()
            b.tags.set([t])

            # We need to save the model again after adding the tags,
            #  since the b.tags.set() line above *doesn't* call the
            #  Bookmark model's post_save signal.
            b.save()

            snarf_favicon.delay(link["url"])
            added_count = added_count + 1

    messages.add_message(request, messages.INFO, "Bookmarks added: {}. Duplicates ignored: {}.".format(added_count, dupe_count))


def bookmark_import(request):
    """
    Import bookmarks from a file.
    Supported formats: Google bookmark export format
    """

    if request.method == 'POST':

        start = request.POST.get('start_folder', '')
        tag = request.POST.get('tag', '')

        links = []

        try:

            if not tag:
                messages.add_message(request, messages.ERROR, "Please specify a tag")
                raise ValueError()
            if not start:
                messages.add_message(request, messages.ERROR, "Please specify a starting folder")
                raise ValueError()

            xml_string = ''
            for chunk in request.FILES['file'].chunks():
                xml_string = xml_string + str(chunk)

            tree = lh.fromstring(xml_string)

            found = tree.xpath('//dt/h3[text()="{}"]/following::dl[1]//a'.format(start))

            if not found:
                messages.add_message(request, messages.ERROR, "No bookmarks were found")
                raise ValueError()

            for link in found:
                links.append(
                    {
                        "url": link.get("href"),
                        "created": datetime.datetime.fromtimestamp(int(link.get("add_date"))),
                        "title": link.text
                    }
                )

            add_bookmarks_from_import(request, tag, links)

        except ValueError:
            pass

    return render(request, 'bookmark/import.html',
                  {'section': SECTION
                  })


@login_required
def bookmark_tag(request, tag_filter=""):

    bookmarks = None

    sorted_bookmarks = []

    if tag_filter:
        request.session['bookmark_tag_filter'] = tag_filter

        bookmarks = Bookmark.objects.filter(user=request.user, tags__name__exact=tag_filter).order_by('-created')
        for bookmark in bookmarks:
            bookmark.tag_list = [x.name for x in bookmark.tags.all() if x.name != tag_filter]

        try:
            sort_order = BookmarkTagUser.objects.get(user=request.user, tag=Tag.objects.get(name=tag_filter))
            sorted_bookmarks = sorted(bookmarks, key=lambda v: sort_order.bookmark_list.index(v.id))
        except ObjectDoesNotExist as e:
            print("Error! %s" % e)
            # TODO: Use celery to fire off an email about the error
            sorted_bookmarks = bookmarks
        except ValueError as e:
            print("Error! %s" % e)
            # TODO: Use celery to fire off an email about the error
            sorted_bookmarks = bookmarks

    tag_counts = {}
    for tag in BookmarkTagUser.objects.filter(user=request.user, tag__in=request.user.userprofile.favorite_tags.all()):
        tag_counts[tag.tag.name] = len(tag.bookmark_list)

    favorite_tags = request.user.userprofile.favorite_tags.all().order_by('sortorder__sort_order')

    return render(request, 'bookmark/tag.html',
                  {'section': SECTION,
                   'bookmarks': sorted_bookmarks,
                   'tag_filter': tag_filter,
                   'tag_counts': tag_counts,
                   'favorite_tags': favorite_tags})


def sort_favorite_tags(request):
    """
    Move a given tag to a new position in a sorted list
    """

    tag_id = request.POST['tag_id']
    new_position = int(request.POST['new_position'])

    SortOrder.reorder(request.user, tag_id, new_position)

    return HttpResponse(json.dumps('OK'), content_type="application/json")


@login_required
def tag_bookmark_list(request):

    tag = request.POST['tag']
    link_id = int(request.POST['link_id'])
    position = int(request.POST['position'])

    sorted_list = BookmarkTagUser.objects.get(user=request.user, tag=Tag.objects.get(name=tag))

    # Verify that the bookmark is in the existing sort list
    if link_id not in sorted_list.bookmark_list:
        print("NOT Found!")
        # TODO Return an exception

    sorted_list.bookmark_list.remove(link_id)
    sorted_list.bookmark_list.insert(position - 1, link_id)

    sorted_list.save()

    return HttpResponse(json.dumps('OK'), content_type="application/json")


class OrderListJson(BaseDatatableView):
    # define column names that will be used in sorting
    # order is important and should be same as order of columns
    # displayed by datatables. For non sortable columns use empty
    # value like ''
    order_columns = ['created', 'url', 'title']

    def get_initial_queryset(self):
        # return queryset used as base for futher sorting/filtering
        # these are simply objects displayed in datatable

        # If the user has 'show untagged bookmarks only' set in preferences,
        # then don't show bookmarks which have been tagged.  However, for
        # searches (filters), ignore that preference
        if self.request.user.userprofile.bookmarks_show_untagged_only and self.request.GET['search[value]'] == '':
            return Bookmark.objects.filter(user=self.request.user, tags__isnull=True)
        else:
            return Bookmark.objects.filter(user=self.request.user)

    def filter_queryset(self, qs):
        # use request parameters to filter queryset

        filter = self.request.GET.get('search[value]', None)
        if filter:
            qs = qs.filter(title__icontains=filter)

        return qs

    def ordering(self, qs):
        randomize = self.request.GET.get('randomize', False)
        if randomize == 'yes':
            return qs.order_by('?')
        else:
            return super(OrderListJson, self).ordering(qs)

    def prepare_results(self, qs):
        # prepare list with output column data
        # queryset is already paginated here

        json_data = []
        for item in qs:
            if not item.title:
                item.title = 'No Title'
            try:
                response_status = requests.status_codes._codes[item.last_response_code][0]
            except KeyError:
                response_status = ''
            json_data.append([
                item.created.strftime("%b %d, %Y"),
                item.url,
                item.title,
                item.id,
                response_status
            ])
        return json_data
