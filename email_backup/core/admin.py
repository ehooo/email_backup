# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from email_backup.core.models import (
    EmailAccount,
    Email,
    EmailPath
)
from django.contrib import admin
from django.utils.translation import ugettext_lazy as _


def sync_directories(modeladmin, request, queryset):
    for account in queryset.all():
        email_server = account.connector()
        email_server.open()
        for directory in email_server.directories():
            EmailPath.objects.get_or_create(account=account, path=directory)
sync_directories.short_description = _("Sync directories")


def sync_accounts(modeladmin, request, queryset):
    queryset.update(sync=True)
sync_accounts.short_description = _("Mark for sync")


def remove_sync_accounts(modeladmin, request, queryset):
    queryset.update(sync=False)
remove_sync_accounts.short_description = _("Remove sync mark")


class EmailAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'host', 'ssl', 'port', 'sync', 'path')
    search_fields = ('user', 'path', 'host')
    list_filter = ('ssl', 'port', 'sync', 'remove', 'just_read')
    actions = [sync_directories, sync_accounts, remove_sync_accounts]

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


def ignore_paths(modeladmin, request, queryset):
    queryset.update(ignore=True)
ignore_paths.short_description = _("Mark for ignore")


def remove_ignore_paths(modeladmin, request, queryset):
    queryset.update(ignore=False)
remove_ignore_paths.short_description = _("Remove ignore mark")


class EmailPathAdmin(admin.ModelAdmin):
    list_display = ('account', 'path', 'ignore')
    search_fields = ('path', )
    readonly_fields = ('account', 'path')
    list_filter = ('ignore', )
    actions = [ignore_paths, remove_ignore_paths]

    def has_add_permission(self, request):
        return False

admin.site.register(EmailPath, EmailPathAdmin)


class EmailAdmin(admin.ModelAdmin):
    list_display = ('send_by', 'subject', 'attaches', 'date')
    search_fields = ('^send_by', 'subject', 'content')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
admin.site.register(Email, EmailAdmin)
