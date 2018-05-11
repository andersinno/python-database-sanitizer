# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import re
import six

try:
    import pymysql
except ImportError:
    raise RuntimeError("You need to install PyMySQL for MySQL support")


def get_mysqldump_args_and_env_from_url(url):
    """
    Constructs list of command line arguments and dictionary of environment
    variables that can be given to `mysqldump` executable to obtain database
    dump of the database described in given URL.

    :param url: Parsed database URL.
    :type url: urllib.urlparse.ParseResult

    :return: List of command line arguments as well as dictionary of
             environment variables that can be used to launch the MySQL dump
             process to obtain dump of the database.
    :rtype: tuple[list[str],dict[str,str]]
    """
    args = [
        # Without this, `INSERT INTO` statements will exclude column names from
        # the output, which are required for sanitation.
        "--complete-insert",

        # This enables use for "exteded inserts" where multiple rows of a table
        # are included in a single `INSERT INTO` statement (contents of the
        # entire table even, if it's within limits). We use it to increase the
        # performance of the sanitation and to decrease the dump size.
        "--extended-insert",

        # This makes the `mysqldump` to attempt to limit size of a single line
        # into 10 megabytes. We use it to reduce memory consumption.
        "--net_buffer_length=10240",

        # Hostname of the database to connect into, should be always present in
        # the parsed database URL.
        "-h",
        url.hostname,
    ]
    env = {}

    if url.port is not None:
        args.extend(("-P", six.text_type(url.port)))

    if url.username:
        args.extend(("-u", url.username))

    if url.password:
        env["MYSQL_PWD"] = url.password

    if len(url.path) < 2 or not url.path.startswith("/"):
        raise ValueError("Name of the database is missing from the URL")

    args.append(url.path[1:])

    return args, env


MYSQL_NULL_PATTERN = re.compile(r"^NULL$", re.IGNORECASE)
MYSQL_BOOLEAN_PATTERN = re.compile(r"^(TRUE|FALSE)$", re.IGNORECASE)
MYSQL_FLOAT_PATTERN = re.compile(r"^[+-]?\d*\.\d+([eE][+-]?\d+)?$")
MYSQL_INT_PATTERN = re.compile(r"^\d+$")
MYSQL_STRING_PATTERN = re.compile(r"'(?:[^']|''|\\')*(?<![\\])'")


def decode_mysql_literal(text):
    """
    Attempts to decode given MySQL literal into Python value.

    :param text: Value to be decoded, as MySQL literal.
    :type text: str

    :return: Python version of the given MySQL literal.
    :rtype: any
    """
    if MYSQL_NULL_PATTERN.match(text):
        return None

    if MYSQL_BOOLEAN_PATTERN.match(text):
        return text.lower() == "true"

    if MYSQL_FLOAT_PATTERN.match(text):
        return float(text)

    if MYSQL_INT_PATTERN.match(text):
        return int(text)

    if MYSQL_STRING_PATTERN.match(text):
        return decode_mysql_string_literal(text)

    raise ValueError("Unable to decode given value: %r" % (text,))


MYSQL_STRING_ESCAPE_SEQUENCE_PATTERN = re.compile(r"\\(.)")
MYSQL_STRING_ESCAPE_SEQUENCE_MAPPING = {
    "\\0": "\000",
    "\\b": "\b",
    "\\n": "\n",
    "\\r": "\r",
    "\\t": "\t",
    "\\Z": "\032",
}


def decode_mysql_string_literal(text):
    """
    Removes quotes and decodes escape sequences from given MySQL string literal
    returning the result.

    :param text: MySQL string literal, with the quotes still included.
    :type text: str

    :return: Given string literal with quotes removed and escape sequences
             decoded.
    :rtype: str
    """
    assert text.startswith("'")
    assert text.endswith("'")

    # Ditch quotes from the string literal.
    text = text[1:-1]

    return MYSQL_STRING_ESCAPE_SEQUENCE_PATTERN.sub(
        unescape_single_character,
        text,
    )


def unescape_single_character(match):
    """
    Unescape a single escape sequence found from a MySQL string literal,
    according to the rules defined at:
    https://dev.mysql.com/doc/refman/5.6/en/string-literals.html#character-escape-sequences

    :param match: Regular expression match object.

    :return: Unescaped version of given escape sequence.
    :rtype: str
    """
    value = match.group(0)
    assert value.startswith("\\")
    return MYSQL_STRING_ESCAPE_SEQUENCE_MAPPING.get(value) or value[1:]


def encode_mysql_literal(value):
    """
    Converts given Python value into MySQL literal, suitable to be used inside
    `INSERT INTO` statement.

    :param value: Value to convert into MySQL literal.
    :type value: any

    :return: Given value encoded into MySQL literal.
    :rtype: str
    """
    return pymysql.converters.escape_item(value, "utf-8")
