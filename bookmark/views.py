from blog.models import User
from bookmark.models import Bookmark

from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext

from bookmark.models import Bookmark
from django_datatables_view.base_datatable_view import BaseDatatableView

section = 'Bookmarks'

@login_required
def bookmark_list(request):

    #    if not request.user.is_authenticated():
    #        return HttpResponseRedirect('/accounts/login/?next=%s' % request.path)
    message = ''
    results = ''
    #    request.session["fav_color"] = "blue"
    if not request.user.is_authenticated():
        message = 'User is NOT authenticated'
    else:
        message = 'Hello ' + request.user.username

    bookmarks = []

    # if 'tagsearch' in request.GET:
    #     bookmarks = Bookmark.objects.filter(tags__name__exact=request.GET['tagsearch'])
    # # elif 'search_item' in request.GET:
    # #     posts = Post.objects.filter(
    # #         Q(post__icontains=request.GET['search_item']) |
    # #         Q(title__icontains=request.GET['search_item'])
    # #     )
    # # elif blog_id:
    # #     posts = Post.objects.filter(id=blog_id)
    # else:
    #     # posts = Post.objects.filter(id=1120)
    #     bookmarks = Bookmark.objects.order_by('-created').all()[:25]

    # pprint(posts)

    # if 'Go' in request.POST:
    #     did_submit = True
    #     mysolr = BCSolr()
    #     results = mysolr.search(request.POST['value'], "title")

    return render_to_response('bookmark/index.html',
                              {'section': section,
                               'bookmarks': bookmarks,
                               'cols': ['Date', 'url', 'title', 'id'],
                               'message': message,
                               'results': results },
                              context_instance=RequestContext(request))


@login_required
def snarf_link(request):

    url = request.GET['url']
    title = request.GET['title']

    # TODO Add authentication here -- don't assume the user is jerrell
    u = User.objects.get(username__exact='jerrell')
    b = Bookmark(user=u, url=url, title=title)
    b.save()

    return render_to_response('bookmark/snarf_link.html',
                              {'section': section, 'url': url, 'title': title},
                              context_instance=RequestContext(request))

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
        return Bookmark.objects.all()

    def filter_queryset(self, qs):
        # use request parameters to filter queryset

        # simple example:
        sSearch = self.request.GET.get('sSearch', None)
        if sSearch:
            qs = qs.filter(title__istartswith=sSearch)

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
