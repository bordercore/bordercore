import uuid
from datetime import timedelta

from elasticsearch import helpers

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models import F, Max, Q
from django.db.models.signals import pre_delete
from django.dispatch import receiver
from django.template.defaultfilters import pluralize
from django.urls import reverse
from django.utils import timezone

from blob.models import Blob
from bookmark.models import Bookmark
from lib.mixins import SortOrderMixin, TimeStampedModel
from lib.util import get_elasticsearch_connection
from tag.models import Tag

from .managers import DrillManager

INTERVALS_DEFAULT = [1, 2, 3, 5, 8, 13, 21, 30]


class Question(TimeStampedModel):
    """
    One question and its answer
    """

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    question = models.TextField()
    answer = models.TextField()
    tags = models.ManyToManyField(Tag, blank=True)
    last_reviewed = models.DateTimeField(null=True)
    times_failed = models.IntegerField(default=0, null=False)
    interval = models.DurationField(default=timedelta(days=1), blank=False, null=False)
    interval_index = models.IntegerField(default=0, null=False)
    is_favorite = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    bc_objects = models.ManyToManyField("drill.BCObject", through="drill.QuestionToObject", through_fields=("node", "bc_object"))

    objects = DrillManager()

    def get_tags(self):
        return ", ".join([tag.name for tag in self.tags.all()])

    def __str__(self):
        return self.question

    @property
    def needs_review(self):
        if not self.last_reviewed:
            return True
        return self.interval < timezone.now() - self.last_reviewed

    def _good_response(self):
        """
        Get the interval changes based on a question response of "good"
        """

        if self.interval_index + 1 < len(self.user.userprofile.drill_intervals):
            new_interval = timedelta(days=self.user.userprofile.drill_intervals[self.interval_index + 1])
            return {
                "description": f"Increase interval to <strong>{new_interval.days} day{pluralize(new_interval.days)}</strong>",
                "interval": new_interval,
                "interval_index": self.interval_index + 1
            }
        else:
            return {
                "description": f"Interval stays at <strong>{self.interval.days} day{pluralize(self.interval.days)}</strong>",
                "interval": self.interval,
                "interval_index": self.interval_index
            }

    def _easy_response(self):
        """
        Get the interval changes based on a question response of "easy"
        """

        if self.interval_index + 2 < len(self.user.userprofile.drill_intervals):
            new_interval = timedelta(days=self.user.userprofile.drill_intervals[self.interval_index + 2])
            return {
                "description": f"Increase interval to <strong>{new_interval.days} day{pluralize(new_interval.days)}</strong>",
                "interval": new_interval,
                "interval_index": self.interval_index + 2
            }
        else:
            return {
                "description": f"Interval stays at <strong>{self.interval.days} day{pluralize(self.interval.days)}</strong>",
                "interval": self.interval,
                "interval_index": self.interval_index
            }

    def _hard_response(self):
        """
        Get the interval changes based on a question response of "hard"
        """

        if self.interval_index > 1:
            new_interval = timedelta(days=self.user.userprofile.drill_intervals[self.interval_index - 2])
            return {
                "description": f"Decrease interval to <strong>{new_interval.days} day{pluralize(new_interval.days)}</strong>",
                "interval": new_interval,
                "interval_index": self.interval_index - 2
            }
        else:
            return {
                "description": f"Interval stays at <strong>{self.interval.days} day{pluralize(self.interval.days)}</strong>",
                "interval": timedelta(days=1),
                "interval_index": 0
            }

    def get_intervals(self, description_only=False):
        """
        Get all the possible interval changes based on various question responses
        """
        intervals = {
            "good": self._good_response(),
            "easy": self._easy_response(),
            "hard": self._hard_response(),
            "reset": {
                "description": "Reset interval to <strong>1 day</strong>",
                "interval": timedelta(days=1),
                "interval_index": 0
            }
        }

        if description_only:
            # Extract the "description" key from each dictionary
            return {
                outer_k: {
                    inner_k: inner_v
                    for inner_k, inner_v in outer_v.items() if inner_k == "description"
                }
                for outer_k, outer_v in intervals.items()
            }

        else:
            return intervals

    def record_response(self, response):
        """
        Modify the question's parameters based on the user's
        self-reported answer.
        """

        intervals = self.get_intervals()
        self.interval = intervals[response]["interval"]
        self.interval_index = intervals[response]["interval_index"]
        self.last_reviewed = timezone.now()
        self.save()

        response = QuestionResponse(question=self, response=response)
        response.save()

    def get_last_response(self):
        """
        Get the last response for this question
        """
        return QuestionResponse.objects.filter(
            question=self
        ).order_by("-date").first()

    def get_all_tags_progress(self):
        """
        Get review progress for all tags assocated with this question.
        """

        info = []

        for tag in self.tags.all():
            info.append(Question.get_tag_progress(self.user, tag.name))

        return info

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)

        # Index the question and answer in Elasticsearch
        self.index_question()

    def delete(self):

        es = get_elasticsearch_connection(host=settings.ELASTICSEARCH_ENDPOINT)
        es.delete(index=settings.ELASTICSEARCH_INDEX, id=self.uuid)

        super().delete()

    def index_question(self, es=None):

        if not es:
            es = get_elasticsearch_connection(host=settings.ELASTICSEARCH_ENDPOINT)

        count, errors = helpers.bulk(es, [self.elasticsearch_document])

    def add_related_object(self, object_uuid):

        blob = Blob.objects.filter(uuid=object_uuid)
        if blob.exists():
            args = {"blob": blob.first()}
        else:
            bookmark = Bookmark.objects.filter(uuid=object_uuid)
            if bookmark.exists():
                args = {"bookmark": bookmark.first()}

        if QuestionToObject.objects.filter(node=self, **args).exists():
            response = {
                "status": "Error",
                "message": "That object is already related",
            }
        else:
            QuestionToObject.objects.create(node=self, **args)
            response = {
                "status": "OK",
            }

        return response

    @property
    def elasticsearch_document(self):
        """
        Return a representation of the drill question suitable for indexing in Elasticsearch
        """
        doc = {
            "_index": settings.ELASTICSEARCH_INDEX,
            "_id": self.uuid,
            "_source": {
                "uuid": self.uuid,
                "bordercore_id": self.id,
                "question": self.question,
                "answer": self.answer,
                "tags": [tag.name for tag in self.tags.all()],
                "importance": 10 if self.is_favorite else 1,
                "last_modified": self.modified,
                "doctype": "drill",
                "date": {"gte": self.created.strftime("%Y-%m-%d %H:%M:%S"), "lte": self.created.strftime("%Y-%m-%d %H:%M:%S")},
                "date_unixtime": self.created.strftime("%s"),
                "user_id": self.user.id,
                **settings.ELASTICSEARCH_EXTRA_FIELDS
            }
        }

        if self.last_reviewed:
            doc["last_reviewed"] = self.last_reviewed.strftime("%s")

        return doc

    @staticmethod
    def start_study_session(user, session, session_type, filter=None, param=None):

        questions = []

        questions = Question.objects.filter(
            user=user
        )

        if session_type == "favorites":
            questions = Question.objects.filter(
                is_favorite=True
            )
        elif session_type == "tag-needing-review":
            for tag in param.split(","):
                questions = questions.filter(
                    tags__name=tag
                )
        elif session_type == "search":
            questions = Question.objects.filter(
                Q(question__icontains=param)
                | Q(answer__icontains=param),
            )

        if filter == "review":
            questions = questions.filter(
                Q(interval__lte=timezone.now() - F("last_reviewed"))
                | Q(last_reviewed__isnull=True)
            )

        questions = questions.order_by("?").values("uuid")

        if session_type == "random":
            count = int(param)
            questions = questions[:count]

        if questions:
            session["drill_study_session"] = {
                "type": session_type,
                "current": str(questions[0]["uuid"]),
                "list": [str(x["uuid"]) for x in questions],
                "tag": param,
                "search_term": param
            }
            return session["drill_study_session"]["current"]

    @staticmethod
    def get_study_session_progress(session):
        if "drill_study_session" in session:
            return session["drill_study_session"]["list"].index(session["drill_study_session"]["current"])

    @staticmethod
    def get_tag_progress(user, tag):
        """
        For all questions with the specified tag, return a summary of testing progress,
        including the last time any of those questions was reviewed, the percentage
        of those questions which need review, and the total question count.
        """
        count = Question.objects.filter(user=user).filter(tags__name=tag).count()

        todo = Question.objects.filter(
            Q(user=user),
            Q(tags__name=tag),
            Q(interval__lte=timezone.now() - F("last_reviewed"))
            | Q(last_reviewed__isnull=True)
        ).count()

        last_reviewed = Tag.objects.filter(
            user=user,
            name=tag).annotate(
                last_reviewed=Max("question__last_reviewed")
            ).first()

        if last_reviewed.last_reviewed:
            last_reviewed = last_reviewed.last_reviewed.strftime("%B %d, %Y")
        else:
            last_reviewed = "Never"

        progress = round(100 - (todo / count * 100)) if count != 0 else 0

        return {
            "name": tag,
            "progress": progress,
            "last_reviewed": last_reviewed,
            "url": reverse("drill:start_study_session_tag", kwargs={"tag": tag}),
            "count": count
        }


