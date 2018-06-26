# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from ..utils.postgres import (
    DECODE_MAP,
    POSTGRES_COPY_NULL_VALUE,
    decode_copy_value,
    encode_copy_value,
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


def test_decode_map_contents():
    assert DECODE_MAP['\\b'] == '\b'
    assert DECODE_MAP['\\n'] == '\n'
    assert DECODE_MAP['\\t'] == '\t'
    assert DECODE_MAP['\\\\'] == '\\'
    assert DECODE_MAP['\\0'] == '\0'
    assert DECODE_MAP['\\74'] == '\74'
    assert DECODE_MAP['\\x0'] == '\0'
    assert DECODE_MAP['\\xa'] == '\x0a'
    assert DECODE_MAP['\\xA'] == '\x0a'
    assert DECODE_MAP['\\x00'] == '\0'
    assert DECODE_MAP['\\xa3'] == '\xa3'
    assert DECODE_MAP['\\xA3'] == '\xa3'
    assert DECODE_MAP['\\xAb'] == '\xab'
    assert DECODE_MAP['\\xaB'] == '\xab'
    assert DECODE_MAP['\\xff'] == '\xff'

    assert '\\' not in DECODE_MAP,  "Unterminated escape is not mapped"
    assert '\\z' not in DECODE_MAP,  "Invalid escape sequences are not mapped"

    assert len(DECODE_MAP) == 1097
