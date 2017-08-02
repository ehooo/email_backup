# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from unittest import TestCase
from mock import Mock, patch, call
from email_backup.core.tasks import *


class SyncAccountTest(TestCase):
    def test_sync_account_no_account(self):
        self.assertRaises(AssertionError, sync_account, Mock())

    def test_sync_account_no_sync(self):
        account = Mock(spec=EmailAccount)
        account.sync = False
        sync_account(account)
        self.assertEqual(account.connector.call_count, 0)

    def test_sync_account_remove_simple(self):
        account = Mock(spec=EmailAccount)
        account.sync = True
        account.remove = True

        email_server_mock = Mock()
        email_server_mock.directories.return_value = []
        account.connector.return_value = email_server_mock
        sync_account(account)
        self.assertEqual(account.connector.call_count, 1)
        self.assertEqual(account.connector.call_args, call())
        self.assertEqual(email_server_mock.directories.call_count, 1)
        self.assertEqual(email_server_mock.directories.call_args, call())
        self.assertEqual(email_server_mock.do_delete.call_count, 1)
        self.assertEqual(email_server_mock.do_delete.call_args, call())

    @patch('email_backup.core.tasks.EmailPath.objects')
    def test_sync_account_ignore(self, objects_mock):
        account = Mock(spec=EmailAccount)
        account.sync = True
        account.remove = False
        directory = 'directory'

        email_server_mock = Mock()
        email_server_mock.directories.return_value = [directory]
        account.connector.return_value = email_server_mock
        path_mock = Mock()
        path_mock.ignore = True
        objects_mock.get_or_create.return_value = path_mock, False

        sync_account(account)

        self.assertEqual(account.connector.call_count, 1)
        self.assertEqual(account.connector.call_args, call())
        self.assertEqual(email_server_mock.directories.call_count, 1)
        self.assertEqual(email_server_mock.directories.call_args, call())
        self.assertEqual(objects_mock.get_or_create.call_count, 1)
        self.assertEqual(objects_mock.get_or_create.call_args,
                         call(account=account, path=directory))
        self.assertEqual(email_server_mock.do_delete.call_count, 0)
        self.assertEqual(email_server_mock.get_emails.call_count, 0)

    @patch('email_backup.core.tasks.EmailPath.objects')
    def test_sync_account_new_path(self, objects_mock):
        account = Mock(spec=EmailAccount)
        account.sync = True
        account.remove = False
        directory = 'directory'

        email_server_mock = Mock()
        email_server_mock.directories.return_value = [directory]
        account.connector.return_value = email_server_mock
        path_mock = Mock()
        path_mock.ignore = False
        objects_mock.get_or_create.return_value = path_mock, True

        sync_account(account)

        self.assertEqual(account.connector.call_count, 1)
        self.assertEqual(account.connector.call_args, call())
        self.assertEqual(email_server_mock.directories.call_count, 1)
        self.assertEqual(email_server_mock.directories.call_args, call())
        self.assertEqual(objects_mock.get_or_create.call_count, 1)
        self.assertEqual(objects_mock.get_or_create.call_args,
                         call(account=account, path=directory))
        self.assertEqual(email_server_mock.do_delete.call_count, 0)
        self.assertEqual(email_server_mock.get_emails.call_count, 0)

    @patch('email_backup.core.tasks.Email.objects')
    @patch('email_backup.core.tasks.EmailPath.objects')
    def test_sync_account_remove(self, objects_mock, email_objects_mock):
        account = Mock(spec=EmailAccount)
        account.sync = True
        account.remove = True
        account.weeks_before = 1
        before = datetime.date.today() - datetime.timedelta(weeks=account.weeks_before)
        directory = 'directory'

        email_server_mock = Mock()
        email_server_mock.directories.return_value = [directory]
        account.connector.return_value = email_server_mock
        email_mock = Mock()
        email_objects_mock.get_or_create_from.return_value = email_mock, True
        path_mock = Mock()
        path_mock.ignore = False
        objects_mock.get_or_create.return_value = path_mock, False
        email_raw = Mock()
        email_server_mock.get_emails.return_value = [email_raw]

        sync_account(account)

        self.assertEqual(account.connector.call_count, 1)
        self.assertEqual(account.connector.call_args, call())
        self.assertEqual(email_server_mock.directories.call_count, 1)
        self.assertEqual(email_server_mock.directories.call_args, call())
        self.assertEqual(objects_mock.get_or_create.call_count, 1)
        self.assertEqual(objects_mock.get_or_create.call_args,
                         call(account=account, path=directory))
        self.assertEqual(email_server_mock.get_emails.call_count, 1)
        self.assertEqual(email_server_mock.get_emails.call_args,
                         call(directory=directory, before=before, just_read=account.just_read))
        self.assertEqual(email_objects_mock.get_or_create_from.call_count, 1)
        self.assertEqual(email_objects_mock.get_or_create_from.call_args,
                         call(email_raw, account=account))
        self.assertEqual(email_mock.paths.add.call_count, 1)
        self.assertEqual(email_mock.paths.add.call_args, call(path_mock))
        self.assertEqual(email_server_mock.mark_delete.call_count, 1)
        self.assertEqual(email_server_mock.mark_delete.call_args, call(email_mock.server_id))
        self.assertEqual(email_server_mock.do_delete.call_count, 1)
        self.assertEqual(email_server_mock.do_delete.call_args, call())

    @patch('email_backup.core.tasks.Email.objects')
    @patch('email_backup.core.tasks.EmailPath.objects')
    def test_sync_account_no_remove(self, objects_mock, email_objects_mock):
        account = Mock(spec=EmailAccount)
        account.sync = True
        account.remove = False
        account.weeks_before = 1
        before = datetime.date.today() - datetime.timedelta(weeks=account.weeks_before)
        directory = 'directory'

        email_server_mock = Mock()
        email_server_mock.directories.return_value = [directory]
        account.connector.return_value = email_server_mock
        email_mock = Mock()
        email_objects_mock.get_or_create_from.return_value = email_mock, True
        path_mock = Mock()
        path_mock.ignore = False
        objects_mock.get_or_create.return_value = path_mock, False
        email_raw = Mock()
        email_server_mock.get_emails.return_value = [email_raw]

        sync_account(account)

        self.assertEqual(account.connector.call_count, 1)
        self.assertEqual(account.connector.call_args, call())
        self.assertEqual(email_server_mock.directories.call_count, 1)
        self.assertEqual(email_server_mock.directories.call_args, call())
        self.assertEqual(objects_mock.get_or_create.call_count, 1)
        self.assertEqual(objects_mock.get_or_create.call_args,
                         call(account=account, path=directory))
        self.assertEqual(email_server_mock.get_emails.call_count, 1)
        self.assertEqual(email_server_mock.get_emails.call_args,
                         call(directory=directory, before=before, just_read=account.just_read))
        self.assertEqual(email_objects_mock.get_or_create_from.call_count, 1)
        self.assertEqual(email_objects_mock.get_or_create_from.call_args,
                         call(email_raw, account=account))
        self.assertEqual(email_mock.paths.add.call_count, 1)
        self.assertEqual(email_mock.paths.add.call_args, call(path_mock))
        self.assertEqual(email_server_mock.mark_delete.call_count, 0)
        self.assertEqual(email_server_mock.do_delete.call_count, 0)
