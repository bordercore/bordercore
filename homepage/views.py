import datetime
import json
from PyOrgMode import OrgDataStructure

from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext

from quote.models import Quote
# from todo.models import Todo
from music.models import Listen
from cal.models import Calendar

SECTION = 'Home'

@login_required
def homepage(request):

    quote = Quote.objects.order_by('?')[0]

    # Get the latest 'urgent' todo tasks
    # tasks = Todo.objects.filter(is_urgent=True).order_by('-modified')[:3]

    # During work hours, show work todos.  Otherwise show personal todos
    t = datetime.datetime.now()
    if t.hour > 9 and t.hour < 18 and t.isoweekday() not in [6, 7]:
        start_node_category = 'Black Duck'
    else:
        start_node_category = 'Bordercore'

    tree = OrgDataStructure()
    tree.load_from_file(request.user.userprofile.orgmode_file)

    startnode = OrgDataStructure.get_node_by_heading(tree.root, start_node_category, [])[0]
    nodes = OrgDataStructure.get_nodes_by_priority(startnode, "A", [])

    tasks = []
    for node in nodes:
        tasks.append( {'task': OrgDataStructure.parse_heading(node.heading)['heading'],
                       'tag': node.tags,
                       'parent_category': OrgDataStructure.parse_heading(node.parent.heading)['heading']} )

    # Get some recently played music
    music = Listen.objects.all().select_related().distinct().order_by('-created')[:3]

    return render_to_response('homepage/index.html',
                              {'section': SECTION, 'quote': quote, 'tasks': tasks, 'music': music },
                              context_instance=RequestContext(request))


@login_required
def get_calendar_events(request):

    calendar = Calendar(request.user.userprofile)
    events = calendar.get_calendar_info()

    return render_to_response('homepage/get_calendar_events.json',
                              {'section': SECTION, 'info': json.dumps(events)},
                              context_instance=RequestContext(request),
                              content_type="application/json")
