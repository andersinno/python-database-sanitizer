# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from ..sanitizers.string import sanitize_empty, sanitize_zfill


@pytest.mark.parametrize(
    "input_value,expected_output",
    (
        ("foo", ""),
        ("bar", ""),
        ("", ""),
        ("   ", ""),
        (None, None),
    ),
)
def test_sanitize_empty(input_value, expected_output):
    assert sanitize_empty(input_value) == expected_output


@pytest.mark.parametrize(
    "input_value,expected_output",
    (
        ("foo", "000"),
        ("test test", "000000000"),
        ("", ""),
        (None, None)
    ),
)
def test_sanitize_zfill(input_value, expected_output):
    return sanitize_zfill(input_value) == expected_output
