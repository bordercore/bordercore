import re

from botocore.errorfactory import ClientError
from elasticsearch import Elasticsearch
from PyOrgMode import PyOrgMode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseNotFound, JsonResponse
from django.shortcuts import render

from blob.models import Blob
from bookmark.models import Bookmark
from cal.models import Calendar
from fitness.models import ExerciseUser
from music.models import Listen
from quote.models import Quote
from todo.models import Todo


@login_required
def homepage(request):

    quote = Quote.objects.order_by('?').first()

    # Get any 'pinned' bookmarks
    pinned_bookmarks = Bookmark.objects.filter(user=request.user, is_pinned=True)

    # if request.user.userprofile.orgmode_file:
    #     try:
    #         tree = PyOrgMode.OrgDataStructure()
    #         tree.load_from_file(request.user.userprofile.orgmode_file)
    #         startnode = PyOrgMode.OrgDataStructure.get_nodes_by_tag(tree.root, "todo", [])
    #         nodes = PyOrgMode.OrgDataStructure.get_nodes_by_priority(startnode[0], "A", [])
    #         for node in nodes:
    #             tasks.append({'task': PyOrgMode.OrgDataStructure.parse_heading(node.heading)['heading'],
    #                           'tag': node.tags,
    #                           'date': get_date(node),
    #                           'parent_category': PyOrgMode.OrgDataStructure.parse_heading(node.parent.heading)['heading']})
    #     except AttributeError as e:
    #         log.info("AttributeError: %s" % e)

    tasks = Todo.objects.filter(user=request.user, priority=Todo.get_priority_value("High")).prefetch_related("tags")

    # Get some recently played music
    music = Listen.objects.filter(user=request.user).select_related("song").distinct().order_by('-created')[:3]

    # Choose a random image
    random_image_info = None
    try:
        random_image = get_random_blob(request, 'image/*')
        if random_image:
            try:
                random_image_info = {'blob': random_image,
                                     'uuid': random_image.uuid,
                                     'cover_info': Blob.get_cover_info(request.user, random_image.sha1sum, 'large', 500)}
            except ClientError as e:
                messages.add_message(request, messages.ERROR, f"Error getting random image info for uuid={random_image.uuid}: {e}")
    except ConnectionRefusedError:
        messages.add_message(request, messages.ERROR, 'Cannot connect to Elasticsearch')

    # Get the most recent untagged bookmarks
    bookmarks = Bookmark.objects.filter(user=request.user, tags__isnull=True).order_by('-created')[:10]

    # Get the list of 'daily' bookmarks
    daily_bookmarks = Bookmark.objects.filter(user=request.user, daily__isnull=False)
    for bookmark in daily_bookmarks:
        if bookmark.daily['viewed'] != 'true':
            bookmark.css_class = "bold"

    # Get the default collection
    default_collection = None
    try:
        default_collection = request.user.userprofile.homepage_default_collection.id
    except AttributeError:
        pass

    overdue_exercises = ExerciseUser.get_overdue_exercises(request.user)

    return render(request, 'homepage/index.html',
                  {'quote': quote,
                   'tasks': tasks,
                   'music': music,
                   'daily_bookmarks': daily_bookmarks,
                   'pinned_bookmarks': pinned_bookmarks,
                   'random_image_info': random_image_info,
                   'bookmarks': bookmarks,
                   'default_collection': default_collection,
                   'overdue_exercises': sorted(overdue_exercises, key=lambda x: x['lag'], reverse=True),
                   'no_left_block': True,
                   'content_block_width': 12,
                   'title': 'Homepage'})


@login_required
def get_calendar_events(request):

    calendar = Calendar(request.user.userprofile)
    if calendar.has_credentials():
        events = calendar.get_calendar_info()
    else:
        events = []

    return JsonResponse(events, safe=False)


def get_random_blob(request, content_type):

    es = Elasticsearch(
        [settings.ELASTICSEARCH_ENDPOINT],
        verify_certs=False
    )

    search_object = {
        'query': {
            "function_score": {
                "random_score": {
                },
                "query": {
                    'bool': {
                        'must': [
                            {
                                "wildcard": {
                                    "content_type": {
                                        "value": content_type,
                                    }
                                }
                            },
                            {
                                'term': {
                                    'user_id': request.user.id
                                }
                            },
                            {
                                'term': {
                                    'is_private': False
                                }
                            }
                        ]
                    }
                }
            }
        },
        'from': 0,
        'size': 1,
        '_source': ['uuid']
    }

    results = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)

    if results["hits"]["hits"]:
        return Blob.objects.get(user=request.user, uuid=results["hits"]["hits"][0]["_source"]["uuid"])
    else:
        return None


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
