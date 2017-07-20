# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from django.core.validators import BaseValidator, validate_ipv46_address
import socket
import six
import re


class PathValidator(BaseValidator):
    message = _('%(show_value)s is not valid path')
    code = 'invalid_path'
    RE_PATH = re.compile('([\w/ .-]+)')

    def __init__(self, message=None):
        BaseValidator.__init__(self, self.RE_PATH, message=message)

    def clean(self, x):
        if isinstance(x, six.string_types):
            valid_path = x.replace('//', '/')
            str_len = len(x)
            while str_len != len(valid_path):
                valid_path = valid_path.replace('//', '/')
                str_len = len(valid_path)
            self.limit_value = valid_path
        return x

    def compare(self, a, b):
        return a != b or not self.RE_PATH.match(a)


def port_validator(value):
    if not (0 < value < 65535):
        message = _('%(show_value)s is not valid port')
        raise ValidationError(message, code='invalid_port', params={'show_value': value})


def bind_port_validator(value):
    port_validator(value)
    if value > 49152:
        message = _('%(show_value)s is not valid bind port')
        raise ValidationError(message, code='invalid_port', params={'show_value': value})


def host_validator(value):
    if not isinstance(value, six.string_types):
        value = "{}".format(value)
    try:
        validate_ipv46_address(value)
    except ValidationError:
        try:
            socket.gethostbyname(value)
        except socket.error:
            message = _('%(show_value)s is not valid host name, cannot be resolved')
            raise ValidationError(message, code='invalid_host', params={'show_value': value})
