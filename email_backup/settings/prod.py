from __future__ import absolute_import
from .devel import *

DEBUG = False

try:
    import psycopg2

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': 'email_backup',
            'USER': 'myuser',
            'PASSWORD': 'password',
            'HOST': 'localhost',
            'PORT': '',
        }
    }
except ImportError:
    pass
