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

CREATE TABLE `test` (
`id` int(11) NOT NULL AUTO_INCREMENT,
`created_at` date NOT NULL,
`notes` varchar(255) NOT NULL,
PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO `test` (`id`, `created_at`, `notes`) VALUES \
(1,'2018-01-01','Test data 1'),\
(2,'2018-01-02','Test data 2'),\
(3,'2018-01-03','Test data 3');

--- Final line after `INSERT INTO` statement.
"""

MOCK_MYSQLDUMP_OUTPUT_WITH_U2028 = b"""
--- Fake MySQL database dump

DROP TABLE IF EXISTS `test`;

CREATE TABLE `test` (
`id` int(11) NOT NULL AUTO_INCREMENT,
`created_at` date NOT NULL,
`notes` varchar(255) NOT NULL,
PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO `test` (`id`, `created_at`, `notes`) VALUES \
(1,'2018-01-01','Test \xe2\x80\xa8 data 1'),\
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

def test_sanitize_with_u2028_from_stream():
    stream = io.BytesIO(MOCK_MYSQLDUMP_OUTPUT_WITH_U2028)
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


def test_skip_table_rows():
    stream = io.BytesIO(MOCK_MYSQLDUMP_OUTPUT)
    config = Configuration()
    config.skip_rows_for_tables.append('test')

    output = list(sanitize_from_stream(stream, config))

    assert output == [
        '',
        '--- Fake MySQL database dump',
        '',
        'DROP TABLE IF EXISTS `test`;',
        '',
        'CREATE TABLE `test` (',
        '`id` int(11) NOT NULL AUTO_INCREMENT,',
        '`created_at` date NOT NULL,',
        '`notes` varchar(255) NOT NULL,',
        'PRIMARY KEY (`id`)',
        ') ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;',
        '',
        '',
        '--- Final line after `INSERT INTO` statement.',
    ]


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
        ("(x')", ()),  # Invalid data
    ),
)
def test_parse_values(text, expected_values):
    assert tuple(parse_values(text)) == expected_values


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
        'ok': MOCK_MYSQLDUMP_OUTPUT,
        'invalid': INVALID_MOCK_MYSQLDUMP_OUTPUT,
    }[data_label]

    should_raise = (
        config_type == 'single-column-config'
        and data_label == 'invalid')

    dump_stream = io.BytesIO(data)
    if should_raise:
        with pytest.raises(ValueError):
            list(sanitize_from_stream(dump_stream, config))
    else:
        expected_output = data.decode('utf-8').splitlines()
        result = list(sanitize_from_stream(dump_stream, config))
        assert result == expected_output
