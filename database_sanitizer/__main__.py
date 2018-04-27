# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import argparse
import sys

from .dump import run


parser = argparse.ArgumentParser(
    description="Sanitizes contents of databases.",
)
# TODO: Add --config argument for configuration files.
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

args = parser.parse_args()
output = sys.stdout
if args.output:
    output = open(args.output[0], "w")
run(url=args.url, output=output)
if args.output:
    output.close()
