from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import OuterRef, Subquery
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.generic.list import ListView

from .models import Metric, MetricData


@method_decorator(login_required, name="dispatch")
class MetricListView(UserPassesTestMixin, ListView):

    model = Metric
    template_name = "metrics/metric_list.html"
    context_object_name = "metrics"

    test_types = {
        "Bordercore Unit Tests": "unit",
        "Bordercore Functional Tests": "functional",
        "Bordercore Data Quality Tests": "data",
        "Bordercore Wumpus Tests": "wumpus",
        "Bordercore Test Coverage": "coverage"
    }

    def test_func(self):
        """
        Only admin users may view this page
        """
        return self.request.user.groups.filter(name="Admin").exists()

    def get_queryset(self):

        newest = MetricData.objects.filter(metric=OuterRef("pk")) \
                                   .order_by("-created")

        return Metric.objects.annotate(
            latest_result=Subquery(newest.values("value")[:1]),
            created=Subquery(newest.values("created")[:1])) \
            .filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["title"] = "Bordercore Metrics"

        for metric in self.object_list:

            if metric.created:

                if timezone.now() - metric.created > timedelta(days=1):
                    metric.overdue = True

                context[self.test_types[metric.name]] = metric

                if metric.name == "Bordercore Test Coverage":
                    metric.latest_result["line_rate"] = int(round(float(metric.latest_result["line_rate"]) * 100, 0))

        context["no_left_block"] = True
        context["content_block_width"] = "12"

        return context
