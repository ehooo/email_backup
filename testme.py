from email_backup.core.connector import *
from datetime import datetime


class EmailAccount(object):
    def __init__(self, user, password, host, path, protocol, ssl, port):
        self.user = user
        self.password = password
        self.host = host
        self.path = path
        self.protocol = protocol
        self.ssl = ssl
        self.port = port


account = EmailAccount(
    user='web.ehooo@gmail.com',
    password='vtsdhkrlecmwkjho',
    host='imap.gmail.com',
    path='/',
    protocol=IMAP4,
    ssl=True,
    port=993
)

conn = EmailConnectorInterface(account.protocol, account.host, account.port, account.ssl, account.user, account.password)
conn.open()
conn.login()
dirs = conn.directories()
conn.connection.select(dirs[-1])
ok, mgs = conn.connection.search(None, 'ALL')
ok, ((info, msg), mark) = conn.connection.fetch(1, '(RFC822)')
before = datetime(2015, 1, 1)
ok, mgs = conn.connection.search(None, '(before "{}")'.format(before.strftime('%d-%b-%Y')))

conn.close()
