import subprocess
from io import BytesIO, StringIO

import mock
import pytest

from database_sanitizer import dump
from database_sanitizer.config import Configuration

EXPECTED_POPEN_KWARGS = {
    'mysql://User:Pass@HostName/Db': {
        'args': (
            'mysqldump --complete-insert --extended-insert'
            ' --net_buffer_length=10240 -h hostname -u User Db'
            ' --single-transaction'
        ).split(),
        'env': {'MYSQL_PWD': 'Pass'},
        'stdout': subprocess.PIPE,
    },
    'postgres:///Db': {
        'args': tuple((
            'pg_dump --encoding=utf-8 --quote-all-identifiers'
            ' --dbname postgres:///Db').split()),
        'stdout': subprocess.PIPE,
    },
}

for url in ['postgresql:///Db', 'postgis:///Db']:
    EXPECTED_POPEN_KWARGS[url] = EXPECTED_POPEN_KWARGS['postgres:///Db'].copy()
    EXPECTED_POPEN_KWARGS[url]['args'] = tuple(
        ' '.join(EXPECTED_POPEN_KWARGS[url]['args'])
        .replace('postgres', 'postgresql').split())


@pytest.mark.parametrize('url', list(EXPECTED_POPEN_KWARGS))
@mock.patch('subprocess.Popen')
def test_run(mocked_popen, url):
    mocked_popen.return_value.stdout = BytesIO(b'INPUT DUMP')
    output = StringIO()
    config = None
    dump.run(url, output, config)

    expected_popen_kwargs = EXPECTED_POPEN_KWARGS[url]
    (popen_args, popen_kwargs) = mocked_popen.call_args
    expected_popen_args = (
        (expected_popen_kwargs.pop('args'),) if popen_args else ())
    assert popen_args == expected_popen_args
    assert popen_kwargs == expected_popen_kwargs


@mock.patch('subprocess.Popen')
def test_run_with_mysql_extra_params(mocked_popen):
    mocked_popen.return_value.stdout = BytesIO(b'INPUT DUMP')
    output = StringIO()

    url = "mysql://User:Pass@HostName/Db"
    config = Configuration()
    config.load({
        "config": {
            "extra_parameters": {
                "mysqldump": ["--double-transaction"]
            }
        }
    })

    dump.run(url, output, config)

    expected = {
        'args': (
            'mysqldump --complete-insert --extended-insert'
            ' --net_buffer_length=10240 -h hostname -u User Db'
            ' --double-transaction'
        ).split(),
        'env': {'MYSQL_PWD': 'Pass'},
        'stdout': subprocess.PIPE,
    }

    (popen_args, popen_kwargs) = mocked_popen.call_args
    expected_popen_args = (
        (expected.pop('args'),) if popen_args else ())
    assert popen_args == expected_popen_args
    assert popen_kwargs == expected


@mock.patch('subprocess.Popen')
def test_run_with_pg_dump_extra_params(mocked_popen):
    mocked_popen.return_value.stdout = BytesIO(b'INPUT DUMP')
    output = StringIO()

    url = "postgres:///Db"
    config = Configuration()
    config.load({
        "config": {
            "extra_parameters": {
                "pg_dump": ["--exclude-table=something"]
            }
        }
    })

    dump.run(url, output, config)

    expected = {
        'args': tuple((
            'pg_dump --encoding=utf-8 --quote-all-identifiers'
            ' --dbname postgres:///Db'
            ' --exclude-table=something'
        ).split()),
        'stdout': subprocess.PIPE,
    }

    (popen_args, popen_kwargs) = mocked_popen.call_args
    expected_popen_args = (
        (expected.pop('args'),) if popen_args else ())
    assert popen_args == expected_popen_args
    assert popen_kwargs == expected


@mock.patch('subprocess.Popen')
def test_run_unknown_scheme(mocked_popen):
    with pytest.raises(ValueError) as excinfo:
        dump.run('unknown:///db', None, None)
    assert str(excinfo.value) == "Unsupported database scheme: 'unknown'"
    mocked_popen.assert_not_called()
