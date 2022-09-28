from rest_framework.decorators import api_view

from django.http import JsonResponse

from bookmark.models import Bookmark
from drill.models import Question


@api_view(["GET"])
def site_stats(request):

    return JsonResponse(
        {
            "untagged_bookmarks": Bookmark.objects.bare_bookmarks(
                user=request.user,
                count_only=True
            ),
            "bookmarks_total": Bookmark.objects.filter(
                user=request.user
            ).count(),
            "drill_needing_review": Question.objects.total_tag_progress(request.user),
        }
    )
