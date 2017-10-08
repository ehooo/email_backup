# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import datetime

from email_backup.celery import app
from email_backup.core.models import EmailAccount, Email, EmailPath


@app.task
def sync_all_account():
    for account in EmailAccount.objects.filter(sync=True):
        sync_account.apply_async(account.pk)


@app.task
def sync_account(account_pk):
    account = EmailAccount.objects.get(pk=account_pk)
    if not account.sync:
        return
    email_server = account.connector()
    for directory in email_server.directories():
        path, created = EmailPath.objects.get_or_create(account=account, path=directory)
        if path.ignore or created:
            continue

        before = datetime.date.today() - datetime.timedelta(weeks=account.weeks_before)
        emails = email_server.get_emails(directory=directory, before=before,
                                         just_read=account.just_read)
        for email in emails:
            email, created = Email.objects.get_or_create_from(email, account=account)
            email.paths.add(path)
            if account.remove:
                email_server.mark_delete(email.server_id)  # email.delete()
    if account.remove:
        email_server.do_delete()
