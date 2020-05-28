import uuid
from functools import cmp_to_key

from elasticsearch import Elasticsearch

from django.conf import settings
from django.contrib.auth.models import User
from django.contrib.postgres.fields import JSONField
from django.core.exceptions import ObjectDoesNotExist
from django.db import models, transaction
from django.db.models import Count, F
from django.db.models.signals import m2m_changed, post_save
from django.dispatch.dispatcher import receiver

from lib.mixins import TimeStampedModel
from tag.models import Tag


class Todo(TimeStampedModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False)
    task = models.TextField()
    note = models.TextField(null=True, blank=True)
    url = models.TextField(null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    due_date = models.DateTimeField(null=True, blank=True)
    tags = models.ManyToManyField(Tag)
    data = JSONField(null=True, blank=True)

    PRIORITY_CHOICES = [
        (1, "High"),
        (2, "Medium"),
        (3, "Low"),
    ]
    priority = models.IntegerField(
        choices=PRIORITY_CHOICES,
        default=2
    )

    def get_modified(self):
        return self.modified.strftime('%b %d, %Y')

    def get_tags(self):
        return ", ".join([tag.name for tag in self.tags.all()])

    @staticmethod
    def get_priority_name(priority_value):
        for priority in Todo.PRIORITY_CHOICES:
            if priority[0] == priority_value:
                return priority[1]
        return None

    @staticmethod
    def get_priority_value(priority_name):
        for priority in Todo.PRIORITY_CHOICES:
            if priority[1] == priority_name:
                return priority[0]
        return None

    @staticmethod
    def get_todo_counts(user, first_tag):

        # Get the list of tags, initially sorted by count per tag
        tags = Tag.objects.values("id", "name") \
                          .annotate(count=Count("todo", distinct=True)) \
                          .filter(todo__user=user) \
                          .order_by("-count")

        # Convert from queryset to list of dicts so we can further sort them
        counts = [{"name": x["name"], "count": x["count"]} for x in tags]

        # Use a custom sort function to insure that the tag matching first_tag
        #  always comes out first.
        counts.sort(key=cmp_to_key(lambda x, y: -1 if x["name"] == first_tag else 1))

        return counts

    def delete(self):

        # Put the imports here to avoid circular dependencies
        from todo.models import TagTodoSortOrder
        for x in TagTodoSortOrder.objects.filter(todo=self):
            x.delete()

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
                                "doctype": "todo"
                            }
                        },
                        {
                            "term": {
                                "uuid.keyword": self.uuid
                            }
                        },

                    ]
                }
            }
        }

        es.delete_by_query(index=settings.ELASTICSEARCH_INDEX, body=request_body)

        super(Todo, self).delete()

    def index_todo(self, es=None):

        if not es:
            es = Elasticsearch(
                [settings.ELASTICSEARCH_ENDPOINT],
                verify_certs=False
            )

        doc = {
            "bordercore_id": self.id,
            "uuid": self.uuid,
            "task": self.task,
            "tags": [tag.name for tag in self.tags.all()],
            "url": self.url,
            "note": self.note,
            "last_modified": self.modified,
            "doctype": "todo",
            "date": {"gte": self.created.strftime("%Y-%m-%d %H:%M:%S"), "lte": self.created.strftime("%Y-%m-%d %H:%M:%S")},
            "date_unixtime": self.created.strftime("%s"),
            "user_id": self.user.id
        }

        res = es.index(
            index=settings.ELASTICSEARCH_INDEX,
            id=self.uuid,
            body=doc
        )


@receiver(post_save, sender=Todo)
def post_save_wrapper(sender, instance, **kwargs):
    """
    This should be called anytime a todo task is added or updated.
    """

    # Index the todo item in Elasticsearch
    instance.index_todo()


def tags_changed(sender, **kwargs):

    # Put the imports here to avoid circular dependencies
    from todo.models import TagTodo, TagTodoSortOrder

    if kwargs["action"] == "post_add":

        todo = kwargs["instance"]
        for tag_id in kwargs["pk_set"]:

            try:
                tt = TagTodo.objects.get(tag_id=tag_id, user=todo.user)
            except ObjectDoesNotExist:
                # If the tag is new, create a new instance
                tt = TagTodo(tag_id=tag_id, user=todo.user)
                tt.save()

            tbso = TagTodoSortOrder(tag_todo=tt, todo=todo)
            tbso.save()

    elif kwargs["action"] == "post_remove":
        todo = kwargs["instance"]
        for tag_id in kwargs["pk_set"]:
            for x in TagTodoSortOrder.objects.filter(todo=todo).filter(tag_todo__tag__id=tag_id):
                x.delete()


m2m_changed.connect(tags_changed, sender=Todo.tags.through)


class TagTodo(models.Model):
    tag = models.OneToOneField(Tag, on_delete=models.PROTECT)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    todos = models.ManyToManyField(Todo, through="TagTodoSortOrder")

    def __unicode__(self):
        return self.tag.name

    def __str__(self):
        return self.tag.name


class TagTodoSortOrder(models.Model):
    tag_todo = models.ForeignKey(TagTodo, on_delete=models.CASCADE)
    todo = models.ForeignKey(Todo, on_delete=models.CASCADE)
    sort_order = models.IntegerField(default=1)

    def delete(self):

        # Get all tags below this one
        # Move them up by decreasing their sort order

        TagTodoSortOrder.objects.filter(
            tag_todo=self.tag_todo,
            sort_order__gte=self.sort_order,
        ).update(
            sort_order=F("sort_order") - 1
        )

        super(TagTodoSortOrder, self).delete()

    def save(self, *args, **kwargs):

        # Don't do this for new objects
        if self.pk is None:
            TagTodoSortOrder.objects.filter(
                tag_todo=self.tag_todo
            ).update(
                sort_order=F("sort_order") + 1
            )

        super(TagTodoSortOrder, self).save(*args, **kwargs)

    def reorder(self, new_position):
        """
        Move a given todo to a new position in a sorted list
        """

        if self.sort_order != new_position:

            with transaction.atomic():
                if self.sort_order > new_position:
                    # Move the tag up the list
                    # All tags between the old position and the new position
                    #  need to be re-ordered by increasing their sort order

                    TagTodoSortOrder.objects.filter(
                        tag_todo=self.tag_todo,
                        sort_order__gte=new_position,
                        sort_order__lt=self.sort_order
                    ).update(
                        sort_order=F("sort_order") + 1
                    )
                else:
                    # Move the tag down the list
                    # All tags between the old position and the new position
                    #  need to be re-ordered by decreasing their sort order

                    TagTodoSortOrder.objects.filter(
                        tag_todo=self.tag_todo,
                        sort_order__lte=new_position,
                        sort_order__gt=self.sort_order
                    ).update(
                        sort_order=F("sort_order") - 1
                    )

                # Finally, update the sort order for the tag in question
                self.sort_order = new_position
                self.save()

    class Meta:
        unique_together = (

            # For a given tag, avoid duplicate todos
            ("tag_todo", "todo"),

        )
        ordering = ("sort_order",)
