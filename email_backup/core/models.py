# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from email_backup.core.validators import (
    ChoicesValidator,
    host_validator,
    bind_port_validator
)
from email_backup.core.connector import POP3, IMAP4

from django.db import models
from django.core.files import File

from email.parser import Parser
from email.utils import (
    parsedate_tz,
    parseaddr,
    mktime_tz
)
import datetime
import StringIO
import binascii
import logging
import hashlib
import base64
import six

logger = logging.getLogger(__name__)


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
    def create_from(self, file_obj, **kwargs):
        if isinstance(file_obj, six.string_types):
            email = Parser().parsestr(file_obj)
        else:
            email = Parser().parse(file_obj)

        read_date = datetime.datetime.now()
        date_str = email.get('date')
        if date_str:
            date_tuple = parsedate_tz(date_str)
            if date_tuple:
                date_stamp = mktime_tz(date_tuple)
                if date_stamp:
                    read_date = datetime.datetime.fromtimestamp(date_stamp)
                else:
                    datetime.datetime(*date_tuple[:7])
        kwargs['send_by'] = parseaddr(email.get('from'))[1]
        kwargs['date'] = read_date
        kwargs['subject'] = email.get('Subject', '')
        if kwargs['subject']:
            enc = email.get('Subject').split('?')
            if enc[0] == enc[-1] == '=':
                try:
                    enc = enc[1:-1]
                    enc_str = base64.decodestring(enc[-1])
                    kwargs['subject'] = enc_str.decode(enc[0])
                except (UnicodeDecodeError, UnicodeEncodeError):
                    logger.exception('Cannot decode {}'.format(kwargs['subject']))
                except binascii.Error:
                    logger.exception('Cannot decode {}'.format(kwargs['subject']))
        if not email.is_multipart():
            enc = email.get('Content-Transfer-Encoding')
            if 'base64' in enc:
                kwargs['content'] = base64.decodestring(email.get_payload)
        else:
            # TODO Multipart
            email.get_boundary()
        # TODO use it ?? email.get('Message-Id')
        email_hash = hashlib.sha512(email.as_string())
        filename = '{}.eml'.format(email_hash.hexdigest())
        kwargs['raw'] = File(StringIO.StringIO(email.as_string()), name=filename)
        self.create(**kwargs)


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
