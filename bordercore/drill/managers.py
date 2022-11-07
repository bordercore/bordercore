from django.apps import apps
from django.db import models
from django.db.models import F, Max, Min, Q
from django.utils import timezone

from tag.models import Tag


class DrillManager(models.Manager):

    def tags_last_reviewed(self, user):
        """
        Return tags which haven't been reviewed in a while
        """
        return Tag.objects.only("id", "name") \
                          .filter(user=user, question__isnull=False) \
                          .annotate(last_reviewed=Min("question__last_reviewed")) \
                          .order_by(F("last_reviewed").asc(nulls_first=True))

    def total_tag_progress(self, user):
        """
        Get percentage of all tags not needing review
        """

        Question = apps.get_model("drill", "Question")

        count = Question.objects.filter(user=user).count()

        todo = Question.objects.filter(
            Q(user=user),
            Q(interval__lte=timezone.now() - F("last_reviewed"))
            | Q(last_reviewed__isnull=True)
        ).count()

        percentage = 100 - (todo / count * 100) if count > 0 else 0

        return {
            "percentage": percentage,
            "count": todo
        }

    def favorite_questions_progress(self, user):
        """
        Get percentage of favorite questions not needing review
        """

        Question = apps.get_model("drill", "Question")

        count = Question.objects.filter(user=user, is_favorite=True).count()

        todo = Question.objects.filter(
            Q(user=user),
            Q(is_favorite=True),
            Q(interval__lte=timezone.now() - F("last_reviewed"))
            | Q(last_reviewed__isnull=True)
        ).count()

        percentage = 100 - (todo / count * 100) if count > 0 else 0

        return {
            "percentage": percentage,
            "count": count
        }

    def get_random_tag(self, user):
        """
        Get a random tag and its related information.

        We don't want a simple "order by random" on the entire tag set,
        since that will bias selections for popular tags. So we use
        a subquery to get the distinct tags first, then choose
        a random tag from that set.
        """

        Question = apps.get_model("drill", "Question")

        distinct_tags = Tag.objects.filter(question__isnull=False, user=user).distinct("name")
        random_tag = Tag.objects.filter(id__in=distinct_tags).order_by("?").first()
        return Question.get_tag_progress(user, random_tag.name) if random_tag else None

    def get_pinned_tags(self, user):
        """
        Get the user's pinned tags
        """

        Question = apps.get_model("drill", "Question")

        tags = user.userprofile.pinned_drill_tags.all().only("name").order_by("drilltag__sort_order")

        info = []

        for tag in tags:
            info.append(Question.get_tag_progress(user, tag.name))

        return info

    def recent_tags(self, user):
        """
        Get the tags most recently attached to questions
        """

        Question = apps.get_model("drill", "Question")

        return Question.objects.values(
            name=F("tags__name")
        ).annotate(
            max=Max("created")
        ).order_by(
            "-max"
        )
