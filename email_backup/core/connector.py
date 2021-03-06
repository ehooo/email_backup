# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import base64
import binascii
import codecs
import datetime
import imaplib
import locale
import logging
import re
from email.parser import Parser
from email.quoprimime import header_decode
from email.utils import (
    parsedate_tz,
    parseaddr,
    mktime_tz,
    ecre
)

import six

logger = logging.getLogger(__name__)

RE_IMAP4_DIR_NAME = re.compile('"([\w/\[\] .-]+)"$', re.UNICODE)

if not six.PY2:  # pragma: no cover
    unicode = str


def get_email_content(email):
    content = None
    if email.is_multipart():
        for e in email.get_payload():
            content = get_email_content(e)
            if content:
                break
    elif email.get_content_maintype() == 'text':
        enc = email.get('Content-Transfer-Encoding', '')
        if 'base64' in enc:
            content = base64.decodestring(six.b(email.get_payload()))
        else:
            content = six.b(email.get_payload())
    enc = email.get('Content-Type', '')
    if enc:
        find = re.findall('charset="([\w-]+)"', enc)
        if find:
            content = codecs.decode(content, find[0], 'strict')
    return content


class Email(object):
    def __init__(self, connector, server_id, directory):
        assert isinstance(connector, EmailConnectorInterface)
        self.id = server_id
        self.connector = connector
        self.directory = directory
        self.email = None
        self._header = False
        self._full = False
        self.raw = None

    @property
    def server_id(self):
        return self.id

    def load(self, only_header=False):
        self.connector.chdir(self.directory)
        msg = None
        if only_header:
            if not self._header:
                msg = self.connector.header(self.id)
            self._header = True
        else:
            if not self._full:
                msg = self.connector.read(self.id)
                self.raw = msg
            self._header = True
            self._full = True
        if msg:
            self.email = Parser().parsestr(msg)

    def __unicode__(self):
        return "[{}] {}".format(self.id, self.directory)

    def __str__(self):
        return "[{}] {}".format(self.id, self.directory)

    def date(self, default=None):
        self.load(True)
        if not self.email:
            return default
        read_date = default
        date_str = self.email.get('date', None)
        if date_str:
            date_tuple = parsedate_tz(date_str)
            if date_tuple:
                read_date = datetime.datetime.fromtimestamp(mktime_tz(date_tuple))
        return read_date

    def send_by(self, default=None):
        self.load(True)
        return parseaddr(self.email.get('from'))[1] or default

    def attaches(self):
        self.load()
        if self.email.is_multipart():
            return len(self.email.get_payload())
        return 0

    def subject(self, default=None):
        self.load(True)
        subject = self.email.get('Subject', default)
        match = ecre.match(subject)
        if match:
            try:
                subject_data = match.groupdict()
                enc_subject = b''
                if subject_data['encoding'] in ['q', 'Q']:
                    enc_subject = six.b(header_decode(subject_data['atom']))
                elif subject_data['encoding'] in ['b', 'B']:
                    enc_subject = base64.decodestring(six.b(subject_data['atom']))
                subject = codecs.decode(enc_subject, subject_data['charset'], 'strict')
            except (UnicodeDecodeError, UnicodeEncodeError):
                logger.exception('Cannot decode {}'.format(subject))
            except binascii.Error:
                logger.exception('Cannot decode {}'.format(subject))
        return subject

    def content(self):
        self.load()
        return get_email_content(self.email)

    def get(self, key, default=None):
        self.load(True)
        if key.lower() == 'date':
            return self.date(default)
        elif key.lower() in ['from', 'send_by']:
            return self.send_by(default)
        elif key.lower() == 'subject':
            return self.subject(default)
        return self.email.get(key, default)


class EmailConnectorInterface(object):
    def __init__(self, host, port, ssl, user, password):
        self.host = host
        self.port = port
        self.ssl = ssl
        self.user = user
        self.password = password
        self.connection = None

    def open(self):
        if self.ssl:
            self.connection = imaplib.IMAP4_SSL(self.host, self.port)
        else:
            self.connection = imaplib.IMAP4(self.host, self.port)
        self.connection.login(self.user, self.password)

    def close(self):
        if self.connection:
            try:
                self.connection.close()
                self.connection.logout()
            except imaplib.IMAP4.error:
                pass  # Error because not login?
            finally:
                sock = self.connection.socket()
                sock.close()
        self.connection = None

    def directories(self):
        directories = []
        if self.connection:
            _, lines = self.connection.list()
            for line in lines:
                find = RE_IMAP4_DIR_NAME.findall(line)
                if find:
                    directories.append(find[0])
        return directories

    def get_emails(self, directory, before=None, just_read=False):
        ids = []
        if self.connection:
            num_emails = self.chdir(directory)
            ids = range(1, int(num_emails) + 1)
            queries = []
            if before:
                before_date = None
                if isinstance(before, (datetime.date, datetime.datetime)):
                    before_date = before
                elif isinstance(before, six.string_types):
                    try:
                        before_date = datetime.datetime.strptime(before, '%d-%b-%Y')
                    except ValueError:
                        pass
                else:
                    raise ValueError('Invalid before')
                try:
                    code, enc = locale.getlocale(locale.LC_TIME)
                    if code == enc:  # Only code == enc is both are None
                        code, enc = locale.getdefaultlocale()
                    loc_code = '{}.{}'.format(code, enc)
                    locale.setlocale(locale.LC_TIME, 'en_GB.UTF-8')
                    if not before_date and isinstance(before, six.string_types):
                        before_date = datetime.datetime.strptime(before, '%d-%b-%Y')
                    queries.append('(before "{}")'.format(before_date.strftime('%d-%b-%Y')))
                    locale.setlocale(locale.LC_TIME, loc_code)
                except locale.Error:
                    pass
            if just_read:
                queries.append('(SEEN)')
            if queries:
                _, (ids_inline,) = self.connection.search(None, *queries)
                ids = ids_inline.split()
        for i in ids:
            yield Email(self, i, directory)

    def read(self, email_id):
        msg = None
        if self.connection and email_id > 0:
            try:
                _, ((_, msg), _) = self.connection.fetch(email_id, '(RFC822)')
            except ValueError:
                pass
        return msg

    def header(self, email_id):
        msg = None
        if self.connection and email_id > 0:
            try:
                _, ((_, msg), _) = self.connection.fetch(email_id, '(BODY.PEEK[HEADER])')
            except ValueError:
                pass
        return msg

    def chdir(self, directory):
        num_emails = 0
        if self.connection and directory:
            ok, (num_emails,) = self.connection.select(directory)
            if ok == 'OK':
                num_emails = int(num_emails)
            else:
                num_emails = 0
        return num_emails

    def mark_delete(self, email_id):
        if self.connection and email_id > 0:
            self.connection.store(email_id, '+FLAGS', '\\Deleted')

    def do_delete(self):
        if self.connection:
            self.connection.expunge()
