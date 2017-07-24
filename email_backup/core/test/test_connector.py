# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from unittest import TestCase
from mock import Mock, patch, call
from email_backup.core.connector import EmailConnectorInterface
from datetime import date
import locale


class OpenTest(TestCase):
    @patch('email_backup.core.connector.imaplib')
    def test_open(self, imap4_mock):
        host, port = 'imap.host.test', 143
        user, password = 'user', 'password'
        login_mock = Mock()
        login_mock.login = Mock()
        imap4_mock.IMAP4.return_value = login_mock

        conn = EmailConnectorInterface(host, port, False, user, password)
        conn.open()

        self.assertEqual(imap4_mock.IMAP4.call_count, 1)
        self.assertEqual(imap4_mock.IMAP4.call_args, call(host, port))
        self.assertEqual(login_mock.login.call_count, 1)
        self.assertEqual(login_mock.login.call_args, call(user, password))

    @patch('email_backup.core.connector.imaplib')
    def test_open_ssl(self, imap4_mock):
        host, port = 'imap.host.test', 993
        user, password = 'user', 'password'
        login_mock = Mock()
        login_mock.login = Mock()
        imap4_mock.IMAP4_SSL.return_value = login_mock

        conn = EmailConnectorInterface(host, port, True, user, password)
        conn.open()

        self.assertEqual(imap4_mock.IMAP4_SSL.call_count, 1)
        self.assertEqual(imap4_mock.IMAP4_SSL.call_args, call(host, port))
        self.assertEqual(login_mock.login.call_count, 1)
        self.assertEqual(login_mock.login.call_args, call(user, password))


class CloseTest(TestCase):
    def setUp(self):
        host, port, ssl, user, password = 'imap.host.test', 143, False, 'user', 'password'
        self.conn = EmailConnectorInterface(host, port, ssl, user, password)

    def test_close(self):
        connection = Mock()
        self.conn.connection = connection
        sock_mock = Mock()
        self.conn.connection.socket.return_value = sock_mock
        self.conn.close()

        self.assertEqual(connection.close.call_count, 1)
        self.assertEqual(connection.close.call_args, call())
        self.assertEqual(connection.logout.call_count, 1)
        self.assertEqual(connection.logout.call_args, call())
        self.assertEqual(connection.socket.call_count, 1)
        self.assertEqual(connection.socket.call_args, call())
        self.assertEqual(sock_mock.close.call_count, 1)
        self.assertEqual(sock_mock.close.call_args, call())
        self.assertIsNone(self.conn.connection)

    def test_close_not_open(self):
        self.conn.close()


class DirectoriesTest(TestCase):
    def setUp(self):
        host, port, ssl, user, password = 'imap.host.test', 143, False, 'user', 'password'
        self.conn = EmailConnectorInterface(host, port, ssl, user, password)
        self.conn.connection = Mock()

    def test_directories_not_open(self):
        self.conn.connection = None
        result = self.conn.directories()
        self.assertEqual(result, [])

    def test_directories_empty(self):
        self.conn.connection.list = Mock()
        self.conn.connection.list.return_value = ('OK', [])
        result = self.conn.directories()
        self.assertEqual(self.conn.connection.list.call_count, 1)
        self.assertEqual(self.conn.connection.list.call_args, call())
        self.assertEqual(result, [])

    def test_directories_with_valid(self):
        valid_without_tildes = ['valid dir', '[Also]valid', 'And_this', 'or-this', 'or/dir', 'with.points']
        valid = []
        for v in valid_without_tildes:
            valid.append('"{}"'.format(v))
        invalid = ['"\tinvalid"', '"invalid\r"', '"invalid\n"', '"invalid?"', 'invalid']
        data = valid[:]
        data.extend(invalid)
        self.conn.connection.list = Mock()
        self.conn.connection.list.return_value = ('OK', data)
        result = self.conn.directories()
        self.assertEqual(result, valid_without_tildes)
        self.assertEqual(self.conn.connection.list.call_count, 1)
        self.assertEqual(self.conn.connection.list.call_args, call())

    def test_directories_not_exist(self):
        pass  # TODO


