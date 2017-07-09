# -*- coding: utf-8 -*-
# Generated by Django 1.11.3 on 2017-07-09 19:40
from __future__ import unicode_literals

from django.db import migrations, models
import email_backup.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='email',
            name='message_id',
            field=models.CharField(default='message_id@localhost', max_length=1024),
        ),
        migrations.AlterField(
            model_name='emailaccount',
            name='port',
            field=models.IntegerField(default=993, validators=[email_backup.core.validators.bind_port_validator]),
        ),
        migrations.AlterField(
            model_name='emailaccount',
            name='protocol',
            field=models.IntegerField(choices=[(0, 'POP3'), (1, 'IMAP4')], default=1, validators=[email_backup.core.validators.ChoicesValidator(((0, 'POP3'), (1, 'IMAP4')))]),
        ),
        migrations.AlterUniqueTogether(
            name='email',
            unique_together=set([('account', 'message_id')]),
        ),
    ]
