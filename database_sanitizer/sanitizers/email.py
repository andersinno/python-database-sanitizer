# -*- coding: utf-8 -*-

from __future__ import unicode_literals


def sanitize_example(value):
    """
    Built-in sanitizer which replaces e-mail address with
    "example@example.org".
    """
    if value is None:
        return None
    elif not value:
        return ""
    else:
        return "example@example.org"
