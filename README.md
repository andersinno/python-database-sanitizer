# Database sanitation tool

[![pypi][pypi-image]][pypi-url]
[![travis][travis-image]][travis-url]
[![codecov][codecov-image]][codecov-url]

[pypi-image]: https://badge.fury.io/py/database-sanitizer.svg
[pypi-url]: https://pypi.org/project/database-sanitizer/
[travis-image]: https://travis-ci.org/andersinno/python-database-sanitizer.svg?branch=master
[travis-url]: https://travis-ci.org/andersinno/python-database-sanitizer
[codecov-image]: https://codecov.io/gh/andersinno/python-database-sanitizer/branch/master/graph/badge.svg
[codecov-url]: https://codecov.io/gh/andersinno/python-database-sanitizer

`database-sanitizer` is a tool which retrieves an database dump from
relational database and performs sanitation on the retrieved data
according to rules defined in a configuration file. Currently the
sanitation tool supports both [PostgreSQL] and [MySQL] databases.

[PostgreSQL]: https://postgres.org
[MySQL]: https://mysql.com

## Installation

`database-sanitizer` can be installed from [PyPI] with [pip] like this:

```bash
$ pip install database-sanitizer
```

If you are using MySQL, you need to install the package like this
instead, so that additional requirements are included:

```bash
$ pip install database-sanitizer[MySQL]
```

[PyPI]: https://pypi.org
[pip]: https://pip.pypa.io/en/stable/

## Usage

Once the package has been installed, `database-sanitizer` can be used
like this:

```bash
$ database-sanitizer <DATABASE-URL>
```

Command line argument `DATABASE-URL` needs to be provided so the tool
knows how to retrieve the dump from the database. With PostgreSQL, it
would be something like this:

```bash
$ database-sanitizer postgres://user:password@host/database
```

However, unless an configuration file is provided, no sanitation will be
performed on the retrieved database dump, which leads us to the next
section which will be...

## Configuration

Rules for the sanitation can be given in a configuration file written in
[YAML]. Path to the configuration file is then given to the command line
utility with `--config` argument (`-c` for shorthand) like this:

[YAML]: http://yaml.org

```bash
$ database-sanitizer -c config.yml postgres://user:password@host/database
```

The configuration file uses following kind of syntax:

```YAML
config:
  addons:
    - some.other.package
    - yet.another.package
strategy:
  user:
    first_name: name.first_name
    last_name: name.last_name
    secret_key: string.empty
```

In the example configuration above, there are first listed two "addon
packages", which are names of Python packages where the sanitizer will
be looking for sanitizer functions. They are completely optional and can
be omitted, in which case only sanitizer functions defined in package
called `sanitizers` and built-in sanitizers will be used instead.

The `strategy` portion of the configuration contains the actual
sanitation rules. First you define name of the database table (in the
example that would be `user`) followed by column names in that table
which each one mapped to sanitation function name. The name of the
sanitation function consists from two parts separated from each other by
a dot: Python module name and name of the actual function, which will
be prefixed with `sanitize_`, so `name.first_name` would be a function
called `sanitize_first_name` in a file called `name.py`.
