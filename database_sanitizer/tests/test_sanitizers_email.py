# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from ..sanitizers.email import sanitize_example


@pytest.mark.parametrize(
    "input_value,expected_output",
    (
        ("test@test.com", "example@example.org"),
        ("", ""),
        (None, None),
    ),
)
def test_sanitize_example(input_value, expected_output):
    assert sanitize_example(input_value) == expected_output
