from django.contrib.auth.models import User
from django.db import models
from django.db.models import JSONField


class Contact(models.Model):

    TYPE_CHOICES = (
        ('first_name', 'First Name'),
        ('middle_name', 'Middle Name'),
        ('last_name', 'Last Name'),)

    first_name = models.TextField(blank=True, null=True)
    middle_name = models.TextField(blank=True, null=True)
    last_name = models.TextField(blank=True, null=True)
    preferred_name = models.CharField(max_length=20, choices=TYPE_CHOICES, blank=True, default='first_name')
    mobile_number = models.TextField(blank=True, null=True)
    work_number = models.TextField(blank=True, null=True)
    title = models.TextField(blank=True, null=True)
    address_list = JSONField(blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    im = models.TextField(blank=True, null=True)
    birthday = models.DateField(blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    created = models.DateTimeField(auto_now_add=True)
