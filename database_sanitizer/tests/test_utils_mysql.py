# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest
from six.moves.urllib import parse as urlparse

from ..utils.mysql import (
    decode_mysql_literal,
    decode_mysql_string_literal,
    get_mysqldump_args_and_env_from_url,
    unescape_single_character,
)


@pytest.mark.parametrize(
    "url",
    (
        "mysql://test:test@localhost/test",
        "mysql://localhost:1234/test",
        "mysql://localhost",
    ),
)
def test_get_mysqldump_args_and_env_from_url(url):
    parsed_url = urlparse.urlparse(url)

    if not parsed_url.path:
        with pytest.raises(ValueError):
            get_mysqldump_args_and_env_from_url(url=parsed_url)
        return

    args, env = get_mysqldump_args_and_env_from_url(url=parsed_url)

    assert isinstance(args, list)
    assert isinstance(env, dict)

    assert len(args) > 0
    assert "--complete-insert" in args
    assert "--extended-insert" in args
    assert "--net_buffer_length=10240" in args
    assert args[-1] == parsed_url.path[1:]

    if parsed_url.username:
        index = args.index("-u")
        assert args[index + 1] == parsed_url.username

    if parsed_url.password:
        assert env["MYSQL_PWD"] == parsed_url.password


@pytest.mark.parametrize(
    "text,expected_value",
    (
        ("NULL", None),
        ("TRUE", True),
        ("FALSE", False),
        ("12", 12),
        ("12.5", 12.5),
        ("'test'", "test"),
    ),
)
def test_decode_mysql_literal(text, expected_value):
    assert decode_mysql_literal(text) == expected_value


def test_decode_mysql_literal_invalid_input():
    with pytest.raises(ValueError):
        decode_mysql_literal("ERROR")


@pytest.mark.parametrize(
    "text,expected_output",
    (
        ("'test'", "test"),
        ("'test\\ntest'", "test\ntest"),
        ("'\\0'", "\000"),
        ("'foo", None),
        ("foo'", None),
        ("foo", None),
    ),
)
def test_decode_mysql_string_literal(text, expected_output):
    if expected_output is None:
        with pytest.raises(AssertionError):
            decode_mysql_string_literal(text)
    else:
        assert decode_mysql_string_literal(text) == expected_output


@pytest.mark.parametrize(
    "text,expected_output",
    (
        ("\\\\", "\\"),
        ("\\n", "\n"),
        ("\\r", "\r"),
        ("\\0", "\000"),
        ("\\Z", "\032"),
        ("\\'", "'"),
        ('\\"', '"'),
    ),
)
def test_unescape_single_character(text, expected_output):
    class MockRegexpMatch(object):

        def __init__(self, text):
            self.text = text

        def group(self, index):
            assert index == 0
            return self.text

    assert unescape_single_character(MockRegexpMatch(text)) == expected_output