class QuestionResponse(models.Model):

    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    response = models.TextField(blank=False, null=False)
    date = models.DateTimeField(auto_now_add=True)


class QuestionToObject(SortOrderMixin):

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    node = models.ForeignKey("drill.Question", null=False, on_delete=models.CASCADE, related_name="nodes")
    blob = models.ForeignKey("blob.Blob", null=True, on_delete=models.CASCADE)
    bookmark = models.ForeignKey("bookmark.Bookmark", null=True, on_delete=models.CASCADE)
    question = models.ForeignKey("drill.Question", null=True, on_delete=models.CASCADE)
    bc_object = models.ForeignKey("drill.BCObject", on_delete=models.CASCADE, null=True)
    note = models.TextField(blank=True, null=True)

    field_name = "node"

    class Meta:
        ordering = ("sort_order",)
        unique_together = (
            ("node", "blob"),
            ("node", "bookmark"),
            ("node", "question")
        )

    def __str__(self):
        if self.blob:
            return f"{self.node} -> {self.blob}"
        elif self.bookmark:
            return f"{self.node} -> {self.bookmark}"
        else:
            return f"{self.node} -> {self.question}"


class BCObject(TimeStampedModel):

    uuid = models.UUIDField(default=uuid.uuid4, editable=False)


@receiver(pre_delete, sender=QuestionToObject)
def remove_relationship(sender, instance, **kwargs):
    instance.handle_delete()
