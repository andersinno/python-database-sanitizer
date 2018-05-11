# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import io
import re
import subprocess

from ..utils.mysql import (
    decode_mysql_literal,
    encode_mysql_literal,
    get_mysqldump_args_and_env_from_url,
)


#: Regular expression which matches `INSERT INTO` statements produced by the
#: `mysqldump` utility, even when extended inserts have been enabled.
INSERT_INTO_PATTERN = re.compile(
    r"^INSERT INTO `(?P<table>[^`]*)`"
    r" \((?P<columns>.*)\)"
    r" VALUES (?P<values>.*);$"
)


#: Regular expression which matches various kinds of MySQL literals.
VALUE_PATTERN = re.compile(
    r"""
    # Group 1:
    (
        '(?:[^']|''|\\')*(?<![\\])'     # String literal
        |                               # or...
        [^',()]+                        # NULL, TRUE, etc.
    )
    # Group 2:
    (
        [,)]                            # Comma or closing parenthesis.
    )
    """,
    re.VERBOSE,
)


def sanitize(url, config):
    """
    Obtains dump of MySQL database by executing `mysqldump` command and
    sanitizes it output.

    :param url: URL to the database which is going to be sanitized, parsed by
                Python's URL parser.
    :type url: urllib.urlparse.ParseResult

    :param config: Optional sanitizer configuration to be used for sanitation
                   of the values stored in the database.
    :type config: database_sanitizer.config.Configuration|None
    """
    if url.scheme != "mysql":
        raise ValueError("Unsupported database type: '%s'" % (url.scheme,))

    args, env = get_mysqldump_args_and_env_from_url(url=url)

    process = subprocess.Popen(
        args=["mysqldump"] + args,
        env=env,
        stdout=subprocess.PIPE,
    )

    return sanitize_from_stream(stream=process.stdout, config=config)


def sanitize_from_stream(stream, config):
    """
    Reads dump of MySQL database from given stream and sanitizes it.

    :param stream: Stream where the database dump is expected to be available
                   from, such as stdout of `mysqldump` process.
    :type stream: file

    :param config: Optional sanitizer configuration to be used for sanitation
                   of the values stored in the database.
    :type config: database_sanitizer.config.Configuration|None
    """
    for line in io.TextIOWrapper(stream, encoding="utf-8"):
        # Eat the trailing new line.
        line = line.rstrip("\n")

        # If there is no configuration it means that there are no sanitizers
        # available.
        if not config:
            yield line
            continue

        # Does the line contain `INSERT INTO` statement? If not, use the line
        # as-is and continue into next one.
        insert_into_match = INSERT_INTO_PATTERN.match(line)
        if not insert_into_match:
            yield line
            continue

        table_name = insert_into_match.group("table")
        column_names = parse_column_names(insert_into_match.group("columns"))

        # Collect sanitizers possibly used for this table and place them into
        # a dictionary from which we can look them up by index later.
        sanitizers = {}
        for index, column_name in enumerate(column_names):
            sanitizer = config.get_sanitizer_for(
                table_name=table_name,
                column_name=column_name,
            )
            if sanitizer:
                sanitizers[index] = sanitizer

        # If this table has no sanitizers available, use the line as-is and
        # continue into next line.
        if len(sanitizers) == 0:
            yield line
            continue

        # Constructs list of tuples containing sanitized column names.
        sanitized_value_tuples = []
        for values in parse_values(insert_into_match.group("values")):
            if len(column_names) != len(values):
                raise ValueError("Mismatch between column names and values")
            sanitized_values = []
            for index, value in enumerate(values):
                sanitizer_callback = sanitizers.get(index)
                if sanitizer_callback:
                    value = sanitizer_callback(value)
                sanitized_values.append(encode_mysql_literal(value))
            sanitized_value_tuples.append(sanitized_values)

        # Finally create new `INSERT INTO` statement from the sanitized values.
        yield "INSERT INTO `%s` (%s) VALUES %s;" % (
            table_name,
            ", ".join("`" + column_name + "`" for column_name in column_names),
            ",".join(
                "(" + ",".join(value_tuple) + ")"
                for value_tuple in sanitized_value_tuples
            ),
        )


def parse_column_names(text):
    """
    Extracts column names from a string containing quoted and comma separated
    column names of a table.

    :param text: Line extracted from MySQL's `INSERT INTO` statement containing
                 quoted and comma separated column names.
    :type text: str

    :return: Tuple containing just the column names.
    :rtype: tuple[str]
    """
    return tuple(
        re.sub(r"^`(.*)`$", r"\1", column_data.strip())
        for column_data in text.split(",")
    )


def parse_values(text):
    """
    Parses values from a string containing values from extended format `INSERT
    INTO` statement. Values will be yielded from the function as tuples, with
    one tuple per row in the table.

    :param text: Text extracted from MySQL's `INSERT INTO` statement containing
                 quoted and comma separated column values.
    :type text: str
    """
    assert text.startswith("(")
    pos = 1
    values = []
    text_len = len(text)
    while pos < text_len:
        match = VALUE_PATTERN.match(text, pos)
        if not match:
            break
        value = match.group(1)
        values.append(decode_mysql_literal(value.strip()))
        pos += len(value) + 1
        if match.group(2) == ")":
            # Skip comma and open parenthesis ",("
            pos += 2
            yield tuple(values)
            values = []
