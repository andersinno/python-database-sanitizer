# -*- coding: utf-8 -*-

from collections import namedtuple

import mock
import pytest

from .. import config
from ..config import Configuration, ConfigurationError


@mock.patch.object(config, 'open')
@mock.patch('yaml.safe_load')
def test_from_file(mocked_yaml_load, mocked_open):
    mocked_yaml_load.return_value = {}

    Configuration.from_file('filename.yml')

    assert mocked_open.call_args == (('filename.yml', 'rb'), {})
    opened_file = mocked_open.return_value.__enter__.return_value
    assert mocked_yaml_load.call_args == ((opened_file,), {})


def test_load_config_data_must_be_dict():
    config = Configuration()
    config.load({})
    with pytest.raises(ConfigurationError):
        config.load(config_data="test")


def test_load_dump_extra_parameters():
    config = Configuration()

    config.load_dump_extra_parameters({})
    assert config.mysqldump_params == ["--single-transaction"]
    assert config.pg_dump_params == []

    with pytest.raises(ConfigurationError):
        config.load_dump_extra_parameters({"config": "test"})

    config.load_dump_extra_parameters({"config": {}})
    assert config.mysqldump_params == ["--single-transaction"]
    assert config.pg_dump_params == []

    with pytest.raises(ConfigurationError):
        config.load_dump_extra_parameters({"config": {
            "extra_parameters": "test"
        }})

    with pytest.raises(ConfigurationError):
        config.load_dump_extra_parameters({"config": {
            "extra_parameters": [True]
        }})

    with pytest.raises(ConfigurationError):
        config.load_dump_extra_parameters({"config": {
            "extra_parameters": {
                "mysqldump": "hernekeitto",
            },
        }})

    with pytest.raises(ConfigurationError):
        config.load_dump_extra_parameters({"config": {
            "extra_parameters": {
                "pg_dump": "viina",
            },
        }})

    config.load_dump_extra_parameters({"config": {
        "extra_parameters": {
            "mysqldump": ["--double-transaction"],
            "pg_dump": ["--exclude-table=something"],
        },
    }})
    assert config.mysqldump_params == ["--double-transaction"]
    assert config.pg_dump_params == ["--exclude-table=something"]


def test_load_addon_packages():
    config = Configuration()

    config.load_addon_packages({})
    assert config.addon_packages == []

    with pytest.raises(ConfigurationError):
        config.load_addon_packages({"config": "test"})

    config.load_addon_packages({"config": {}})
    assert config.addon_packages == []

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
    assert config.addon_packages == ["test1", "test2", "test3"]


def test_load_sanitizers():
    config = Configuration()

    with pytest.raises(ConfigurationError):
        config.load_sanitizers({"strategy": "test"})

    with pytest.raises(ConfigurationError):
        config.load_sanitizers({"strategy": {"test": "test"}})

    def mock_find_sanitizer(*args):
        return lambda value: value

    with mock.patch("database_sanitizer.config.Configuration.find_sanitizer",
                    side_effect=mock_find_sanitizer):
        with pytest.raises(ConfigurationError):
            config.load_sanitizers({"strategy": {"table1": {"column1": True}}})

        config.load_sanitizers({"strategy": {
            "table1": {
                "column1": None,
                "column2": "test.test",
            },
            "table2": {
                "column1": "test.test",
            },
            "table3": None,
        }})

    assert "table1.column1" not in config.sanitizers
    assert "table1.column2" in config.sanitizers
    assert "table2.column1" in config.sanitizers


def test_table_skip_rows_configuration():
    config = Configuration()

    with pytest.raises(ConfigurationError):
        config.load_sanitizers({"strategy": "test"})

    def mock_find_sanitizer(*args):
        return lambda value: value

    with mock.patch("database_sanitizer.config.Configuration.find_sanitizer",
                    side_effect=mock_find_sanitizer):

        config.load_sanitizers({"strategy": {
            "table1": "skip_rows",
            "table2": {
                "column1": "test",
            }
        }})

    assert "table2.column1" in config.sanitizers
    assert "table1" in config.skip_rows_for_tables


def test_find_sanitizer():
    config = Configuration()

    with pytest.raises(ConfigurationError):
        config.find_sanitizer("test")

    def mock_find_sanitizer_from_module1(module_name, function_name):
        assert module_name == "sanitizers.test"
        assert function_name == "sanitize_test"
        return lambda value: value

    with mock.patch("database_sanitizer.config.Configuration.find_sanitizer_from_module",
                    side_effect=mock_find_sanitizer_from_module1):
        assert config.find_sanitizer("test.test") is not None

    def mock_find_sanitizer_from_module2(module_name, function_name):
        assert module_name in ("sanitizers.test", "addon.test")
        assert function_name == "sanitize_test"
        if module_name.startswith("addon."):
            return lambda value: value
        else:
            return None

    with mock.patch("database_sanitizer.config.Configuration.find_sanitizer_from_module",
                    side_effect=mock_find_sanitizer_from_module2):
        config.addon_packages = ("addon",)
        assert config.find_sanitizer("test.test") is not None

    def mock_find_sanitizer_from_module3(module_name, function_name):
        assert module_name in (
            "sanitizers.test",
            "addon.test",
            "database_sanitizer.sanitizers.test",
        )
        assert function_name == "sanitize_test"
        if module_name.startswith("database_sanitizer."):
            return lambda value: value
        else:
            return None

    with mock.patch("database_sanitizer.config.Configuration.find_sanitizer_from_module",
                    side_effect=mock_find_sanitizer_from_module3):
        assert config.find_sanitizer("test.test") is not None

    def mock_find_sanitizer_from_module4(module_name, function_name):
        return None

    with mock.patch("database_sanitizer.config.Configuration.find_sanitizer_from_module",
                    side_effect=mock_find_sanitizer_from_module4):
        with pytest.raises(ConfigurationError):
            config.find_sanitizer("test.test")


def test_find_sanitizer_from_module():
    def mock_import1(module_name):
        assert module_name == "test"
        raise ImportError("Should be catched")

    with mock.patch("importlib.import_module", side_effect=mock_import1):
        assert Configuration.find_sanitizer_from_module("test", "test") is None

    mock_module_type = namedtuple("mock_module", ("test",))

    def mock_import2(module_name):
        assert module_name == "test"
        return mock_module_type(test=None)

    with mock.patch("importlib.import_module", side_effect=mock_import2):
        assert Configuration.find_sanitizer_from_module("test", "test") is None

    def mock_import3(module_name):
        assert module_name == "test"
        return mock_module_type(test=lambda value: value)

    with mock.patch("importlib.import_module", side_effect=mock_import3):
        assert Configuration.find_sanitizer_from_module("test", "test") is not None

    def mock_import4(module_name):
        assert module_name == "test"
        return mock_module_type(test="test")

    with mock.patch("importlib.import_module", side_effect=mock_import4):
        with pytest.raises(ConfigurationError):
            Configuration.find_sanitizer_from_module("test", "test")


def test_sanitize():
    config = Configuration()
    config.sanitizers["a.a"] = lambda value: value.upper()
    config.sanitizers["a.b"] = lambda value: value[::-1]

    assert config.sanitize("a", "a", "test") == "TEST"
    assert config.sanitize("a", "b", "test") == "tset"
    assert config.sanitize("a", "c", "test") == "test"
