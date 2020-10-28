import base64
import datetime
import json
import re

import lxml.html as lh
import pytz

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
from django.utils.decorators import method_decorator
from django.views.generic import ListView

from accounts.models import SortOrder
from bookmark.forms import BookmarkForm
from bookmark.models import Bookmark
from lib.util import get_pagination_range
from tag.models import SortOrderTagBookmark, Tag

SECTION = 'bookmarks'
BOOKMARKS_PER_PAGE = 50


@login_required
def click(request, bookmark_id=None):

    b = Bookmark.objects.get(user=request.user, pk=bookmark_id) if bookmark_id else None
    b.daily['viewed'] = 'true'
    b.save()
    return redirect(b.url)


@login_required
def edit(request, bookmark_id=None):

    action = 'Edit'
    b = Bookmark.objects.get(user=request.user, pk=bookmark_id) if bookmark_id else None

    tags = []

    if request.method == 'POST':
        if request.POST['Go'] in ['Edit', 'Add']:
            form = BookmarkForm(request.POST, instance=b, request=request)
            if form.is_valid():
                newform = form.save(commit=False)
                newform.user = request.user
                newform.save()
                form.save_m2m()
                form.instance.index_bookmark()
                form.instance.snarf_favicon()
                messages.add_message(request, messages.INFO, f'Bookmark {request.POST["Go"].lower()}ed')
                return overview(request)
        elif request.POST['Go'] == 'Delete':
            b.delete()
            messages.add_message(request, messages.INFO, 'Bookmark deleted')
            return overview(request)

    elif bookmark_id:
        action = 'Edit'
        form = BookmarkForm(instance=b, request=request)
        tags = [{"text": x.name, "value": x.name, "is_meta": x.is_meta} for x in b.tags.all()]

    else:
        action = 'Add'
        form = BookmarkForm(request=request)

    return render(request, 'bookmark/edit.html',
                  {'section': SECTION,
                   'action': action,
                   'form': form,
                   'tags': tags,
                   'bookmark': b})


@login_required
def delete(request, bookmark_id=None):

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
        messages.add_message(
            request,
            messages.WARNING,
            f"Bookmark already exists and was added on {b.created.strftime('%B %d, %Y')}",
            extra_tags="show_in_dom"
        )
        return redirect('bookmark_edit', b.id)
    except ObjectDoesNotExist:
        b = Bookmark(is_pinned=False, user=request.user, url=url, title=title)
        b.save()
        b.index_bookmark()
        b.snarf_favicon()

    return redirect('bookmark_edit', b.id)


@login_required
def get_tags_used_by_bookmarks(request):

    tags = Tag.objects.filter(bookmark__user=request.user, name__icontains=request.GET.get("query", ""), bookmark__isnull=False).distinct("name")

    return JsonResponse([{"value": x.name, "is_meta": x.is_meta} for x in tags], safe=False)


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

            b.index_bookmark()
            b.snarf_favicon()
            added_count = added_count + 1

    messages.add_message(request, messages.INFO, "Bookmarks added: {}. Duplicates ignored: {}.".format(added_count, dupe_count))


@login_required
def do_import(request):
    """
    Import bookmarks from a file.
    Supported formats: Google bookmark export format
    """

    if request.method == 'POST':

        start = request.POST.get('start_folder', '')
        tag = request.POST.get('tags', '')

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

    return render(request, 'bookmark/import.html', {'section': SECTION})


@login_required
def get_random_bookmarks(request):
    return overview(request, random=True)


@login_required
def overview(request,
             random=False):

    sorted_bookmarks = []
    tag_counts = {}

    tag_counts["Untagged"] = Bookmark.objects.filter(user=request.user, tags__isnull=True).count()

    favorite_tags = request.user.userprofile.favorite_tags.all().order_by('sortorder__sort_order')

    t = Tag.objects\
           .filter(id__in=[x.id for x in favorite_tags])\
           .values('id', 'name')\
           .annotate(bookmark_count=Count('bookmarks__sortordertagbookmark__bookmark'))

    for x in t:
        tag_counts[x["name"]] = x["bookmark_count"]

    return render(request, 'bookmark/index.html',
                  {
                      'section': SECTION,
                      'bookmarks': sorted_bookmarks,
                      'tag_counts': tag_counts,
                      'favorite_tags': favorite_tags,
                      'col_left': "bogus",
                      'col_content': "col-lg-12"
                  })


