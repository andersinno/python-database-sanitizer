# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import mock
import pytest

from ..sanitizers.string import sanitize_empty, sanitize_random, sanitize_zfill


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


@mock.patch('random.choice', return_value='x')
def test_sanitize_random(mocked_random_choice):
    assert sanitize_random(None) is None
    assert sanitize_random('') == ''
    assert sanitize_random('a') == 'x'
    assert sanitize_random('hello') == 'xxxxx'
    assert sanitize_random('hello world') == 'xxxxxxxxxxx'
