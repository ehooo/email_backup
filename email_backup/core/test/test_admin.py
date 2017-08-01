# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from unittest import TestCase
from mock import Mock, patch, call
from email_backup.core.admin import *


class AdminActionsTest(TestCase):
    @patch('email_backup.core.admin.EmailPath.objects')
    def test_sync_directories(self, objects_mock):
        account = Mock()
        directory = 'directory'
        modeladmin, request, queryset = Mock(), Mock(), Mock()
        queryset.all.return_value = [account]
        open_mock = Mock()
        open_mock.directories.return_value = [directory]
        account.connector.return_value = open_mock

        sync_directories(modeladmin, request, queryset)

        self.assertEqual(queryset.all.call_count, 1)
        self.assertEqual(queryset.all.call_args, call())
        self.assertEqual(open_mock.open.call_count, 1)
        self.assertEqual(open_mock.open.call_args, call())
        self.assertEqual(open_mock.directories.call_count, 1)
        self.assertEqual(open_mock.directories.call_args, call())

        self.assertEqual(objects_mock.get_or_create.call_count, 1)
        self.assertEqual(objects_mock.get_or_create.call_args, call(account=account, path=directory))

    def test_sync_accounts(self):
        modeladmin, request, queryset = Mock(), Mock(), Mock()
        sync_accounts(modeladmin, request, queryset)

        self.assertEqual(queryset.update.call_count, 1)
        self.assertEqual(queryset.update.call_args, call(sync=True))

    def test_remove_sync_accounts(self):
        modeladmin, request, queryset = Mock(), Mock(), Mock()
        remove_sync_accounts(modeladmin, request, queryset)

        self.assertEqual(queryset.update.call_count, 1)
        self.assertEqual(queryset.update.call_args, call(sync=False))

    def test_ignore_paths(self):
        modeladmin, request, queryset = Mock(), Mock(), Mock()
        ignore_paths(modeladmin, request, queryset)

        self.assertEqual(queryset.update.call_count, 1)
        self.assertEqual(queryset.update.call_args, call(ignore=True))

    def test_remove_ignore_paths(self):
        modeladmin, request, queryset = Mock(), Mock(), Mock()
        remove_ignore_paths(modeladmin, request, queryset)

        self.assertEqual(queryset.update.call_count, 1)
        self.assertEqual(queryset.update.call_args, call(ignore=False))


class EmailAdminTest(TestCase):
    def test_has_add_permission(self):
        page = EmailAdmin(Email, None)
        self.assertFalse(page.has_add_permission(None))

    def test_has_change_permission(self):
        page = EmailAdmin(Email, None)
        self.assertFalse(page.has_change_permission(None))


class EmailPathAdminTest(TestCase):
    def test_has_add_permission(self):
        page = EmailPathAdmin(EmailPath, None)
        self.assertFalse(page.has_add_permission(None))
