import uuid
from datetime import timedelta

from elasticsearch import Elasticsearch, helpers

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models import F, Max, Q
from django.db.models.signals import post_save, pre_delete
from django.dispatch.dispatcher import receiver
from django.urls import reverse
from django.utils import timezone

from blob.models import Blob
from bookmark.models import Bookmark
from lib.mixins import SortOrderMixin, TimeStampedModel
from tag.models import Tag

from .managers import DrillManager

QUESTION_STATES = (
    ("N", "New"),
    ("L", "Learning"),
    ("R", "Reviewing"),
)

EASY_FACTOR = 1.3
HARD_FACTOR = 0.7

# Starting "easiness" factor
# Answering "Good" will increase the delay by approximately this amount
EFACTOR_DEFAULT = 2.5

# Multiplication factor for interval
# 1.0 does nothing
# 0.8 sets the interval at 80% their normal size
INTERVAL_MODIFIER = 1.0


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
    efactor = models.FloatField(blank=False, null=False)
    is_favorite = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    bookmarks = models.ManyToManyField(Bookmark, through="SortOrderDrillBookmark")
    blobs = models.ManyToManyField(Blob, through="SortOrderDrillBlob")

    objects = DrillManager()

    LEARNING_STEPS = (
        (1, "1"),
        (2, "10")
    )
    learning_step = models.IntegerField(default=1, null=False)

    state = models.CharField(max_length=1,
                             choices=QUESTION_STATES,
                             default="L")

    def get_tags(self):
        return ", ".join([tag.name for tag in self.tags.all()])

    def __str__(self):
        return self.question

    @staticmethod
    def get_state_name(name):
        for state in QUESTION_STATES:
            if state[0] == name:
                return state[1]
        return None

    def get_learning_step_count(self):
        return len(self.LEARNING_STEPS)

    def is_final_learning_step(self):
        return True if self.learning_step == self.LEARNING_STEPS[-1][0] else False

    def learning_step_increase(self):
        """
        Increment to the next learning step in the LEARNING_STEPS sequence,
        stopping if we've reached the final one
        """

        for i, step in enumerate(self.LEARNING_STEPS):
            if step[0] == self.learning_step and step[0] != self.LEARNING_STEPS[-1][0]:
                self.learning_step = self.LEARNING_STEPS[i + 1][0]

    def record_response(self, response):
        """
        Modify the question's parameters based on the user's
        self-reported answer.
        """

        if response == "good":
            if self.state == "L":
                if self.is_final_learning_step():
                    self.state = "R"
                    self.interval = self.interval * self.efactor * INTERVAL_MODIFIER
                else:
                    self.learning_step_increase()
            else:
                self.interval = self.interval * self.efactor
        elif response == "easy":
            # An "easy" answer to a "Learning" question is graduated to "Reviewing"
            if self.state == "L":
                self.state = "R"
            self.interval = self.interval * self.efactor * EASY_FACTOR * INTERVAL_MODIFIER
            self.efactor = self.efactor + (self.efactor * 0.15)
        elif response == "hard":
            self.times_failed = self.times_failed + 1
            self.interval = self.interval * HARD_FACTOR * INTERVAL_MODIFIER
            self.efactor = self.efactor - (self.efactor * 0.15)
        elif response == "again":
            if self.state == "L":
                self.learning_step = 1
            else:
                self.state = "L"
            self.interval = timedelta(days=1)
            self.efactor = self.efactor - (self.efactor * 0.2)

        self.last_reviewed = timezone.now()
        self.save()

    def get_all_tags_progress(self):
        """
        Get review progress for all tags assocated with this question.
        """

        info = []

        for tag in self.tags.all():
            info.append(Question.get_tag_progress(self.user, tag.name))

        return info

    def delete(self):

        es = Elasticsearch(
            [settings.ELASTICSEARCH_ENDPOINT],
            verify_certs=False
        )

        request_body = {
            "query": {
                "bool": {
                    "must": [
                        {
                            "term": {
                                "doctype": "drill"
                            }
                        },
                        {
                            "term": {
                                "uuid": self.uuid
                            }
                        },

                    ]
                }
            }
        }

        es.delete_by_query(index=settings.ELASTICSEARCH_INDEX, body=request_body)

        super().delete()

    def index_question(self, es=None):

        if not es:
            es = Elasticsearch(
                [settings.ELASTICSEARCH_ENDPOINT],
                verify_certs=False
            )

        count, errors = helpers.bulk(es, [self.elasticsearch_document])

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
                "last_modified": self.modified,
                "doctype": "drill",
                "date": {"gte": self.created.strftime("%Y-%m-%d %H:%M:%S"), "lte": self.created.strftime("%Y-%m-%d %H:%M:%S")},
                "date_unixtime": self.created.strftime("%s"),
                "user_id": self.user.id
            }
        }

        if self.last_reviewed:
            doc["last_reviewed"] = self.last_reviewed.strftime("%s")

        return doc

    @staticmethod
    def start_study_session(user, session, session_type, param=None):

        questions = []

        if session_type == "favorites":
            questions = Question.objects.filter(user=user, is_favorite=True).order_by("?").values("uuid")
        elif session_type == "tag-needing-review":
            questions = Question.objects.filter(
                Q(user=user),
                Q(tags__name=param),
                Q(interval__lte=timezone.now() - F("last_reviewed"))
                | Q(last_reviewed__isnull=True)
                | Q(state="L")
            ).order_by("?").values("uuid")
        elif session_type == "learning":
            questions = Question.objects.filter(
                Q(user=user),
                Q(state="L")
            ).order_by("?").values("uuid")
        elif session_type == "random":
            count = int(param)
            questions = Question.objects.filter(
                Q(user=user)
            ).order_by("?").values("uuid")[:count]
        elif session_type == "search":
            questions = Question.objects.filter(
                Q(user=user),
                Q(question__icontains=param)
                | Q(answer__icontains=param)
            ).order_by("?").values("uuid")

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
            | Q(state="L")).count()

        last_reviewed = Tag.objects.filter(user=user, name=tag).annotate(last_reviewed=Max("question__last_reviewed")).first()

        if last_reviewed.last_reviewed:
            last_reviewed = last_reviewed.last_reviewed.strftime("%B %d, %Y")
        else:
            last_reviewed = "Never"

        if count != 0:
            progress = round(100 - (todo / count * 100))
        else:
            progress = 0

        return {
            "name": tag,
            "progress": progress,
            "last_reviewed": last_reviewed,
            "url": reverse("drill:start_study_session_tag", kwargs={"tag": tag}),
            "count": count
        }


@receiver(post_save, sender=Question)
def post_save_wrapper(sender, instance, **kwargs):
    """
    This should be called anytime a question is created or updated.
    """

    # Index the question and answer in Elasticsearch
    instance.index_question()


class SortOrderDrillBookmark(SortOrderMixin):

    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    bookmark = models.ForeignKey(Bookmark, on_delete=models.CASCADE)

    field_name = "question"

    def __str__(self):
        return f"SortOrder: {self.question}, {self.bookmark}"

    class Meta:
        ordering = ("sort_order",)
        unique_together = (
            ("question", "bookmark")
        )


@receiver(pre_delete, sender=SortOrderDrillBookmark)
def remove_bookmark(sender, instance, **kwargs):
    instance.handle_delete()


class SortOrderDrillBlob(SortOrderMixin):

    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    blob = models.ForeignKey(Blob, on_delete=models.CASCADE)

    field_name = "question"

    def __str__(self):
        return f"SortOrder: {self.question}, {self.blob}"

    class Meta:
        ordering = ("sort_order",)
        unique_together = (
            ("question", "blob")
        )


@receiver(pre_delete, sender=SortOrderDrillBlob)
def remove_blob(sender, instance, **kwargs):
    instance.handle_delete()
