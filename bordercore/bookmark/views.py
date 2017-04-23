import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.shortcuts import redirect, render

from django_datatables_view.base_datatable_view import BaseDatatableView

from bookmark.models import Bookmark, BookmarkTagUser
from bookmark.forms import BookmarkForm
from bookmark.tasks import snarf_favicon
from tag.models import Tag

SECTION = 'Bookmarks'


@login_required
def bookmark_list(request):

    message = ''
    bookmarks = []

    untagged_count = Bookmark.objects.filter(tags__isnull=True).count()

    return render(request, 'bookmark/index.html',
                  {'section': SECTION,
                   'bookmarks': bookmarks,
                   'cols': ['Date', 'url', 'title', 'id'],
                   'message': message,
                   'untagged_count': untagged_count})


@login_required
def bookmark_click(request, bookmark_id=None):

    b = Bookmark.objects.get(pk=bookmark_id) if bookmark_id else None
    b.daily['viewed'] = 'true'
    b.save()
    return redirect(b.url)


@login_required
def bookmark_edit(request, bookmark_id=None):

    action = 'Edit'

    b = Bookmark.objects.get(pk=bookmark_id) if bookmark_id else None

    if request.method == 'POST':
        if request.POST['Go'] in ['Edit', 'Add']:
            form = BookmarkForm(request.POST, instance=b)  # A form bound to the POST data
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
        form = BookmarkForm(instance=b)

    else:
        action = 'Add'
        form = BookmarkForm()  # An unbound form

    return render(request, 'bookmark/edit.html',
                  {'section': SECTION,
                   'action': action,
                   'form': form})


@login_required
def bookmark_delete(request, bookmark_id=None):

    # First delete the bookmark from any tag lists
    info = BookmarkTagUser.objects.raw("SELECT * FROM bookmark_bookmarktaguser WHERE %s = ANY (bookmark_list)" % bookmark_id)
    for tag in info:
        tag.bookmark_list.remove(int(bookmark_id))
        tag.save()

    # Then delete the actual bookmark
    bookmark = Bookmark.objects.get(pk=bookmark_id)
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
        b = Bookmark.objects.get(url=url)
        messages.add_message(request, messages.WARNING, 'Bookmark already exists and was added on %s' % b.created.strftime("%B %d, %Y"))
        return redirect('bookmark_edit', b.id)
    except ObjectDoesNotExist:
        b = Bookmark(is_pinned=False, user=request.user, url=url, title=title)
        b.save()
        snarf_favicon.delay(url)

    return redirect('bookmark_edit', b.id)


@login_required
def tag_search(request):

    tags = Tag.objects.filter(name__istartswith=request.GET.get('query', ''), bookmark__isnull=False).distinct('name')

    return HttpResponse(json.dumps([x.name for x in tags]), content_type="application/json")


@login_required
def bookmark_tag(request):

    bookmarks = None

    tag_filter = request.GET.get('tagsearch', None)
    if not tag_filter:
        tag_filter = request.session.get('bookmark_tag_filter', None)

    sorted_bookmarks = []

    if tag_filter:
        bookmarks = Bookmark.objects.filter(tags__name__exact=tag_filter).order_by('-created')
        request.session['bookmark_tag_filter'] = tag_filter

        try:
            sort_order = BookmarkTagUser.objects.get(tag=Tag.objects.get(name=tag_filter), user=request.user)
            sorted_bookmarks = sorted(bookmarks, key=lambda v: sort_order.bookmark_list.index(v.id))
        except ObjectDoesNotExist as e:
            print("Error! %s" % e)
            # TODO: Use celery to fire off an email about the error
            sorted_bookmarks = bookmarks
        except ValueError as e:
            print("Error! %s" % e)
            # TODO: Use celery to fire off an email about the error
            sorted_bookmarks = bookmarks

    favorite_tags = request.user.userprofile.favorite_tags.all()

    return render(request, 'bookmark/tag.html',
                  {'section': SECTION,
                   'bookmarks': sorted_bookmarks,
                   'tag_filter': tag_filter,
                   'favorite_tags': favorite_tags})


@login_required
def tag_bookmark_list(request):

    tag = request.POST['tag']
    link_id = int(request.POST['link_id'])
    position = int(request.POST['position'])

    sorted_list = BookmarkTagUser.objects.get(tag=Tag.objects.get(name=tag), user=request.user)

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
        if self.request.user.userprofile.bookmarks_show_untagged_only and self.request.GET.get('sSearch') == '':
            return Bookmark.objects.filter(tags__isnull=True)
        else:
            return Bookmark.objects.all()

    def filter_queryset(self, qs):
        # use request parameters to filter queryset

        sSearch = self.request.GET.get('sSearch', None)
        if sSearch:
            qs = qs.filter(title__icontains=sSearch)

        return qs

    def prepare_results(self, qs):
        # prepare list with output column data
        # queryset is already paginated here

        json_data = []
        for item in qs:
            if not item.title:
                item.title = 'No Title'
            json_data.append([
                item.created.strftime("%b %d, %Y"),
                item.url,
                item.title,
                item.id
            ])
        return json_data
