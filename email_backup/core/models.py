# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from email_backup.core.validators import (
    ChoicesValidator,
    host_validator,
    bind_port_validator
)
from django.db import models
from email.parser import Parser


class EmailAccount(models.Model):
    PROTOCOLS = (
        (0, 'POP3'),
        (1, 'IMAP4')
    )
    user = models.CharField(max_length=128)
    password = models.CharField(max_length=128)
    host = models.CharField(max_length=64,
                            validators=[host_validator])
    path = models.CharField(max_length=512, default='/')
    protocol = models.IntegerField(choices=PROTOCOLS, default=0,
                                   validators=[ChoicesValidator(PROTOCOLS)])
    ssl = models.BooleanField(default=True)
    port = models.IntegerField(default=995, validators=[bind_port_validator])

    class Meta:
        unique_together = ("user", "host")


class EmailManager(models.Manager):
    def create_from(self, file_obj):
        parser = Parser().parse(file_obj)
        # TODO


class Email(models.Model):
    account = models.ForeignKey(EmailAccount)
    raw = models.FileField(null=True)
    # For search proposed
    send_by = models.EmailField()
    subject = models.CharField(max_length=512, blank=True)
    content = models.TextField(blank=True)
    attaches = models.IntegerField(default=0)
    date = models.DateTimeField()
    folder = models.CharField(max_length=512, default='/')

    objects = EmailManager()
