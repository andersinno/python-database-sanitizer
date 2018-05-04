# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import io
import pytest

from collections import namedtuple
from six.moves.urllib import parse as urlparse

from ..config import Configuration
from ..dump.postgres import parse_column_names, parse_values, sanitize

try:
    from unittest import mock
except ImportError:
    import mock


MOCK_PG_DUMP_OUTPUT = b"""
--- Fake PostgreSQL database dump

COMMENT ON SCHEMA "public" IS 'standard public schema';

COPY "public"."test" ("id", "created_at", "notes") FROM stdin;
1\t2018-01-01 00:00:00\tTest data 1
2\t2018-01-02 00:00:00\tTest data 2
3\t2018-01-03 00:00:00\tTest data 3
\\.

--- Final line after `COPY` statement
""".strip()


INVALID_MOCK_PG_DUMP_OUTPUT = b"""
--- Fake PostgreSQL database dump

COMMENT ON SCHEMA "public" IS 'standard public schema';

COPY "public"."test" ("id", "created_at", "notes") FROM stdin;
1\t2018-01-01 00:00:00 Test data 1
2\t2018-01-02 00:00:00 Test data 2
3\t2018-01-03 00:00:00 Test data 3
\\.

--- Final line after `COPY` statement
""".strip()


def create_mock_popen(mock_pg_dump_output):
    def mock_popen(cmd_args, stdout):
        mock_pipe_type = namedtuple("mock_pipe", ("stdout",))
        mock_stdout = io.BytesIO(mock_pg_dump_output)
        return mock_pipe_type(stdout=mock_stdout)
    return mock_popen


def test_sanitize():
    url = urlparse.urlparse("postgres://localhost/test")
    config = Configuration()
    config.sanitizers["test.notes"] = lambda value: "Sanitized"

    with mock.patch("subprocess.Popen", side_effect=create_mock_popen(MOCK_PG_DUMP_OUTPUT)):
        dump_output_lines = list(sanitize(url, config))

    assert "--- Fake PostgreSQL database dump" in dump_output_lines
    assert "--- Final line after `COPY` statement" in dump_output_lines
    assert "2\t2018-01-02 00:00:00\tSanitized" in dump_output_lines


def test_sanitizer_invalid_input():
    url = urlparse.urlparse("postgres://localhost/test")

    with mock.patch("subprocess.Popen", side_effect=create_mock_popen(INVALID_MOCK_PG_DUMP_OUTPUT)):
        with pytest.raises(ValueError):
            # Yes, we need the list() function there to eat the yields.
            list(sanitize(url, None))


def test_sanitizer_invalid_scheme():
    url = urlparse.urlparse("http://localhost/test")
    with pytest.raises(ValueError):
        list(sanitize(url, None))


@pytest.mark.parametrize(
    "text,expected_column_names",
    (
        ("\"test\"", ("test",)),
        ("\"test\",\"test\"", ("test", "test")),
        ("\"test\", \"test\"", ("test", "test")),
    )
)
def test_parse_column_names(text, expected_column_names):
    assert parse_column_names(text) == expected_column_names


@pytest.mark.parametrize(
    "text,expected_values",
    (
        ("Test", ("Test",)),
        ("Test\tTest", ("Test", "Test")),
        ("Test\tTest\t", ("Test", "Test", "")),
        ("\\N", (None,)),
    )
)
def test_parse_values(text, expected_values):
    assert parse_values(text) == expected_values
