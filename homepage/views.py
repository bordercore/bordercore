from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext

from quote.models import Quote
from todo.models import Todo
from music.models import Listen

SECTION = 'Home'

@login_required
def homepage(request):

    quote = Quote.objects.order_by('?')[0]

    # Get the latest 'urgent' todo tasks
    tasks = Todo.objects.filter(is_urgent=True).order_by('-modified')[:3]

    # Get some recently played music
    music = Listen.objects.all().select_related().distinct().order_by('-created')[:3]

    return render_to_response('homepage/index.html',
                              {'section': SECTION, 'quote': quote, 'tasks': tasks, 'music': music },
                              context_instance=RequestContext(request))
