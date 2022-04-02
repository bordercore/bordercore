import pytest

from django.contrib.auth.models import User
from django.db.models import Max, Min

from search.models import RecentSearch

pytestmark = pytest.mark.data_quality


def test_recent_searches_sort_order_mixin():
    """
    This test checks for two things for the RecentSearch model for each user:

    min(sort_order) = 1
    max(sort_order) should equal the total count
    """

    assert RecentSearch.objects.values(
        "user"
    ).aggregate(
        Min("sort_order")
    )["sort_order__min"] == 1, "Min(sort_order) is not 1 for RecentSearches user"

    for user in User.objects.filter(recentsearch__isnull=False).distinct():
        count = RecentSearch.objects.filter(user=user).count()
        assert RecentSearch.objects.filter(
            user=user
        ).aggregate(
            Max("sort_order")
        )["sort_order__max"] == count, f"Max(sort_order) != total count for RecentSearches user={user}"
