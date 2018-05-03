# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import pytest

from ..config import Configuration, ConfigurationError


def test_load_addon_packages():
    config = Configuration()

    config.load_addon_packages({})
    assert config.addon_packages is None

    with pytest.raises(ConfigurationError):
        config.load_addon_packages({"config": "test"})

    config.load_addon_packages({"config": {}})
    assert config.addon_packages is None

    with pytest.raises(ConfigurationError):
        config.load_addon_packages({"config": {"addons": "test"}})

    with pytest.raises(ConfigurationError):
        config.load_addon_packages({"config": {"addons": [True]}})

    config.load_addon_packages({"config": {
        "addons": [
            "test1",
            "test2",
            "test3",
        ],
    }})
    assert config.addon_packages == ("test1", "test2", "test3")


def test_sanitize():
    config = Configuration()
    config.sanitizers["a.a"] = lambda value: value.upper()
    config.sanitizers["a.b"] = lambda value: value[::-1]

    assert config.sanitize("a", "a", "test") == "TEST"
    assert config.sanitize("a", "b", "test") == "tset"
    assert config.sanitize("a", "c", "test") == "test"
