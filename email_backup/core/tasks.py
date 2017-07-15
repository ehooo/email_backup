from email_backup.core.connector import EmailConnectorInterface
from email_backup.core.models import Sync, EmailAccount, Email
import datetime


def sync_account(account):
    assert isinstance(account, EmailAccount)
    sync_config = Sync.objects.get(account=account)
    email_server = EmailConnectorInterface(account.host, account.port, account.ssl,
                                           account.user, account.password)
    for directory in email_server.directories():
        before = datetime.date.today() - datetime.timedelta(weeks=sync_config.weeks_before)
        emails = email_server.get_emails(directory=directory, before=before,
                                         just_read=sync_config.just_read)
        for email in emails:
            Email.objects.get_or_create_from(email, account=account)
            if sync_config.remove:
                email_server.mark_delete(email.server_id)  # email.delete()
        if sync_config.remove:
            email_server.do_delete()
