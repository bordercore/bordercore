import re

from botocore.errorfactory import ClientError
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import ConnectionError
from PyOrgMode import PyOrgMode

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse
from django.shortcuts import render

from blob.models import Blob
from bookmark.models import Bookmark
from cal.models import Calendar
from collection.models import Collection
from drill.models import Question
from fitness.models import ExerciseUser
from music.models import Listen
from quote.models import Quote
from todo.models import Todo


@login_required
def homepage(request):

    quote = Quote.objects.order_by("?").first()

    # Get any 'pinned' bookmarks
    pinned_bookmarks = Bookmark.objects.filter(user=request.user, is_pinned=True)

    tasks = Todo.objects.filter(user=request.user, priority=Todo.get_priority_value("High")).prefetch_related("tags")[:5]

    # Get some recently played music
    music = Listen.objects.filter(user=request.user).select_related("song").distinct().order_by("-created")[:3]

    # Choose a random image
    random_image_info = None
    try:
        random_image = get_random_image(request, "image/*")
        if random_image:
            try:
                random_image_info = {
                    **random_image,
                    "url": Blob.get_cover_url_static(
                        random_image["uuid"],
                        random_image["filename"],
                        "large",
                    ),
                }
            except ClientError as e:
                messages.add_message(request, messages.ERROR, f"Error getting random image info for uuid={random_image['uuid']}: {e}")
    except (ConnectionRefusedError, ConnectionError):
        messages.add_message(request, messages.ERROR, "Cannot connect to Elasticsearch")
    except ObjectDoesNotExist:
        messages.add_message(request, messages.ERROR, "Blob found in Elasticsearch but not the DB")

    # Get the most recent untagged bookmarks
    bookmarks = Bookmark.objects.bare_bookmarks(request.user, 50)

    # Get the list of 'daily' bookmarks
    daily_bookmarks = Bookmark.objects.filter(user=request.user, daily__isnull=False)
    for bookmark in daily_bookmarks:
        if bookmark.daily["viewed"] != "true":
            bookmark.css_class = "font-weight-bold"

    # Get the default collection
    default_collection = get_default_collection_blobs(request)

    overdue_exercises = ExerciseUser.get_overdue_exercises(request.user)

    return render(request, "homepage/index.html",
                  {"quote": quote,
                   "tasks": tasks,
                   "music": music,
                   "daily_bookmarks": daily_bookmarks,
                   "pinned_bookmarks": pinned_bookmarks,
                   "random_image_info": random_image_info,
                   "bookmarks": bookmarks,
                   "default_collection": default_collection,
                   "overdue_exercises": sorted(overdue_exercises, key=lambda x: x["lag"], reverse=True),
                   "drill_total_progress": Question.objects.total_tag_progress(request.user),
                   "title": "Homepage"})


@login_required
def get_calendar_events(request):

    calendar = Calendar(request.user.userprofile)
    if calendar.has_credentials():
        events = calendar.get_calendar_info()
    else:
        events = []

    return JsonResponse(events, safe=False)


def get_random_image(request, content_type):

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
        '_source': [
            'filename',
            'name',
            'uuid'
        ]
    }

    results = es.search(index=settings.ELASTICSEARCH_INDEX, body=search_object)

    if results["hits"]["hits"]:
        return results["hits"]["hits"][0]["_source"]
    else:
        return None


def get_default_collection_blobs(request):

    try:
        collection = Collection.objects.get(pk=request.user.userprofile.homepage_default_collection.id)
        return {
            "uuid": collection.uuid,
            "name": collection.name,
            "blob_list": collection.get_blob_list(limit=3)
        }
    except AttributeError:
        pass


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


@login_required
def gallery(request):
    return render(request, "homepage/gallery.html", {})


def handler404(request, exception):

    response = render(request, "404.html", {})
    response.status_code = 404
    return response


def handler403(request, exception):

    response = render(request, "403.html", {})
    response.status_code = 403
    return response


def handler500(request):

    response = render(request, "500.html", {})
    response.status_code = 500
    return response
