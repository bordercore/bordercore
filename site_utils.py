import re

from django.http import HttpResponseNotFound, HttpResponse
from django.conf import settings

# from bookmark.tasks import snarf_favicon


def handler404(request):

    url = request.get_full_path().replace('.ico', '')

    p = re.compile(".*/img/favicons/(.*)")
    m = p.match(url)
    if m:
        # url = m.group(1)
        # if url != 'default':
        #     snarf_favicon.delay(url, False)

        # Serve back a default favicon
        with open("%s/templates/static/img/favicons/default.png" % (settings.PROJECT_ROOT,), "rb") as f:
            return HttpResponse(f.read(), content_type="image/x-icon")

    return HttpResponseNotFound('<h1>Page not found</h1>')
