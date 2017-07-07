# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import poplib
import imaplib


POP3 = 0
IMAP4 = 1


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
                self.connection.close()
                self.connection.logout()
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
        if self.connection and self.protocol == IMAP4:
            pass

    def emails(self, directory=None):
        if self.connection:
            if self.protocol == POP3:
                _, mgs, _ = self.connection.list()
                for i in range(1, len(mgs)):
                    _, lines, _ = self.connection.retr(i)
                    yield '\r\n'.join(lines)
            elif self.protocol == IMAP4:
                pass
