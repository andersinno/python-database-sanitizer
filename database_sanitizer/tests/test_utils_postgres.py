# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from ..utils.postgres import (
    decode_copy_value,
    encode_copy_value,
    POSTGRES_COPY_NULL_VALUE,
)


@pytest.mark.parametrize(
    "input_value,expected_value",
    (
        ("", ""),
        (POSTGRES_COPY_NULL_VALUE, None),
        ("Test", "Test"),
        ("\\\\", "\\"),
        ("\\b", "\b"),
        ("\\f", "\f"),
        ("\\n", "\n"),
        ("\\r", "\r"),
        ("\\t", "\t"),
        ("\\v", "\v"),
        ("\\xff", "\xff"),
        ("\\123", "\123"),
        ("Test\\r\\nTest", "Test\r\nTest"),
    )
)
def test_decode_copy_value(input_value, expected_value):
    assert decode_copy_value(input_value) == expected_value


@pytest.mark.parametrize(
    "input_value,expected_value",
    (
        ("", ""),
        (None, POSTGRES_COPY_NULL_VALUE),
        ("Test", "Test"),
        ("\\", "\\\\"),
        ("\b", "\\b"),
        ("\f", "\\f"),
        ("\n", "\\n"),
        ("\r", "\\r"),
        ("\t", "\\t"),
        ("\v", "\\v"),
        ("\xff", "\xff"),
        ("\123", "\123"),
        ("Test\r\nTest", "Test\\r\\nTest"),
    )
)
def test_encode_copy_value(input_value, expected_value):
    assert encode_copy_value(input_value) == expected_value


def test_invalid_escape_sequence():
    with pytest.raises(ValueError):
        decode_copy_value("\\")
    with pytest.raises(ValueError):
        decode_copy_value("\\X")