class FetchTest(TestCase):
    def setUp(self):
        host, port, ssl, user, password = 'imap.host.test', 143, False, 'user', 'password'
        self.conn = EmailConnectorInterface(host, port, ssl, user, password)
        self.conn.connection = Mock()
        self.conn.connection.fetch = Mock()

    def test_read_not_open(self):
        self.conn.connection = None
        email_id = 1
        result = self.conn.read(email_id)
        self.assertEqual(result, None)

    def test_read(self):
        msg = 'Message'
        data = (('', msg), '')
        email_id = 1
        self.conn.connection.fetch.return_value = ('OK', data)
        result = self.conn.read(email_id)
        self.assertEqual(result, msg)
        self.assertEqual(self.conn.connection.fetch.call_count, 1)
        self.assertEqual(self.conn.connection.fetch.call_args, call(email_id, '(RFC822)'))

    def test_header_not_open(self):
        self.conn.connection = None
        email_id = 1
        result = self.conn.header(email_id)
        self.assertEqual(result, None)

    def test_header(self):
        msg = 'Message'
        data = (('', msg), '')
        email_id = 1
        self.conn.connection.fetch.return_value = ('OK', data)
        result = self.conn.header(email_id)
        self.assertEqual(result, msg)
        self.assertEqual(self.conn.connection.fetch.call_count, 1)
        self.assertEqual(self.conn.connection.fetch.call_args, call(email_id, '(BODY.PEEK[HEADER])'))

    def test_wrong_zero(self):
        email_id = 0
        result = self.conn.header(email_id)
        self.assertIsNone(result)
        self.assertEqual(self.conn.connection.fetch.call_count, 0)

    def test_wrong_index_out(self):
        data = [None]
        email_id = 99999
        self.conn.connection.fetch.return_value = ('OK', data)

        result = self.conn.header(email_id)
        self.assertIsNone(result)
        self.assertEqual(self.conn.connection.fetch.call_count, 1)
        self.assertEqual(self.conn.connection.fetch.call_args, call(email_id, '(BODY.PEEK[HEADER])'))

        result = self.conn.read(email_id)
        self.assertIsNone(result)
        self.assertEqual(self.conn.connection.fetch.call_count, 2)
        self.assertIn(call(email_id, '(RFC822)'), self.conn.connection.fetch.call_args_list)


class ChDirTest(TestCase):
    def setUp(self):
        host, port, ssl, user, password = 'imap.host.test', 143, False, 'user', 'password'
        self.conn = EmailConnectorInterface(host, port, ssl, user, password)
        self.conn.connection = Mock()
        self.conn.connection.select = Mock()

    def test_chdir_not_open(self):
        self.conn.connection = None
        result = self.conn.chdir('dir')
        self.assertEqual(result, 0)

    def test_chdir(self):
        directory = 'dir'
        ret_val = '5'
        self.conn.connection.select.return_value = ('OK', [ret_val])
        result = self.conn.chdir(directory)
        self.assertEqual(result, 5)
        self.assertEqual(self.conn.connection.select.call_count, 1)
        self.assertEqual(self.conn.connection.select.call_args, call(directory))

    def test_wrong_chdir(self):
        directory = 'not exist'
        ret_val = ['[NONEXISTENT] Unknown Mailbox:  (Failure)']
        self.conn.connection.select.return_value = ('NO', ret_val)
        result = self.conn.chdir(directory)
        self.assertEqual(result, 0)
        self.assertEqual(self.conn.connection.select.call_count, 1)


