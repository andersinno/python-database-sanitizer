# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import io
import re
import subprocess

from ..utils.postgres import decode_copy_value, encode_copy_value


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
    if url.scheme not in ("postgres", "postgresql"):
        raise ValueError("Unsupported database type: '%s'" % (url.scheme,))

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
            url.geturl(),
        ),
        stdout=subprocess.PIPE,
    )

    current_table = None
    current_table_columns = None

    for line in io.TextIOWrapper(process.stdout, encoding="utf-8"):
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

            # Otherwise we have a line containing column values. It's time to
            # parse and sanitize them.
            unsanitized_values = parse_values(line)
            sanitized_values = []

            if len(unsanitized_values) != len(current_table_columns):
                raise ValueError("Mismatch between column names and values.")

            for index, value in enumerate(unsanitized_values):
                if config:
                    value = config.sanitize(
                        table_name=current_table,
                        column_name=current_table_columns[index],
                        value=value,
                    )
                sanitized_values.append(value)

            # Convert sanitized values back into column values.
            yield "\t".join(encode_copy_value(value) for value in sanitized_values)
            continue

        # Is the line beginning of `COPY` statement?
        copy_line_match = COPY_LINE_PATTERN.match(line)
        if not copy_line_match:
            yield line
            continue

        current_table = copy_line_match.group("table")
        current_table_columns = parse_column_names(copy_line_match.group("columns"))

        yield line


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
