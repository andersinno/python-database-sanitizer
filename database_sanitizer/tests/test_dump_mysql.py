# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import io
import pytest

from six.moves.urllib import parse as urlparse

from ..config import Configuration
from ..dump.mysql import (
    parse_column_names,
    parse_values,
    sanitize,
    sanitize_from_stream,
)


MOCK_MYSQLDUMP_OUTPUT = b"""
--- Fake MySQL database dump

DROP TABLE IF EXISTS `test`;

INSERT INTO `test` (`id`, `created_at`, `notes`) VALUES \
(1,'2018-01-01','Test data 1'),\
(2,'2018-01-02','Test data 2'),\
(3,'2018-01-03','Test data 3');

--- Final line after `INSERT INTO` statement.
"""


INVALID_MOCK_MYSQLDUMP_OUTPUT = b"""
--- Fake MySQL database dump

DROP TABLE IF EXISTS `test`;

INSERT INTO `test` (`id`, `created_at`, `notes`) VALUES (1),(2),(3);

--- Final line after `INSERT INTO` statement.
"""


def test_sanitize_wrong_scheme():
    url = urlparse.urlparse("http://localhost/test")
    with pytest.raises(ValueError):
        list(sanitize(url, None))


def test_sanitize_from_stream():
    stream = io.BytesIO(MOCK_MYSQLDUMP_OUTPUT)
    config = Configuration()
    config.sanitizers["test.notes"] = lambda value: "Sanitized"
    dump_output_lines = list(sanitize_from_stream(stream, config))

    assert "--- Fake MySQL database dump" in dump_output_lines
    assert "--- Final line after `INSERT INTO` statement." in dump_output_lines
    assert """INSERT INTO `test` (`id`, `created_at`, `notes`) VALUES \
(1,'2018-01-01','Sanitized'),\
(2,'2018-01-02','Sanitized'),\
(3,'2018-01-03','Sanitized');\
""" in dump_output_lines


def test_sanitizer_invalid_input():
    stream = io.BytesIO(INVALID_MOCK_MYSQLDUMP_OUTPUT)
    config = Configuration()
    config.sanitizers["test.notes"] = lambda value: "Sanitized"

    with pytest.raises(ValueError):
        list(sanitize_from_stream(stream, config))


@pytest.mark.parametrize(
    "text,expected_column_names",
    (
        ("`test`", ("test",)),
        ("`test`, `test`", ("test", "test")),
        ("`test`,`test`", ("test", "test")),
    ),
)
def test_parse_column_names(text, expected_column_names):
    assert parse_column_names(text) == expected_column_names


@pytest.mark.parametrize(
    "text,expected_values",
    (
        ("('test'),('test')", (("test",), ("test",))),
        ("(1,2),(3,4),", ((1, 2), (3, 4))),
        ("(TRUE),(FALSE),(NULL)", ((True,), (False,), (None,))),
    ),
)
def test_parse_values(text, expected_values):
    assert tuple(parse_values(text)) == expected_values
