# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from unittest import TestCase
from django.core.exceptions import ValidationError
from mock import patch, call
import socket
from email_backup.core.validators import (
    bind_port_validator,
    port_validator,
    host_validator,
    path_validator
)


class PortValidatorTest(TestCase):
    def test_letter(self):
        self.assertRaises(ValidationError, port_validator, 'a')

    def test_float(self):
        self.assertRaises(ValidationError, port_validator, 1.2)

    def test_object(self):
        self.assertRaises(ValidationError, port_validator, object)

    def test_big_int(self):
        self.assertRaises(ValidationError, port_validator, 65536)

    def test_valid(self):
        self.assertIsNone(port_validator(80))


class BindPortValidatorTest(TestCase):
    def test_letter(self):
        self.assertRaises(ValidationError, bind_port_validator, 'a')

    def test_float(self):
        self.assertRaises(ValidationError, bind_port_validator, 1.2)

    def test_object(self):
        self.assertRaises(ValidationError, bind_port_validator, object)

    def test_big_int(self):
        self.assertRaises(ValidationError, bind_port_validator, 65536)

    def test_no_bind(self):
        self.assertRaises(ValidationError, bind_port_validator, 65000)

    def test_valid(self):
        self.assertIsNone(bind_port_validator(80))


class HostValidatorTest(TestCase):
    def test_ip(self):
        self.assertIsNone(host_validator('127.0.0.1'))

    @patch('email_backup.core.validators.socket')
    def test_valid_host(self, sock_mock):
        host = 'domain.host'
        self.assertIsNone(host_validator(host))
        self.assertEqual(sock_mock.gethostbyname.call_count, 1)
        self.assertEqual(sock_mock.gethostbyname.call_args, call(host))

    @patch('email_backup.core.validators.socket.gethostbyname')
    def test_invalid_host(self, gethostbyname_mock):
        gethostbyname_mock.side_effect = socket.error
        host = 'domain.host'
        self.assertRaises(ValidationError, host_validator, host)
        self.assertEqual(gethostbyname_mock.call_count, 1)
        self.assertEqual(gethostbyname_mock.call_args, call(host))


class PathValidatorTest(TestCase):
    def test_root(self):
        self.assertIsNone(path_validator('/'))

    def test_relative_path(self):
        self.assertIsNone(path_validator('./'))

    def test_multi_path(self):
        self.assertRaises(ValidationError, path_validator, '//')

    def test_blank(self):
        self.assertRaises(ValidationError, path_validator, '')

    def test_null(self):
        self.assertRaises(ValidationError, path_validator, '\x00')

    def test_unicode(self):
        self.assertRaises(ValidationError, path_validator, '\uFFFF')

    def test_invalid_chars(self):
        self.assertRaises(ValidationError, path_validator, '\\')
        self.assertRaises(ValidationError, path_validator, '\t')
        self.assertRaises(ValidationError, path_validator, '\r')
        self.assertRaises(ValidationError, path_validator, '\n')
        self.assertRaises(ValidationError, path_validator, '(')
        self.assertRaises(ValidationError, path_validator, ')')
        self.assertRaises(ValidationError, path_validator, '[')
        self.assertRaises(ValidationError, path_validator, ']')
        self.assertRaises(ValidationError, path_validator, '{')
        self.assertRaises(ValidationError, path_validator, '}')
        self.assertRaises(ValidationError, path_validator, '!')
        self.assertRaises(ValidationError, path_validator, '?')
        self.assertRaises(ValidationError, path_validator, '=')
        self.assertRaises(ValidationError, path_validator, '*')
        self.assertRaises(ValidationError, path_validator, '+')
        self.assertRaises(ValidationError, path_validator, '"')
        self.assertRaises(ValidationError, path_validator, "'")
