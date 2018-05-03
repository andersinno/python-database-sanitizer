# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import argparse
import sys

from .config import Configuration
from .dump import run


def main(args=None):
    if args is None:
        args = sys.argv[1:]

    parser = argparse.ArgumentParser(
        description="Sanitizes contents of databases.",
    )
    parser.add_argument(
        "--config",
        "-c",
        nargs=1,
        type=str,
        dest="config",
        help="Path to the sanitizer configuration file.",
    )
    parser.add_argument(
        "--output",
        "-o",
        nargs=1,
        type=str,
        dest="output",
        help=(
            "Path to the file where the sanitized database will be written into. "
            "If omitted, standard output will be used instead."
        ),
    )
    parser.add_argument(
        "url",
        help="Database URL to which to connect into and sanitize contents.",
    )

    args = parser.parse_args(args=args)
    output = sys.stdout
    config = None

    if args.config:
        config = Configuration.from_file(args.config[0])
    if args.output:
        output = open(args.output[0], "w")

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
