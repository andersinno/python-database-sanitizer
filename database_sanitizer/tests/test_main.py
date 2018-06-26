from __future__ import unicode_literals

import mock
import pytest
import six

from database_sanitizer import __main__

main = __main__.main


@mock.patch.object(__main__, 'run')
def test_main_without_args(mocked_run, capsys):
    with pytest.raises(SystemExit) as excinfo:
        main(['SANI'])
    assert excinfo.value.code == 2

    captured = capsys.readouterr()
    assert captured.out == ''
    assert captured.err.splitlines() == [
        'usage: SANI [-h] [--config CONFIG] [--output OUTPUT] url',
        'SANI: error: the following arguments are required: url' if six.PY3
        else 'SANI: error: too few arguments',
    ]
    assert not mocked_run.called


@mock.patch.object(__main__, 'run')
def test_main_with_url(mocked_run, capsys):
    main(['SANI', 'some://url'])

    # Output should be empty
    captured = capsys.readouterr()
    assert captured.out == ''
    assert captured.err == ''

    # The run function should have been called with the URL
    (run_call_args, run_call_kwargs) = mocked_run.call_args
    assert run_call_args == ()
    assert set(run_call_kwargs.keys()) == {'config', 'output', 'url'}
    assert run_call_kwargs['config'] is None
    assert run_call_kwargs['url'] == 'some://url'


@pytest.mark.parametrize('optname', ['-c', '--config'])
@mock.patch.object(__main__, 'run')
@mock.patch.object(__main__, 'Configuration')
def test_main_with_config(mocked_conf, mocked_run, capsys, optname):
    main(['SANI', optname, 'config_file.yml', 'some://url'])

    # Output should be empty
    captured = capsys.readouterr()
    assert captured.out == ''
    assert captured.err == ''

    # Configuration should have been created with Configuration.from_file
    (fromfile_args, fromfile_kwargs) = mocked_conf.from_file.call_args
    assert fromfile_args == ('config_file.yml',)
    assert fromfile_kwargs == {}

    # The run function should have been called with the config and URL
    (run_call_args, run_call_kwargs) = mocked_run.call_args
    assert run_call_args == ()
    assert set(run_call_kwargs.keys()) == {'config', 'output', 'url'}
    assert run_call_kwargs['config'] == mocked_conf.from_file.return_value
    assert run_call_kwargs['url'] == 'some://url'


@pytest.mark.parametrize('optname', ['-o', '--output'])
@mock.patch.object(__main__, 'run')
@mock.patch.object(__main__, 'open')
def test_main_with_output(mocked_open, mocked_run, capsys, optname):
    main(['SANI', optname, 'output_file.sql', 'some://url'])

    # Output should be empty
    captured = capsys.readouterr()
    assert captured.out == ''
    assert captured.err == ''

    # Output file should have been opened
    (open_args, open_kwargs) = mocked_open.call_args
    assert open_args == ('output_file.sql', 'w')
    assert open_kwargs == {}

    # The run function should have been called with the output and URL
    (run_call_args, run_call_kwargs) = mocked_run.call_args
    assert run_call_args == ()
    assert set(run_call_kwargs.keys()) == {'config', 'output', 'url'}
    assert run_call_kwargs['config'] is None
    assert run_call_kwargs['output'] == mocked_open.return_value
    assert run_call_kwargs['url'] == 'some://url'
