# -*- coding: utf-8 -*-

from __future__ import unicode_literals


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
