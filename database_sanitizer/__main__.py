# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import argparse
import codecs
import os
import sys

import six

from .config import Configuration
from .dump import run


def main(argv=sys.argv):
    parser = argparse.ArgumentParser(
        prog=(argv[0] if len(argv) else "database-sanitizer"),
        description="Sanitizes contents of databases.",
    )
    parser.add_argument(
        "--config",
        "-c",
        type=str,
        dest="config",
        help="Path to the sanitizer configuration file.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=str,
        dest="output",
        help=(
            "Path to the file where the sanitized database will be written "
            "into. If omitted, standard output will be used instead."
        ),
    )
    parser.add_argument(
        "url",
        help="Database URL to which to connect into and sanitize contents.",
    )

    args = parser.parse_args(args=argv[1:])
    output = sys.stdout
    if six.PY2:
        output = codecs.getwriter("utf-8")(output)
    config = None

    if args.config:
        conf_dir = os.path.realpath(os.path.dirname(args.config))
        sys.path.insert(0, conf_dir)
        config = Configuration.from_file(args.config)
    if args.output:
        output = open(args.output, "w")

    try:
        run(
            url=args.url,
            output=output,
            config=config,
        )
    finally:
        if args.output:
            output.close()


if __name__ == "__main__":
    main()
