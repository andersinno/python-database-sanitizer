# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import importlib

from six.moves.urllib import parse as urlparse

from .. import session

SUPPORTED_DATABASE_MODULES = {
    "mysql": "database_sanitizer.dump.mysql",
    "postgres": "database_sanitizer.dump.postgres",
    "postgresql": "database_sanitizer.dump.postgres",
    "postgis": "database_sanitizer.dump.postgres",
}


# Register supported database schemes.
for scheme in SUPPORTED_DATABASE_MODULES.keys():
    urlparse.uses_netloc.append(scheme)


def run(url, output, config):
    """
    Extracts database dump from given database URL and outputs sanitized
    copy of it into given stream.

    :param url: URL to the database which is to be sanitized.
    :type url: str

    :param output: Stream where sanitized copy of the database dump will be
                   written into.
    :type output: file

    :param config: Optional sanitizer configuration to be used for sanitation
                   of the values stored in the database.
    :type config: database_sanitizer.config.Configuration|None
    """
    parsed_url = urlparse.urlparse(url)
    db_module_path = SUPPORTED_DATABASE_MODULES.get(parsed_url.scheme)
    if not db_module_path:
        raise ValueError("Unsupported database scheme: '%s'" % (parsed_url.scheme,))
    db_module = importlib.import_module(db_module_path)
    session.reset()
    for line in db_module.sanitize(url=parsed_url, config=config):
        output.write(line + "\n")
