from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from .models import Quote


@login_required
def get_random_quote(request):

    quote = Quote.objects.all().order_by("?")[0]

    response = {
        "status": "OK",
        "quote": {
            "uuid": quote.uuid,
            "quote": quote.quote,
            "source": quote.source
        },
    }

    return JsonResponse(response)
