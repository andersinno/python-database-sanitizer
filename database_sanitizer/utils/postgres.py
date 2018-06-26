# -*- coding: utf-8 -*-
"""
Contains utilities for working with Postgres `COPY` command, mainly encoding
and decoding values in the custom format used by Postgres.

Documentation about copy command and the text format used by it can be found
from:
https://www.postgresql.org/docs/9.2/static/sql-copy.html

For decoding we use a regular expression to find the escape sequences
and invoke `unescape_single_character` function for each occurence.
Allowed escape sequences are precalculated into `DECODE_MAP` to make the
lookups faster.

For encoding we use a string translation table `ENCODE_TRANSLATE_TABLE`,
which maps the "forbidden" characters to escape sequences.  This is used
with `str.translate`, which is very fast way to escape characters.
"""

from __future__ import unicode_literals

import itertools
import re

import six

#: Representation of NULL value in Postgres COPY statement.
POSTGRES_COPY_NULL_VALUE = "\\N"

ENCODE_MAP = {
    '\\': '\\\\',
    '\b': '\\b',
    '\f': '\\f',
    '\n': '\\n',
    '\r': '\\r',
    '\t': '\\t',
    '\v': '\\v',
}

ENCODE_TRANSLATE_TABLE = [
    ENCODE_MAP.get(six.unichr(n), six.unichr(n))
    for n in range(256)
]

DECODE_REGEX = re.compile(r"""
\\                 # a backslash
(?:                # followed by one of these (in non-capturing parenthesis):
    [0-7]{1,3}         # 1, 2 or 3 octal digits
    |                  # or
    x[0-9a-fA-F]{1,2}  # 'x' followed by 1 or 2 hexadecimal digits
    |                  # or
    .                  # any character
    |                  # or
    \Z                 # end of string
)
""", re.VERBOSE)


def decode_copy_value(value):
    """
    Decodes value received as part of Postgres `COPY` command.

    :param value: Value to decode.
    :type value: str

    :return: Either None if the value is NULL string, or the given value where
             escape sequences have been decoded from.
    :rtype: str|None
    """
    # Test for null values first.
    if value == POSTGRES_COPY_NULL_VALUE:
        return None

    # If there is no backslash present, there's nothing to decode.
    #
    # This early return provides a little speed-up, because it's very
    # common to not have anything to decode and then simple search for
    # backslash is faster than the regex sub below.
    if '\\' not in value:
        return value

    return DECODE_REGEX.sub(unescape_single_character, value)


def unescape_single_character(match):
    """
    Unescape a single escape sequence found by regular expression.

    :param match: Regular expression match object
    :rtype: str
    :raises: ValueError if the escape sequence is invalid
    """
    try:
        return DECODE_MAP[match.group(0)]
    except KeyError:
        value = match.group(0)
        if value == '\\':
            raise ValueError("Unterminated escape sequence encountered")

        raise ValueError(
            "Unrecognized escape sequence encountered: {}".format(value))


def encode_copy_value(value):
    """
    Encodes given value into format suitable for Postgres `COPY` statement.

    :param value: Value to encode.
    :type value: str|None

    :return: Given value encoded into format that is suitable to be used in the
             `COPY` command.
    :rtype: str
    """
    if value is None:
        return POSTGRES_COPY_NULL_VALUE

    return value.translate(ENCODE_TRANSLATE_TABLE)


def _generate_decode_map():
    # Initialize the map by inverting the encode map
    decode_map = {
        encoded_char: char
        for (char, encoded_char) in ENCODE_MAP.items()
    }

    # Add entries for 1-3 octal digits and 1-2 hexadecimal digits
    digit_encode_params = [
        # (base, prefix, lengths, digit_chars)
        (8, '\\', [1, 2, 3], '01234567'),
        (16, '\\x', [1, 2], '0123456789abcdefABCDEF')
    ]
    for (base, prefix, lengths, digit_chars) in digit_encode_params:
        for length in lengths:
            for digits in itertools.product(digit_chars, repeat=length):
                digit_string = ''.join(digits)
                value = int(digit_string, base=base)
                char = six.unichr(value)
                decode_map[prefix + digit_string] = char

    return decode_map


DECODE_MAP = _generate_decode_map()
