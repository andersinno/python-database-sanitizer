# -*- coding: utf-8 -*-

import importlib

from six.moves.urllib import parse as urlparse


SUPPORTED_DATABASE_MODULES = {
    "postgres": "database_sanitizer.dump.postgres",
    "postgresql": "database_sanitizer.dump.postgres",
}


# Register supported database schemes.
urlparse.uses_netloc.append("postgres")
urlparse.uses_netloc.append("postgresql")


def run(url, output):
    """
    Extracts database dump from given database URL and outputs sanitized
    copy of it into given stream.

    :param url: URL to the database which is to be sanitized.
    :type url: str

    :param output: Stream where sanitized copy of the database dump will be
                   written into.
    :type output: file
    """
    parsed_url = urlparse.urlparse(url)
    db_module_path = SUPPORTED_DATABASE_MODULES.get(parsed_url.scheme)
    if not db_module_path:
        raise ValueError("Unsupported database scheme: '%s'" % (parsed_url.scheme,))
    db_module = importlib.import_module(db_module_path)
    for line in db_module.sanitize(url=parsed_url):
        output.write(line + "\n")
