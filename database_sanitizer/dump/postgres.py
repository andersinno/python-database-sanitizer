# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import codecs
import re
import subprocess

from ..utils.postgres import decode_copy_value, encode_copy_value
from ..config import PG_DUMP_DEFAULT_PARAMETERS

COPY_LINE_PATTERN = re.compile(
    r"^COPY \"(?P<schema>[^\"]*)\".\"(?P<table>[^\"]*)\" "
    r"\((?P<columns>.*)\) "
    r"FROM stdin;$"
)


def sanitize(url, config):
    """
    Obtains dump of an Postgres database by executing `pg_dump` command and
    sanitizes it's output.

    :param url: URL to the database which is going to be sanitized, parsed by
                Python's URL parser.
    :type url: six.moves.urllib.parse.ParseResult

    :param config: Optional sanitizer configuration to be used for sanitation
                   of the values stored in the database.
    :type config: database_sanitizer.config.Configuration|None
    """
    if url.scheme not in ("postgres", "postgresql", "postgis"):
        raise ValueError("Unsupported database type: '%s'" % (url.scheme,))

    extra_params = PG_DUMP_DEFAULT_PARAMETERS
    if config:
        extra_params = config.pg_dump_params

    process = subprocess.Popen(
        (
            "pg_dump",
            # Force output to be UTF-8 encoded.
            "--encoding=utf-8",
            # Quote all table and column names, just in case.
            "--quote-all-identifiers",
            # Luckily `pg_dump` supports DB URLs, so we can just pass it the
            # URL as argument to the command.
            "--dbname",
            url.geturl().replace('postgis://', 'postgresql://'),
         ) + tuple(extra_params),
        stdout=subprocess.PIPE,
    )

    sanitize_value_line = None
    current_table = None
    current_table_columns = None

    for line in codecs.getreader("utf-8")(process.stdout):
        # Eat the trailing new line.
        line = line.rstrip("\n")

        # Are we currently in middle of `COPY` statement?
        if current_table:
            # Backslash following a dot marks end of an `COPY` statement.
            if line == "\\.":
                current_table = None
                current_table_columns = None
                yield "\\."
                continue

            if not sanitize_value_line:
                yield line
                continue

            yield sanitize_value_line(line)
            continue

        # Is the line beginning of `COPY` statement?
        copy_line_match = COPY_LINE_PATTERN.match(line)
        if not copy_line_match:
            yield line
            continue

        current_table = copy_line_match.group("table")
        current_table_columns = parse_column_names(copy_line_match.group("columns"))

        sanitize_value_line = get_value_line_sanitizer(
            config, current_table, current_table_columns)

        yield line


def get_value_line_sanitizer(config, table, columns):
    if not config:
        return None

    def get_sanitizer(column):
        sanitizer = config.get_sanitizer_for(table, column)

        if not sanitizer:
            return _identity

        def decode_sanitize_encode(value):
            return encode_copy_value(sanitizer(decode_copy_value(value)))

        return decode_sanitize_encode

    sanitizers = [get_sanitizer(column) for column in columns]

    if all(x is _identity for x in sanitizers):
        return None

    def sanitize_line(line):
        values = line.split('\t')
        if len(values) != len(columns):
            raise ValueError("Mismatch between column names and values.")
        return '\t'.join(
            sanitizer(value)
            for (sanitizer, value) in zip(sanitizers, values))

    return sanitize_line


def _identity(x):
    return x


def parse_column_names(text):
    """
    Extracts column names from a string containing quoted and comma separated
    column names.

    :param text: Line extracted from `COPY` statement containing quoted and
                 comma separated column names.
    :type text: str

    :return: Tuple containing just the column names.
    :rtype: tuple[str]
    """
    return tuple(
        re.sub(r"^\"(.*)\"$", r"\1", column_name.strip())
        for column_name in text.split(",")
    )


def parse_values(text):
    """
    Parses line following `COPY` statement containing values for a single row
    in the table, in custom Postgres format.

    :param text: Line following `COPY` statement containing values.
    :type text: str

    :return: Column values extracted from the given line.
    :rtype: tuple[str|None]
    """
    return tuple(decode_copy_value(value) for value in text.split("\t"))
