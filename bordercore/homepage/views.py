import datetime
import json
from PyOrgMode import OrgDataStructure

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

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

    return render(request, 'homepage/index.html',
                  {'section': SECTION,
                   'quote': quote,
                   'tasks': tasks,
                   'music': music,
                   'pinned_bookmarks': pinned_bookmarks})


@login_required
def get_calendar_events(request):

    calendar = Calendar(request.user.userprofile)
    events = calendar.get_calendar_info()

    return render(request, 'homepage/get_calendar_events.json',
                  {'section': SECTION,
                   'info': json.dumps(events)})
