import uuid
from datetime import timedelta

import markdown
from elasticsearch import Elasticsearch
from markdown.extensions.codehilite import CodeHiliteExtension

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models import F, Q
from django.db.models.signals import post_save
from django.dispatch.dispatcher import receiver
from django.utils import timezone

from lib.mixins import TimeStampedModel
from tag.models import Tag

QUESTION_STATES = (
    ('N', 'New'),
    ('L', 'Learning'),
    ('R', 'To Review'),
)

EASY_BONUS = 1.3

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
    user = models.ForeignKey(User, on_delete=models.PROTECT)

    LEARNING_STEPS = (
        (1, '1'),
        (2, '10')
    )
    learning_step = models.IntegerField(default=1, null=False)

    state = models.CharField(max_length=1,
                             choices=QUESTION_STATES,
                             default='L')

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

    def get_question(self):
        return markdown.markdown(self.question, extensions=[CodeHiliteExtension(guess_lang=False), "tables", "pymdownx.arithmatex"])

    def get_answer(self):
        return markdown.markdown(self.answer, extensions=[CodeHiliteExtension(guess_lang=False), "tables", "pymdownx.arithmatex"])

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
                else:
                    self.learning_step_increase()
            else:
                self.interval = self.interval * self.efactor
        elif response == "easy":
            # An "easy" answer to a "Learning" question is
            #  graduated to "To Review"
            if self.state == "L":
                self.state = "R"
            self.interval = self.interval * EASY_BONUS * INTERVAL_MODIFIER
            self.efactor = self.efactor + (self.efactor * 0.15)
        elif response == "hard":
            self.times_failed = self.times_failed + 1
            self.interval = self.interval * 1.2 * INTERVAL_MODIFIER
            self.efactor = self.efactor - (self.efactor * 0.15)
        elif response == "again":
            if self.state == "L":
                self.learning_step = 1
            else:
                self.state = "L"
            self.interval = timedelta(days=1)
            self.efactor = self.efactor - (self.efactor * 0.2)

        self.save()

    def get_tag_info(self):

        info = []

        for tag in self.tags.all():

            count = Question.objects.filter(user=self.user).filter(tags=tag).count()
            todo = Question.objects.filter(
                Q(user=self.user),
                Q(tags__name=tag),
                Q(interval__lte=timezone.now() - F("last_reviewed"))
                | Q(last_reviewed__isnull=True)
                | Q(state="L")).count()

            info.append(
                {
                    "name": tag.name,
                    "progress": 100 - (todo / count * 100)
                }
            )

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

        super(Question, self).delete()

    def index_question(self, es=None):

        if not es:
            es = Elasticsearch(
                [settings.ELASTICSEARCH_ENDPOINT],
                verify_certs=False
            )

        doc = {
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

        if self.last_reviewed:
            doc["last_reviewed"] = self.last_reviewed.strftime("%s")

        es.index(
            index=settings.ELASTICSEARCH_INDEX,
            id=self.uuid,
            body=doc
        )


@receiver(post_save, sender=Question)
def post_save_wrapper(sender, instance, **kwargs):
    """
    This should be called anytime a question is created or updated.
    """

    # Index the question and answer in Elasticsearch
    instance.index_question()
