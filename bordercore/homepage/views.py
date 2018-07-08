import datetime
import json
import random
import re

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponseNotFound, HttpResponse, JsonResponse
from django.shortcuts import render

from blob.models import Document
from bookmark.models import Bookmark
from cal.models import Calendar
from fitness.models import ExerciseUser
from music.models import Listen
from PyOrgMode import PyOrgMode
from quote.models import Quote
from solrpy.core import SolrConnection

SECTION = 'Home'


@login_required
def homepage(request):

    quote = Quote.objects.order_by('?')[0]

    # Get any 'pinned' bookmarks
    pinned_bookmarks = Bookmark.objects.filter(is_pinned=True)

    tasks = []
    try:
        tree = PyOrgMode.OrgDataStructure()
        tree.load_from_file(request.user.userprofile.orgmode_file)

        startnode = get_nodes_by_tag(tree.root, "todo", [])
        nodes = PyOrgMode.OrgDataStructure.get_nodes_by_priority(startnode[0], "A", [])

        for node in nodes:
            tasks.append({'task': PyOrgMode.OrgDataStructure.parse_heading(node.heading)['heading'],
                          'tag': node.tags,
                          'date': get_date(node),
                          'parent_category': PyOrgMode.OrgDataStructure.parse_heading(node.parent.heading)['heading']})
    except AttributeError as e:
        print("AttributeError: %s" % e)

    # Get some recently played music
    music = Listen.objects.all().select_related().distinct().order_by('-created')[:3]

    # Choose a random image
    random_image = get_random_blob('image/*')
    random_image_info = {'uuid': random_image.uuid,
                         'cover_info': Document.get_cover_info(random_image.sha1sum, 'large', 500)}

    # Get the most recent untagged bookmarks
    bookmarks = Bookmark.objects.filter(tags__isnull=True).order_by('-created')[:10]

    # Get the list of 'daily' bookmarks
    daily_bookmarks = Bookmark.objects.filter(daily__isnull=False)
    for bookmark in daily_bookmarks:
        if bookmark.daily['viewed'] != 'true':
            bookmark.css_class = "bold"

    # Get the default collection
    default_collection = request.user.userprofile.homepage_default_collection.id

    # Get overdue exercises
    overdue_exercises = []
    active_exercises = ExerciseUser.objects.filter(user=1)
    for exercise in active_exercises:
        lag = int((int(datetime.datetime.now().strftime("%s")) - int(exercise.exercise.data_set.order_by('-date')[0].date.strftime("%s"))) / 86400) + 1
        if (lag >= exercise.frequency):
            overdue_exercises.append({'exercise': exercise,
                                      'lag': lag})

    return render(request, 'homepage/index.html',
                  {'section': SECTION,
                   'quote': quote,
                   'tasks': tasks,
                   'music': music,
                   'daily_bookmarks': daily_bookmarks,
                   'pinned_bookmarks': pinned_bookmarks,
                   'random_image_info': random_image_info,
                   'bookmarks': bookmarks,
                   'default_collection': default_collection,
                   'overdue_exercises': sorted(overdue_exercises, key=lambda x: x['lag'], reverse=True)})


@login_required
def get_calendar_events(request):

    calendar = Calendar(request.user.userprofile)
    events = calendar.get_calendar_info()

    return JsonResponse(events, safe=False)


def get_random_blob(content_type):
    seed = random.randint(1, 10000)
    conn = SolrConnection('http://%s:%d/%s' % (settings.SOLR_HOST, settings.SOLR_PORT, settings.SOLR_COLLECTION))
    solr_args = {'q': 'content_type:%s' % (content_type),
                 'sort': 'random_%s+desc' % (seed),
                 'wt': 'json',
                 'fl': 'internal_id,sha1sum,uuid',
                 'fq': '-is_private:true',
                 'rows': 1}
    solr_results = json.loads(conn.raw_query(**solr_args).decode('UTF-8'))['response']['docs'][0]
    try:
        blob = Document.objects.get(pk=solr_results['internal_id'])
    except ObjectDoesNotExist:
        pass
    return blob


# This possibly should be moved to a static method in PyOrgMode
def get_nodes_by_tag(node, tag, found_nodes=[]):

        if isinstance(node, PyOrgMode.OrgElement):
            try:
                if tag in node.tags:
                    found_nodes.append(node)
            except AttributeError:
                pass
            for node in node.content:
                get_nodes_by_tag(node, tag, found_nodes)
            return found_nodes
        else:
            return found_nodes


def get_date(node):

    if len(node.content) > 0 and isinstance(node.content[0], PyOrgMode.OrgDrawer.Element):
        property = node.content[0].content[0]
        if property.name == 'CREATED':
            raw_date = property.value
            matches = re.match(r'\[(\d\d\d\d-\d\d-\d\d).*\]', raw_date)
            if matches:
                return matches.group(1)
            else:
                return property.value


def handler404(request, exception, template=None):

    url = request.get_full_path().replace('.ico', '')

    p = re.compile(".*/img/favicons/(.*)")
    m = p.match(url)
    if m:
        # url = m.group(1)
        # if url != 'default':
        #     snarf_favicon.delay(url, False)

        # Serve back a default favicon
        with open("%s/static/img/favicons/default.png" % (settings.PROJECT_DIR,), "rb") as f:
            return HttpResponse(f.read(), content_type="image/x-icon")

    return HttpResponseNotFound('<h1>Page not found</h1>')
