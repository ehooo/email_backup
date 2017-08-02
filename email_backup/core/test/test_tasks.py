# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from unittest import TestCase
from mock import Mock, patch, call
from email_backup.core.tasks import *


class SyncAllAccountTest(TestCase):
    @patch('email_backup.core.tasks.EmailAccount.objects.filter')
    def test_sync_all_account_empty(self, filter_mock):
        filter_mock.return_value = []
        sync_all_account()
        self.assertEqual(filter_mock.call_count, 1)
        self.assertEqual(filter_mock.call_args, call(sync=True))

    @patch('email_backup.core.tasks.sync_account')
    @patch('email_backup.core.tasks.EmailAccount.objects.filter')
    def test_sync_all_account(self, filter_mock, sync_account_mock):
        account = Mock()
        account.pk = 1
        filter_mock.return_value = [account]
        sync_all_account()
        self.assertEqual(filter_mock.call_count, 1)
        self.assertEqual(filter_mock.call_args, call(sync=True))
        self.assertEqual(sync_account_mock.apply_async.call_count, 1)
        self.assertEqual(sync_account_mock.apply_async.call_args, call(account.pk))


class SyncAccountTest(TestCase):
    def test_sync_account_no_account(self):
        self.assertRaises(EmailAccount.DoesNotExist, sync_account, 1)

    @patch('email_backup.core.tasks.EmailAccount.objects.get')
    def test_sync_account_no_sync(self, get_account_objects_mock):
        account = Mock(spec=EmailAccount)
        account.sync = False
        get_account_objects_mock.return_value = account
        sync_account(1)
        self.assertEqual(account.connector.call_count, 0)

    @patch('email_backup.core.tasks.EmailAccount.objects.get')
    def test_sync_account_remove_simple(self, get_account_objects_mock):
        account = Mock(spec=EmailAccount)
        account.sync = True
        account.remove = True
        email_server_mock = Mock()
        email_server_mock.directories.return_value = []
        account.connector.return_value = email_server_mock

        get_account_objects_mock.return_value = account
        sync_account(1)

        self.assertEqual(account.connector.call_count, 1)
        self.assertEqual(account.connector.call_args, call())
        self.assertEqual(email_server_mock.directories.call_count, 1)
        self.assertEqual(email_server_mock.directories.call_args, call())
        self.assertEqual(email_server_mock.do_delete.call_count, 1)
        self.assertEqual(email_server_mock.do_delete.call_args, call())

    @patch('email_backup.core.tasks.EmailPath.objects')
    @patch('email_backup.core.tasks.EmailAccount.objects.get')
    def test_sync_account_ignore(self, get_account_objects_mock, objects_mock):
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


        get_account_objects_mock.return_value = account
        sync_account(1)

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
    @patch('email_backup.core.tasks.EmailAccount.objects.get')
    def test_sync_account_new_path(self, get_account_objects_mock, objects_mock):
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

        get_account_objects_mock.return_value = account
        sync_account(1)

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
    @patch('email_backup.core.tasks.EmailAccount.objects.get')
    def test_sync_account_remove(self, get_account_objects_mock, objects_mock, email_objects_mock):
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

        get_account_objects_mock.return_value = account
        sync_account(1)

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
    @patch('email_backup.core.tasks.EmailAccount.objects.get')
    def test_sync_account_no_remove(self, get_account_objects_mock, objects_mock, email_objects_mock):
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

        get_account_objects_mock.return_value = account
        sync_account(1)

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
