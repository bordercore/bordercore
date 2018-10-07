from django.contrib.auth.models import User
from django.db import models

from lib.mixins import TimeStampedModel
from tag.models import Tag

import markdown


class Deck(TimeStampedModel):
    """
    A collection of questions and answers
    """

    title = models.TextField(null=True)
    description = models.TextField(null=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT)

    def get_created(self):
        return self.created.strftime('%b %d, %Y')

    def __unicode__(self):
        return self.title

    def __str__(self):
        return self.title

    def is_empty(self):
        if Question.objects.filter(deck=self).count() == 0:
            return True
        else:
            return False


QUESTION_STATES = (
    ('N', 'New'),
    ('L', 'Learning'),
    ('R', 'To Review'),
)


class Question(TimeStampedModel):
    """
    One question and its answer
    """

    deck = models.ForeignKey(Deck, on_delete=models.PROTECT)
    question = models.TextField()
    answer = models.TextField()
    tags = models.ManyToManyField(Tag, blank=True)
    last_reviewed = models.DateTimeField(null=True)
    times_failed = models.IntegerField(default=0, null=False)
    interval = models.FloatField(default=1.0, blank=False, null=False)
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
        count = 0
        for state in self.LEARNING_STEPS:
            if state[0] == self.learning_step:
                if count == len(self.LEARNING_STEPS) - 1:
                    return True
                else:
                    return False
            count = count + 1

    def learning_step_increase(self):
        count = 0
        for step in self.LEARNING_STEPS:
            if step[0] == self.learning_step:
                print("Match: {}".format(step[0]))
                self.learning_step = self.LEARNING_STEPS[count + 1][0]
                break
            count = count + 1
