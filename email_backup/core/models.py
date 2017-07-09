# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from email_backup.core.validators import (
    ChoicesValidator,
    host_validator,
    bind_port_validator
)
from email_backup.core.connector import (
    POP3,
    IMAP4,
    Email
)

from django.db import models
from django.core.files import File

import StringIO
import hashlib


class EmailAccount(models.Model):
    PROTOCOLS = (
        (POP3, 'POP3'),
        (IMAP4, 'IMAP4')
    )
    user = models.CharField(max_length=128)
    password = models.CharField(max_length=128)
    host = models.CharField(max_length=64,
                            validators=[host_validator])
    path = models.CharField(max_length=512, default='/')
    protocol = models.IntegerField(choices=PROTOCOLS, default=IMAP4,
                                   validators=[ChoicesValidator(PROTOCOLS)])
    ssl = models.BooleanField(default=True)
    port = models.IntegerField(default=993, validators=[bind_port_validator])

    class Meta:
        unique_together = ("user", "host")


class EmailManager(models.Manager):
    def create_from(self, email, **kwargs):
        assert isinstance(email, Email), 'Only support Email objects'

        kwargs['message_id'] = email.get('Message-Id')
        kwargs['send_by'] = email.get('from')
        kwargs['date'] = email.get('date')
        kwargs['subject'] = email.get('Subject', '')
        kwargs['subject'] = email.get('Subject')
        kwargs['content'] = email.content
        kwargs['attaches'] = email.attaches

        email_hash = hashlib.sha512(unicode(email))
        filename = '{}.eml'.format(email_hash.hexdigest())
        kwargs['raw'] = File(StringIO.StringIO(unicode(email)), name=filename)

        return self.create(**kwargs)


class Email(models.Model):
    account = models.ForeignKey(EmailAccount)
    raw = models.FileField(null=True)
    message_id = models.CharField(max_length=1024, default='message_id@localhost')
    # For search proposed
    send_by = models.EmailField()
    subject = models.CharField(max_length=512, blank=True)
    content = models.TextField(blank=True)
    attaches = models.IntegerField(default=0)
    date = models.DateTimeField()
    folder = models.CharField(max_length=512, default='/')

    objects = EmailManager()

    class Meta:
        unique_together = ("account", "message_id")
