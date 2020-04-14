from datetime import timedelta

import markdown

from django.contrib.auth.models import User
from django.db import models

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

    def __unicode__(self):
        return self.question

    def __str__(self):
        return self.question

    @staticmethod
    def get_state_name(name):
        for state in QUESTION_STATES:
            if state[0] == name:
                return state[1]
        return None

    def get_question(self):
        return markdown.markdown(self.question, extensions=['codehilite(guess_lang=False)', 'tables'])

    def get_answer(self):
        return markdown.markdown(self.answer, extensions=['codehilite(guess_lang=False)', 'tables'])

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
