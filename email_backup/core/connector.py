# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from email.parser import Parser
from email.utils import (
    parsedate_tz,
    parseaddr,
    mktime_tz
)
from email.errors import MessageError

import datetime
import binascii
import logging
import imaplib
import poplib
import base64
import locale
import six
import re

logger = logging.getLogger(__name__)


POP3 = 0
IMAP4 = 1
RE_IMAP4_DIR_NAME = re.compile('"([\w\s/\[\]]+)"$')


def get_email_content(email):
    content = None
    if email.is_multipart():
        for e in email:
            content = get_email_content(e)
            if content:
                break
    elif email.get_content_maintype() == 'text':
        enc = email.get('Content-Transfer-Encoding')
        if 'base64' in enc:
            content = base64.decodestring(email.get_payload())
        else:
            content = email.get_payload()
    return content


class TmpEmail(object):
    def __init__(self, server_id, file_obj, directory=None):
        self.id = server_id
        if isinstance(file_obj, six.string_types):
            self.email = Parser().parsestr(file_obj)
        else:
            self.email = Parser().parse(file_obj)
        self.directory = directory

    def __unicode__(self):
        return self.email.as_string()

    def date(self, default=None):
        read_date = default
        date_str = self.email.get('date', default)
        if date_str:
            date_tuple = parsedate_tz(date_str)
            if date_tuple:
                date_stamp = mktime_tz(date_tuple)
                if date_stamp:
                    read_date = datetime.datetime.fromtimestamp(date_stamp)
                else:
                    read_date = datetime.datetime(*date_tuple[:7])
        return read_date

    def send_by(self, default=None):
        return parseaddr(self.email.get('from'))[1] or default

    def attaches(self):
        if self.email.is_multipart():
            return len(self.email.get_payload())
        return 0

    def subject(self, default=None):
        subject = self.email.get('Subject', default)
        if subject:
            enc = subject.split('?')
            if enc[0] == enc[-1] == '=':
                try:
                    enc = enc[1:-1]
                    enc_str = base64.decodestring(enc[-1])
                    subject = enc_str.decode(enc[0])
                except (UnicodeDecodeError, UnicodeEncodeError):
                    logger.exception('Cannot decode {}'.format(subject))
                except binascii.Error:
                    logger.exception('Cannot decode {}'.format(subject))
        return subject

    def content(self):
        return get_email_content(self.email)

    def get(self, key, default=None):
        if key.lower() == 'date':
            return self.date(default)
        elif key.lower() in ['from', 'send_by']:
            return self.send_by(default)
        elif key.lower() == 'subject':
            return self.subject(default)
        return self.email.get(key, default)


class EmailConnectorInterface(object):
    def __init__(self, protocol, host, port, ssl, user, password):
        assert protocol in [POP3, IMAP4], "Protocol not allowed"
        self.protocol = protocol
        self.host = host
        self.port = port
        self.ssl = ssl
        self.user = user
        self.password = password
        self.connection = None

    def open(self):
        if self.protocol == POP3:
            if self.ssl:
                self.connection = poplib.POP3_SSL(self.host, self.port)
            else:
                self.connection = poplib.POP3(self.host, self.port)
        elif self.protocol == IMAP4:
            if self.ssl:
                self.connection = imaplib.IMAP4_SSL(self.host, self.port)
            else:
                self.connection = imaplib.IMAP4(self.host, self.port)

    def close(self):
        if self.connection:
            if self.protocol == POP3:
                self.connection.quit()
            elif self.protocol == IMAP4:
                try:
                    self.connection.close()
                    self.connection.logout()
                except imaplib.IMAP4.error:
                    pass  # Error because not login
                finally:
                    sock = self.connection.socket()
                    sock.close()
        self.connection = None

    def login(self):
        if self.connection:
            if self.protocol == POP3:
                try:
                    self.connection.apop(self.user, self.password)
                except poplib.error_proto:
                    self.connection.user(self.user)
                    self.connection.pass_(self.password)

            elif self.protocol == IMAP4:
                self.connection.login(self.user, self.password)

    def directories(self):
        directories = []
        if self.connection and self.protocol == IMAP4:
            _, lines = self.connection.list()
            for line in lines:
                find = RE_IMAP4_DIR_NAME.findall(line)
                if find:
                    directories.append(find[0])
        return directories

    def emails(self, directory=None, before=None):
        if self.connection:
            if self.protocol == POP3:
                _, mgs, _ = self.connection.list()
                for i in range(1, len(mgs)):
                    _, lines, _ = self.connection.retr(i)
                    try:
                        yield TmpEmail(i, '\r\n'.join(lines))
                    except MessageError:
                        logger.exception('Error processing email {}'.format(i))

            elif self.protocol == IMAP4:
                _, (mgs, ) = self.connection.select(directory)
                ids = range(1, mgs)
                if before and isinstance(before, (datetime.date, datetime.datetime)):
                    try:
                        code, enc = locale.getlocale(locale.LC_TIME)
                        if code == enc:  # Only code == enc is both are None
                            code, enc = locale.getdefaultlocale()
                        loc_code = '{}.{}'.format(code, enc)
                        locale.setlocale(locale.LC_TIME, 'en_GB.UTF-8')
                        _, (mgs,) = self.connection.search(None, '(before "{}")'.format(before.strftime('%d-%b-%Y')))
                        ids = mgs.split()
                        locale.setlocale(locale.LC_TIME, loc_code)
                    except locale.Error:
                        pass
                for i in ids:
                    _, ((_, msg), _) = self.connection.fetch(i, '(RFC822)')
                    try:
                        yield TmpEmail(i, msg, directory)
                    except MessageError:
                        logger.exception('Error processing email {} on {}'.format(i, directory))

    def delete(self, tmp_email):
        if self.connection:
            if self.protocol == POP3:
                self.connection.dele(tmp_email.id)
            elif self.protocol == IMAP4:
                self.connection.select(tmp_email.directory)
                self.connection.store(tmp_email.id, '+FLAGS', '\\Deleted')
                self.connection.expunge()
