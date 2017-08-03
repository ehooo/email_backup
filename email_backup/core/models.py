# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from email_backup.core.validators import (
    host_validator,
    bind_port_validator,
    path_validator
)
from email_backup.core.connector import Email as TmpEmail
from email_backup.core.connector import EmailConnectorInterface

from django.db import models
from django.core.files import File
from django.utils.translation import ugettext_lazy as _
from django.core.files.storage import default_storage

from six import StringIO
import hashlib
import os


class EmailAccount(models.Model):
    user = models.CharField(max_length=128)
    password = models.CharField(max_length=128)
    host = models.CharField(max_length=64,
                            validators=[host_validator])
    path = models.CharField(max_length=512, default='.', validators=[path_validator])
    ssl = models.BooleanField(default=True)
    port = models.PositiveIntegerField(default=993, validators=[bind_port_validator])

    sync = models.BooleanField(default=False)
    weeks_before = models.PositiveSmallIntegerField(
        default=0, blank=True,
        help_text=_("Number of weeks until the system should process emails")
    )
    remove = models.BooleanField(
        default=False,
        help_text=_("Should the system remove emails when they are processed?")
    )
    just_read = models.BooleanField(
        default=True,
        help_text=_("Should de system ignore the unread emails?")
    )

    class Meta:
        unique_together = ("user", "host")

    def __unicode__(self):
        return "{} at [{}]".format(self.user, self.host)

    def __str__(self):
        return "{} at [{}]".format(self.user, self.host)

    def connector(self):
        return EmailConnectorInterface(self.host, self.port, self.ssl, self.user, self.password)


class EmailPath(models.Model):
    account = models.ForeignKey(EmailAccount, related_name='ignore')
    path = models.CharField(max_length=2048, validators=[path_validator])
    ignore = models.BooleanField(default=False)

    class Meta:
        unique_together = ("account", "path")

    def __unicode__(self):
        return self.path

    def __str__(self):
        return self.path


class EmailManager(models.Manager):
    def filter_from(self, email):
        assert isinstance(email, TmpEmail), 'Only support {} objects'.format(TmpEmail.__class__)
        email.load(True)
        return self.get_queryset().filter(message_id=email.get('Message-Id'))

    def get_or_create_from(self, email, **kwargs):
        assert isinstance(email, TmpEmail), 'Only support {} objects'.format(TmpEmail.__class__)
        account = kwargs.get('account', None)
        assert account, 'Account is required'
        email.load(True)
        exist = self.get_queryset().filter(message_id=email.get('Message-Id'), account=account)
        if exist.exists():
            return exist.get(), False
        return self.create_from(email, **kwargs), True

    def create_from(self, email, **kwargs):
        assert isinstance(email, TmpEmail), 'Only support {} objects'.format(TmpEmail.__class__)
        account = kwargs.get('account', None)
        assert account, 'Account is required'
        email.load()

        kwargs['message_id'] = email.get('Message-Id')
        kwargs['send_by'] = email.get('from')
        kwargs['date'] = email.get('date')
        kwargs['subject'] = email.get('Subject', '')
        kwargs['content'] = email.content()
        kwargs['attaches'] = email.attaches()

        email_hash = hashlib.sha512(email.raw or '')

        base_path = '.'
        try:
            base_path = default_storage.path('.')
        except NotImplementedError:
            pass
        filename = '{}/{}/{}.eml'.format(base_path, account.path, email_hash.hexdigest())
        filename = os.path.abspath(filename)
        kwargs['raw'] = File(StringIO(unicode(email)), name=filename)

        return self.create(**kwargs)


class Email(models.Model):
    account = models.ForeignKey(EmailAccount)
    raw = models.FileField()
    message_id = models.CharField(max_length=1024)
    # For search proposed
    send_by = models.EmailField()
    subject = models.CharField(max_length=512, blank=True)
    content = models.TextField(blank=True)
    attaches = models.IntegerField(default=0)
    date = models.DateTimeField()
    paths = models.ManyToManyField(EmailPath, related_name='emails')

    objects = EmailManager()

    class Meta:
        unique_together = ("account", "message_id")
