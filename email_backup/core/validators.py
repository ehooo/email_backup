# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

from django.core.validators import BaseValidator, validate_ipv46_address
import socket
import six


class ChoicesValidator(BaseValidator):
    message = _('%(show_value)s is not on the list %(limit_value)s')
    code = 'invalid_choices'

    def __init__(self, limit_value, message=None):
        self.limit_value = dict(limit_value)
        super(ChoicesValidator, self).__init__(limit_value, message=message)

    def clean(self, x):
        for key, val in self.limit_value:
            if key == x or val == x:
                return key

    def compare(self, a, b):
        return a in b


def port_validator(value):
    if not (0 < value < 65535):
        message = _('%(show_value)s is not valid port')
        raise ValidationError(message, code='invalid_port', params={'show_value': value})


def bind_port_validator(value):
    if not (0 < value < 49152):
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
