import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse
from django.shortcuts import redirect, render_to_response
from django.template import RequestContext

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

    return render_to_response('bookmark/index.html',
                              {'section': SECTION,
                               'bookmarks': bookmarks,
                               'cols': ['Date', 'url', 'title', 'id'],
                               'message': message },
                              context_instance=RequestContext(request))


@login_required
def bookmark_edit(request, bookmark_id = None):

    action = 'Edit'

    b = Bookmark.objects.get(pk=bookmark_id) if bookmark_id else None

    if request.method == 'POST':
        if request.POST['Go'] in ['Edit', 'Add']:
            form = BookmarkForm(request.POST, instance=b) # A form bound to the POST data
            if form.is_valid():
                newform = form.save(commit=False)
                newform.user = request.user
                newform.save()
                form.save_m2m() # Save the many-to-many data for the form.
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
        form = BookmarkForm() # An unbound form

    return render_to_response('bookmark/edit.html',
                              {'section': SECTION, 'action': action, 'form': form },
                              context_instance=RequestContext(request))

@login_required
def snarf_link(request):

    import HTMLParser
    h = HTMLParser.HTMLParser()

    url = request.GET['url']
    title = h.unescape( request.GET['title'] )

    b = Bookmark(user=request.user, url=url, title=title)
    b.save()

    return redirect('bookmark_edit', b.id)


@login_required
def tag_search(request):

    tags = Tag.objects.filter(name__istartswith=request.GET.get('query', ''))
    tag_list = []

    # Filter out tags which haven't been applied to at least one bookmark
    for tag in tags:
        if tag.bookmark_set.all():
            tag_list.append(tag.name)

    return HttpResponse(json.dumps( tag_list ), content_type="application/json")


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
            sorted_bookmarks = sorted(bookmarks, key=lambda v : sort_order.bookmark_list.index(v.id))
        except ObjectDoesNotExist, e:
            print "Error! %s" % e
            # TODO: Use celery to fire off an email about the error
            sorted_bookmarks = bookmarks
        except ValueError, e:
            print "Error! %s" % e
            # TODO: Use celery to fire off an email about the error
            sorted_bookmarks = bookmarks

    favorite_tags = request.user.userprofile.favorite_tags.all()

    return render_to_response('bookmark/tag.html',
                              {'section': SECTION, 'bookmarks': sorted_bookmarks, 'tag_filter': tag_filter, 'favorite_tags': favorite_tags },
                              context_instance=RequestContext(request))


@login_required
def tag_bookmark_list(request):

    tag = request.POST['tag']
    link_id = int(request.POST['link_id'])
    position = int(request.POST['position'])
    print "tag: %s" % tag
    print "link_id: %d" % link_id
    print "position: %d" % position

    print Tag.objects.get(name=tag).name
    sorted_list = BookmarkTagUser.objects.get(tag=Tag.objects.get(name=tag), user=request.user)

    # Verify that the bookmark is in the existing sort list
    if not link_id in sorted_list.bookmark_list:
        print "NOT Found!"
        # TODO Return an exception

    sorted_list.bookmark_list.remove( link_id )
    sorted_list.bookmark_list.insert( position - 1, link_id )

    print "New order: %s" % sorted_list.bookmark_list
    sorted_list.save()

    return HttpResponse(json.dumps( 'OK' ), content_type="application/json")


#@login_required
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
        if self.request.user.userprofile.bookmarks_show_untagged_only and self.request.GET.get('sSearch') != None:
            return Bookmark.objects.filter(tags__isnull=True)
        else:
            return Bookmark.objects.all()

    def filter_queryset(self, qs):
        # use request parameters to filter queryset

#        qs = [ bookmark for bookmark in qs if not bookmark.tags.all() ]

        # simple example:
        sSearch = self.request.GET.get('sSearch', None)
        if sSearch:
            qs = qs.filter(title__icontains=sSearch)

        # more advanced example
        # filter_customer = self.request.GET.get('customer', None)

        # if filter_customer:
        #     customer_parts = filter_customer.split(' ')
        #     qs_params = None
        #     for part in customer_parts:
        #         q = Q(customer_firstname__istartswith=part)|Q(customer_lastname__istartswith=part)
        #         qs_params = qs_params | q if qs_params else q
        #         qs = qs.filter(qs_params)

        return qs

    def prepare_results(self, qs):
        # prepare list with output column data
        # queryset is already paginated here

        json_data = []
        for item in qs:
            json_data.append([
                item.created.strftime("%b %d, %Y"),
                item.url,
                item.title,
                item.id
                # "%s %s" % (item.customer_firstname, item.customer_lastname),
                # item.get_state_display(),
                # item.modified.strftime("%Y-%m-%d %H:%M:%S")
            ])
        return json_data