@method_decorator(login_required, name="dispatch")
class BookmarkListView(ListView):
    paginate_by = 2
    model = Bookmark

    def get_queryset(self):

        query = Bookmark.objects.filter(user=self.request.user)
        if "search" in self.kwargs:
            query = query.filter(title__icontains=self.kwargs.get("search"))
        elif "tag_filter" in self.kwargs:
            query = query.filter(title__icontains=self.kwargs.get("tag_filter"))
        else:
            query = query.filter(tags__isnull=True)

        query = query.prefetch_related("tags")
        query = query.only("id", "created", "url", "title", "last_response_code", "note")

        if "random" in self.kwargs:
            query = query.order_by("?")
        else:
            query = query.order_by("-created")

        page_number = self.kwargs.get("page_number", 1)
        paginator = Paginator(query, BOOKMARKS_PER_PAGE)
        page_obj = paginator.get_page(page_number)

        return page_obj

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        pagination = {}

        if queryset.paginator.num_pages > 1:

            page_number = self.kwargs.get("page_number", 1)

            pagination = {
                "num_pages": queryset.paginator.num_pages,
                "page_number": page_number,
                "paginate_by": self.paginate_by
            }

            pagination["range"] = get_pagination_range(
                page_number,
                queryset.paginator.num_pages,
                self.paginate_by
            )

            if queryset.has_next():
                pagination["next_page_number"] = queryset.next_page_number()
            if queryset.has_previous():
                pagination["previous_page_number"] = queryset.previous_page_number()

        bookmarks = []

        for x in queryset:
            bookmarks.append(
                {
                    "id": x.id,
                    "created": x.created.strftime("%B %d, %Y"),
                    "createdYear": x.created.strftime("%Y"),
                    "url": x.url,
                    "title": re.sub("[\n\r]", "", x.title),
                    "last_response_code": x.last_response_code,
                    "note": x.note,
                    "favicon_url": x.get_favicon_url(size=16),
                    "tags": [x.name for x in x.tags.all()]
                }
            )

        return JsonResponse(
            {
                "bookmarks": bookmarks,
                "pagination": pagination
            },
            safe=False
        )


@method_decorator(login_required, name="dispatch")
class BookmarkListTagView(BookmarkListView):

    def get(self, request, *args, **kwargs):
        queryset = self.get_queryset()

        pagination = {
            "num_pages": 1
        }

        bookmarks = []

        for x in queryset:
            bookmarks.append(
                {
                    "id": x.id,
                    "created": x.created.strftime("%B %d, %Y"),
                    "createdYear": x.created.strftime("%Y"),
                    "url": x.url,
                    "title": re.sub("[\n\r]", "", x.title),
                    "last_response_code": x.last_response_code,
                    "note": x.note,
                    "favicon_url": x.get_favicon_url(size=16),
                    "tags": [x.name for x in x.tags.all()]
                }
            )

        return JsonResponse(
            {
                "bookmarks": bookmarks,
                "pagination": pagination
            },
            safe=False
        )

    def get_queryset(self):

        bookmarks = Bookmark.get_tagged_bookmarks(self.request.user, self.kwargs.get("tag_filter"))
        return bookmarks


@login_required
def sort_favorite_tags(request):
    """
    Move a given tag to a new position in a sorted list
    """

    tag_id = request.POST['tag_id']
    new_position = int(request.POST['new_position'])

    if new_position < 1:
        response = {
            "status": "Error",
            "message": f"Position cannot be < 1: {new_position}"
        }
    else:
        SortOrder.reorder(request.user, tag_id, new_position)
        response = {
            "status": "OK"
        }

    return JsonResponse(response, safe=False)


@login_required
def sort_bookmarks(request):
    """
    Given an ordered list of bookmarks with a specified tag, move a
    bookmark to a new position within that list
    """

    tag_name = request.POST["tag"]
    link_id = int(request.POST["link_id"])
    new_position = int(request.POST["position"])

    s = SortOrderTagBookmark.objects.get(tag__name=tag_name, bookmark__id=link_id)
    SortOrderTagBookmark.reorder(s, new_position)

    return JsonResponse({"status": "OK"}, safe=False)


@login_required
def add_note(request):

    tag_name = request.POST["tag"]
    link_id = int(request.POST["link_id"])

    note = request.POST["note"]

    SortOrderTagBookmark.objects.filter(
        tag__name=tag_name,
        bookmark__id=link_id
    ).update(note=note)

    return JsonResponse({"status": "OK"}, safe=False)


@login_required
def get_new_bookmarks_count(request, timestamp):
    """
    Get a count of all bookmarks created after the specified timestamp
    """

    time = datetime.datetime.fromtimestamp(timestamp / 1000, pytz.timezone("US/Eastern"))
    count = Bookmark.objects.filter(user=request.user, created__gte=time).count()

    return JsonResponse(
        {
            "status": "OK",
            "count": count
        }
    )
