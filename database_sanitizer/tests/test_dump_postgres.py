# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from ..dump.postgres import parse_column_names, parse_values


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
