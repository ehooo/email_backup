# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from django.core.validators import validate_ipv46_address
import socket
import six
import re


RE_PATH = re.compile('([\w/\[\] .-]+)$', re.UNICODE)


def path_validator(value):
    if not isinstance(value, six.string_types):
        message = _('%(show_value)s is not valid path')
        raise ValidationError(message, code='invalid_path', params={'show_value': value})
    if value.endswith('/'):
        message = _('%(show_value)s is not valid path')
        raise ValidationError(message, code='invalid_path', params={'show_value': value})
    valid_path = value.replace('//', '/')
    str_len = len(value)
    if str_len != len(valid_path):
        message = _('%(show_value)s is not valid path')
        raise ValidationError(message, code='invalid_path', params={'show_value': value})
    if not RE_PATH.match(value):
        message = _('%(show_value)s is not valid path')
        raise ValidationError(message, code='invalid_path', params={'show_value': value})


def port_validator(value):
    if not (0 < value < 65535) or not isinstance(value, int):
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
