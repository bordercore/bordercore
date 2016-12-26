import datetime
import json
from PyOrgMode import OrgDataStructure
import random
import solr

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render

from blob.models import Blob
from bookmark.models import Bookmark
from quote.models import Quote
from music.models import Listen
from cal.models import Calendar

SECTION = 'Home'


@login_required
def homepage(request):

    quote = Quote.objects.order_by('?')[0]

    # Get any 'pinned' bookmarks
    pinned_bookmarks = Bookmark.objects.filter(is_pinned=True)

    # Get the latest 'urgent' todo tasks
    # tasks = Todo.objects.filter(is_urgent=True).order_by('-modified')[:3]

    # During work hours, show work todos.  Otherwise show personal todos
    t = datetime.datetime.now()
    if t.hour > 9 and t.hour < 18 and t.isoweekday() not in [6, 7]:
        start_node_category = 'Black Duck'
    else:
        start_node_category = 'Bordercore'

    tasks = []
    try:
        tree = OrgDataStructure()
        tree.load_from_file(request.user.userprofile.orgmode_file)

        startnode = OrgDataStructure.get_node_by_heading(tree.root, start_node_category, [])[0]
        nodes = OrgDataStructure.get_nodes_by_priority(startnode, "A", [])

        for node in nodes:
            tasks.append({'task': OrgDataStructure.parse_heading(node.heading)['heading'],
                          'tag': node.tags,
                          'parent_category': OrgDataStructure.parse_heading(node.parent.heading)['heading']})
    except AttributeError, e:
        print "AttributeError: %s" % e

    # Get some recently played music
    music = Listen.objects.all().select_related().distinct().order_by('-created')[:3]

    # Choose a random image
    random_image = get_random_blob('image/*')
    random_image_info = {'sha1sum': random_image.sha1sum,
                         'cover_info': Blob.get_cover_info(random_image.sha1sum, 'small', 500)}

    # Get the most recent untagged bookmarks
    bookmarks = Bookmark.objects.filter(tags__isnull=True)[:10]

    # Get the list of 'daily' bookmarks
    daily_bookmarks = Bookmark.objects.filter(tags__name__in=['daily'])
    for bookmark in daily_bookmarks:
        if int(datetime.datetime.now().strftime("%s")) - int(bookmark.last_check.strftime("%s")) > 1:
            bookmark.css_class = "bookmark-daily"
            print("%s needs to be checked" % bookmark.title)

    return render(request, 'homepage/index.html',
                  {'section': SECTION,
                   'quote': quote,
                   'tasks': tasks,
                   'music': music,
                   'daily_bookmarks': daily_bookmarks,
                   'pinned_bookmarks': pinned_bookmarks,
                   'random_image_info': random_image_info,
                   'bookmarks': bookmarks})


@login_required
def get_calendar_events(request):

    calendar = Calendar(request.user.userprofile)
    events = calendar.get_calendar_info()

    return JsonResponse(events, safe=False)


def get_random_blob(content_type):
    seed = random.randint(1, 10000)
    conn = solr.SolrConnection('http://%s:%d/%s' % (settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
    solr_args = {'q': 'content_type:%s' % (content_type),
                 'sort': 'random_%s+desc' % (seed),
                 'wt': 'json',
                 'fl': 'internal_id,sha1sum',
                 'fq': '-is_private:true',
                 'rows': 1}
    solr_results = json.loads(conn.raw_query(**solr_args))['response']['docs'][0]
    blob = Blob.objects.get(pk=solr_results['internal_id'])
    return blob