class DeleteTest(TestCase):
    def setUp(self):
        host, port, ssl, user, password = 'imap.host.test', 143, False, 'user', 'password'
        self.conn = EmailConnectorInterface(host, port, ssl, user, password)
        self.conn.connection = Mock()
        self.conn.connection.store = Mock()

    def test_mark_delete_not_open(self):
        self.conn.connection = None
        self.conn.mark_delete(1)

    def test_do_delete_not_open(self):
        self.conn.connection = None
        self.conn.do_delete()

    def test_mark_delete(self):
        email_id = 5
        self.conn.mark_delete(email_id)
        self.assertEqual(self.conn.connection.store.call_count, 1)
        self.assertEqual(self.conn.connection.store.call_args, call(email_id, '+FLAGS', '\\Deleted'))

    def test_do_delete(self):
        self.conn.do_delete()
        self.assertEqual(self.conn.connection.expunge.call_count, 1)
        self.assertEqual(self.conn.connection.expunge.call_args, call())

    def test_mark_delete_wrong(self):
        email_id = 0
        self.conn.mark_delete(email_id)
        self.assertEqual(self.conn.connection.store.call_count, 0)


class GetEmailsTest(TestCase):
    def setUp(self):
        host, port, ssl, user, password = 'imap.host.test', 143, False, 'user', 'password'
        self.conn = EmailConnectorInterface(host, port, ssl, user, password)
        self.conn.connection = Mock()

    def test_get_emails_not_open(self):
        self.conn.connection = None
        generator = self.conn.get_emails(None)
        self.assertRaises(StopIteration, generator.next)

    def test_get_emails_without_extra(self):
        directory = 'directory'
        self.conn.chdir = Mock()
        self.conn.chdir.return_value = 0

        generator = self.conn.get_emails(directory)
        self.assertRaises(StopIteration, generator.next)

        self.assertEqual(self.conn.chdir.call_count, 1)
        self.assertEqual(self.conn.chdir.call_args, call(directory))

    def test_get_emails_with_just_read(self):
        directory = 'directory'
        ret_val = ''
        self.conn.chdir = Mock()
        self.conn.chdir.return_value = 0
        self.conn.connection.search = Mock()
        self.conn.connection.search.return_value = ('OK', (ret_val, ))

        generator = self.conn.get_emails(directory, just_read=True)
        self.assertRaises(StopIteration, generator.next)

        self.assertEqual(self.conn.chdir.call_count, 1)
        self.assertEqual(self.conn.chdir.call_args, call(directory))
        self.assertEqual(self.conn.connection.search.call_count, 1)
        self.assertEqual(self.conn.connection.search.call_args, call(None, '(SEEN)'))

    def test_get_emails_with_before(self):
        directory = 'directory'
        ret_val = ''
        before = date(2017, 1, 1)
        before_str = '01-Jan-2017'
        self.conn.chdir = Mock()
        self.conn.chdir.return_value = 0
        self.conn.connection.search = Mock()
        self.conn.connection.search.return_value = ('OK', (ret_val, ))

        generator = self.conn.get_emails(directory, before=before)
        self.assertRaises(StopIteration, generator.next)

        self.assertEqual(self.conn.chdir.call_count, 1)
        self.assertEqual(self.conn.chdir.call_args, call(directory))
        self.assertEqual(self.conn.connection.search.call_count, 1)
        self.assertEqual(self.conn.connection.search.call_args, call(None, '(before "{}")'.format(before_str)))

    def test_get_emails_with_before_as_string_on_esES(self):
        directory = 'directory'
        ret_val = ''
        locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
        before_str_es = '1-Ene-2017'
        before_str = '01-Jan-2017'
        self.conn.chdir = Mock()
        self.conn.chdir.return_value = 0
        self.conn.connection.search = Mock()
        self.conn.connection.search.return_value = ('OK', (ret_val, ))

        generator = self.conn.get_emails(directory, before=before_str_es)
        self.assertRaises(StopIteration, generator.next)

        self.assertEqual(self.conn.chdir.call_count, 1)
        self.assertEqual(self.conn.chdir.call_args, call(directory))
        self.assertEqual(self.conn.connection.search.call_count, 1)
        self.assertEqual(self.conn.connection.search.call_args, call(None, '(before "{}")'.format(before_str)))

    def test_get_emails_with_before_as_string(self):
        directory = 'directory'
        ret_val = ''
        before_str = '01-Jan-2017'
        self.conn.chdir = Mock()
        self.conn.chdir.return_value = 0
        self.conn.connection.search = Mock()
        self.conn.connection.search.return_value = ('OK', (ret_val, ))

        generator = self.conn.get_emails(directory, before=before_str)
        self.assertRaises(StopIteration, generator.next)

        self.assertEqual(self.conn.chdir.call_count, 1)
        self.assertEqual(self.conn.chdir.call_args, call(directory))
        self.assertEqual(self.conn.connection.search.call_count, 1)
        self.assertEqual(self.conn.connection.search.call_args, call(None, '(before "{}")'.format(before_str)))

    def test_get_emails_with_wrong_before(self):
        directory = 'directory'
        before_str = 'THIS_IS_NOT_DATE'
        self.conn.chdir = Mock()
        self.conn.chdir.return_value = 0

        generator = self.conn.get_emails(directory, before=before_str)
        self.assertRaises(ValueError, generator.next)

    def test_get_emails_with_before_and_just_read(self):
        directory = 'directory'
        ret_val = ''
        before_str = '01-Jan-2017'
        self.conn.chdir = Mock()
        self.conn.chdir.return_value = 0
        self.conn.connection.search = Mock()
        self.conn.connection.search.return_value = ('OK', (ret_val, ))

        generator = self.conn.get_emails(directory, before=before_str, just_read=True)
        self.assertRaises(StopIteration, generator.next)

        self.assertEqual(self.conn.chdir.call_count, 1)
        self.assertEqual(self.conn.chdir.call_args, call(directory))
        self.assertEqual(self.conn.connection.search.call_count, 1)
        self.assertEqual(self.conn.connection.search.call_args,
                         call(None, '(before "{}")'.format(before_str), '(SEEN)'))

    def test_get_emails_with_response(self):
        directory = 'directory'
        self.conn.chdir = Mock()
        self.conn.chdir.return_value = 1

        generator = self.conn.get_emails(directory)
        email = generator.next()

        self.assertEqual(email.id, 1)
        self.assertEqual(email.connector, self.conn)
        self.assertEqual(email.directory, directory)
        self.assertRaises(StopIteration, generator.next)

    def test_get_emails_with_response_and_query(self):
        directory = 'directory'
        ret_val = '1 10'
        self.conn.chdir = Mock()
        self.conn.chdir.return_value = 0
        self.conn.connection.search = Mock()
        self.conn.connection.search.return_value = ('OK', (ret_val, ))

        generator = self.conn.get_emails(directory, just_read=True)

        email = generator.next()
        self.assertEqual(email.id, '1')
        self.assertEqual(email.connector, self.conn)
        self.assertEqual(email.directory, directory)
        email = generator.next()
        self.assertEqual(email.id, '10')
        self.assertEqual(email.connector, self.conn)
        self.assertEqual(email.directory, directory)

        self.assertEqual(self.conn.chdir.call_count, 1)
        self.assertEqual(self.conn.chdir.call_args, call(directory))
        self.assertEqual(self.conn.connection.search.call_count, 1)
        self.assertEqual(self.conn.connection.search.call_args, call(None, '(SEEN)'))

        self.assertRaises(StopIteration, generator.next)

    def test_get_emails_wrong_dir(self):
        directory = 'not exist'
        self.conn.chdir = Mock()
        self.conn.chdir.return_value = 0

        generator = self.conn.get_emails(directory)
        self.assertRaises(StopIteration, generator.next)

        self.assertEqual(self.conn.chdir.call_count, 1)
        self.assertEqual(self.conn.chdir.call_args, call(directory))
