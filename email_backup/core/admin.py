# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from email_backup.core.models import (
    EmailAccount,
    Email
)
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _


class EmailAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'host', 'ssl', 'port', 'sync')
    search_fields = ('user', 'path', 'host')
    list_filter = ('ssl', 'port', 'sync', 'remove', 'just_read')

    fieldsets = (
        (None, {
            'fields': ('user', 'password', 'host')
        }),
        (_('Advanced options'), {
            'classes': ('collapse',),
            'fields': ('path', 'ssl', 'port'),
        }),
        (_('Sync options'), {
            'classes': ('collapse',),
            'fields': ('sync', 'weeks_before', 'remove', 'just_read'),
        }),
    )
admin.site.register(EmailAccount, EmailAccountAdmin)


class EmailAdmin(admin.ModelAdmin):
    list_display = ('send_by', 'subject', 'attaches', 'date')
    search_fields = ('^send_by', 'subject', 'content')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
admin.site.register(Email, EmailAdmin)
