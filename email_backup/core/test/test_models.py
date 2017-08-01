# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from unittest import TestCase
from mock import Mock, patch, call
from email_backup.core.models import *
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


class EmailAccountTest(TestCase):
    def setUp(self):
        self.model = EmailAccount(host='host', port=993, ssl=True, user='user', password='password')

    @patch('email_backup.core.models.EmailConnectorInterface')
    def test_connector(self, interface_mock):
        self.model.connector()
        self.assertEqual(interface_mock.call_count, 1)
        self.assertEqual(interface_mock.call_args, call('host', 993, True, 'user', 'password'))

    def test_string(self):
        self.assertEqual(str(self.model), "user at [host]")
        self.assertEqual(unicode(self.model), u"user at [host]")


class EmailPathTest(TestCase):
    def setUp(self):
        self.model = EmailPath(path='path')

    def test_string(self):
        self.assertEqual(str(self.model), "path")
        self.assertEqual(unicode(self.model), u"path")


class EmailManagerTest(TestCase):
    def setUp(self):
        self.email = Mock(spec=TmpEmail)
        self.email.get.return_value = 'message_id'

    def test_filter_from(self):
        Email.objects.filter_from(self.email)
        self.assertEqual(self.email.load.call_count, 1)
        self.assertEqual(self.email.load.call_args, call(True))
        self.assertEqual(self.email.get.call_count, 1)
        self.assertEqual(self.email.get.call_args, call('Message-Id'))

    def test_create_from_without_account(self):
        self.assertRaises(AssertionError, Email.objects.create_from, self.email)

    @patch('email_backup.core.models.StringIO.StringIO')
    @patch('email_backup.core.models.File')
    @patch('email_backup.core.models.default_storage')
    @patch('email_backup.core.models.EmailManager.create')
    def test_create_from(self, create_mock, default_storage_mock, file_mock, stringIO_mock):
        email_file = os.path.join(BASE_DIR, 'files', 'multi_email.eml')
        connector = Mock(spec=EmailConnectorInterface)
        connector.read.return_value = open(email_file).read()
        default_storage_mock.path.return_value = '/'
        self.email = TmpEmail(connector, 1, 'test')
        account = Mock(spec=EmailAccount)
        account.path = '.'

        kwargs = {}
        kwargs['message_id'] = '<ID_multi@email.test>'
        kwargs['send_by'] = 'from@email.test'
        kwargs['date'] = datetime(2017, 7, 31, 14, 18, 46)
        kwargs['subject'] = 'Test subject'
        kwargs['content'] = '*Test Body*\r\n\r\n-- \r\nSignature with link <http://domain.test>\r\n'
        kwargs['attaches'] = 2
        kwargs['raw'] = file_mock.return_value

        Email.objects.create_from(self.email, account=account)

        sha = '74967d805810b1a6eddf4b7cc23d0ebe0a755ab20471fc4d4578d94eda5d612e83d3b45765a76643d86121fbba6d71fdde1d' \
              '90e8c3a83cae1aac2645e5a9a677'
        base_path = default_storage_mock.path.return_value
        filename = '{}/{}/{}.eml'.format(base_path, account.path, sha)
        filename = os.path.abspath(filename)

        self.assertEqual(default_storage_mock.path.call_count, 1)
        self.assertEqual(default_storage_mock.path.call_args, call('.'))
        self.assertEqual(stringIO_mock.call_count, 1)
        self.assertEqual(stringIO_mock.call_args, call(unicode(self.email)))
        self.assertEqual(file_mock.call_count, 1)
        self.assertEqual(file_mock.call_args, call(stringIO_mock.return_value, name=filename))
        self.assertEqual(create_mock.call_count, 1)
        self.assertEqual(create_mock.call_args, call(account=account, **kwargs))

    @patch('email_backup.core.models.StringIO.StringIO')
    @patch('email_backup.core.models.File')
    @patch('email_backup.core.models.default_storage')
    @patch('email_backup.core.models.EmailManager.create')
    def test_create_from_no_storage(self, create_mock, default_storage_mock, file_mock, stringIO_mock):
        email_file = os.path.join(BASE_DIR, 'files', 'multi_email.eml')
        connector = Mock(spec=EmailConnectorInterface)
        connector.read.return_value = open(email_file).read()
        default_storage_mock.path.side_effect = NotImplementedError
        self.email = TmpEmail(connector, 1, 'test')
        account = Mock(spec=EmailAccount)
        account.path = '.'

        kwargs = {}
        kwargs['message_id'] = '<ID_multi@email.test>'
        kwargs['send_by'] = 'from@email.test'
        kwargs['date'] = datetime(2017, 7, 31, 14, 18, 46)
        kwargs['subject'] = 'Test subject'
        kwargs['content'] = '*Test Body*\r\n\r\n-- \r\nSignature with link <http://domain.test>\r\n'
        kwargs['attaches'] = 2
        kwargs['raw'] = file_mock.return_value

        Email.objects.create_from(self.email, account=account)

        sha = '74967d805810b1a6eddf4b7cc23d0ebe0a755ab20471fc4d4578d94eda5d612e83d3b45765a76643d86121fbba6d71fdde1d' \
              '90e8c3a83cae1aac2645e5a9a677'
        base_path = '.'
        filename = '{}/{}/{}.eml'.format(base_path, account.path, sha)
        filename = os.path.abspath(filename)

        self.assertEqual(default_storage_mock.path.call_count, 1)
        self.assertEqual(default_storage_mock.path.call_args, call('.'))
        self.assertEqual(stringIO_mock.call_count, 1)
        self.assertEqual(stringIO_mock.call_args, call(unicode(self.email)))
        self.assertEqual(file_mock.call_count, 1)
        self.assertEqual(file_mock.call_args, call(stringIO_mock.return_value, name=filename))
        self.assertEqual(create_mock.call_count, 1)
        self.assertEqual(create_mock.call_args, call(account=account, **kwargs))

    @patch('email_backup.core.models.EmailManager.create_from')
    def test_get_or_create_from_new(self, create_from_mock):
        account = EmailAccount()
        ret = Email.objects.get_or_create_from(self.email, account=account)

        self.assertEqual(ret, (create_from_mock.return_value, True))
        self.assertEqual(self.email.load.call_count, 1)
        self.assertEqual(self.email.load.call_args, call(True))
        self.assertEqual(create_from_mock.call_count, 1)
        self.assertEqual(create_from_mock.call_args, call(self.email, account=account))

    @patch('email_backup.core.models.EmailManager.get_queryset')
    def test_get_or_create_from_exist(self, get_queryset_mock):
        account = EmailAccount()
        exists_mock = Mock()
        exists_mock.exists.return_value = True
        filter_mock = Mock()
        filter_mock.filter.return_value = exists_mock
        get_queryset_mock.return_value = filter_mock

        ret = Email.objects.get_or_create_from(self.email, account=account)

        self.assertEqual(ret, (exists_mock.get.return_value, False))
        self.assertEqual(self.email.load.call_count, 1)
        self.assertEqual(self.email.load.call_args, call(True))
        self.assertEqual(filter_mock.filter.call_count, 1)
        self.assertEqual(filter_mock.filter.call_args, call(message_id='message_id', account=account))
        self.assertEqual(exists_mock.exists.call_count, 1)
        self.assertEqual(exists_mock.exists.call_args, call())
        self.assertEqual(exists_mock.get.call_count, 1)
        self.assertEqual(exists_mock.get.call_args, call())
