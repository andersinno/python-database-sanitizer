# -*- coding: utf-8 -*-

from __future__ import absolute_import, unicode_literals

import random
import string

CHARACTERS = string.ascii_letters + string.digits


def sanitize_empty(value):
    """
    Built-in sanitizer which replaces the original value with empty string.
    """
    return None if value is None else ""


def sanitize_zfill(value):
    """
    Built-in sanitizer which replaces the original value with zeros.
    """
    return None if value is None else "".zfill(len(value))


def sanitize_random(value):
    """
    Random string of same length as the given value.
    """
    if not value:
        return value
    return ''.join(random.choice(CHARACTERS) for _ in range(len(value)))
