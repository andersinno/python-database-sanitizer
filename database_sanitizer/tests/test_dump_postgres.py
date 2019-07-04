# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import io
from collections import namedtuple

import mock
import pytest
from six.moves.urllib import parse as urlparse

from ..config import Configuration
from ..dump import postgres as dump_postgres
from ..dump.postgres import parse_column_names, parse_values, sanitize
from ..utils.postgres import decode_copy_value

MOCK_PG_DUMP_OUTPUT = b"""
--- Fake PostgreSQL database dump

COMMENT ON SCHEMA "public" IS 'standard public schema';

CREATE TABLE "public"."test" (
"id" integer NOT NULL,
"created_at" timestamp with time zone NOT NULL,
"notes" character varying(255) NOT NULL
);

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


def test_skip_table_rows():
    url = urlparse.urlparse("postgres://localhost/test")
    config = Configuration()
    config.skip_rows_for_tables.append('test')

    with mock.patch("subprocess.Popen",
                    side_effect=create_mock_popen(MOCK_PG_DUMP_OUTPUT)):
        output = list(sanitize(url, config))

    assert output == [
        '--- Fake PostgreSQL database dump',
        '',
        'COMMENT ON SCHEMA "public" IS \'standard public schema\';',
        '',
        'CREATE TABLE "public"."test" (',
        '"id" integer NOT NULL,',
        '"created_at" timestamp with time zone NOT NULL,',
        '"notes" character varying(255) NOT NULL',
        ');',
        '',
        '',
        '--- Final line after `COPY` statement'
    ]


def test_sanitizer_invalid_input():
    url = urlparse.urlparse("postgres://localhost/test")

    config = Configuration()
    config.sanitizers["test.notes"] = lambda value: "Sanitized"

    with mock.patch("subprocess.Popen", side_effect=create_mock_popen(INVALID_MOCK_PG_DUMP_OUTPUT)):
        with pytest.raises(ValueError):
            # Yes, we need the list() function there to eat the yields.
            list(sanitize(url, config))


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


@pytest.mark.parametrize('config_type', [
    'no-config', 'empty-config', 'single-column-config'])
@pytest.mark.parametrize('data_label', ['ok', 'invalid'])
def test_optimizations(config_type, data_label):
    if config_type == 'no-config':
        config = None
        decoder_call_count = 0
    else:
        config = Configuration()
        if config_type == 'empty-config':
            decoder_call_count = 0
        else:
            assert config_type == 'single-column-config'
            config.sanitizers["test.notes"] = (lambda x: x)
            decoder_call_count = 3  # Number of rows in test table

    data = {
        'ok': MOCK_PG_DUMP_OUTPUT,
        'invalid': INVALID_MOCK_PG_DUMP_OUTPUT,
    }[data_label]

    should_raise = (
        config_type == 'single-column-config'
        and data_label == 'invalid')

    url = urlparse.urlparse("postgres://localhost/test")
    with mock.patch("subprocess.Popen", side_effect=create_mock_popen(data)):
        with mock.patch.object(dump_postgres, 'decode_copy_value') as decoder:
            decoder.side_effect = decode_copy_value
            if should_raise:
                with pytest.raises(ValueError):
                    list(sanitize(url, config))
            else:
                expected_output = data.decode('utf-8').splitlines()
                assert list(sanitize(url, config)) == expected_output
                assert decoder.call_count == decoder_call_count
