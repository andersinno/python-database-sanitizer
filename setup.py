# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from setuptools import setup


setup(
    name="database-sanitizer",
    version="0.1.0",
    descriptions="Sanitizes contents of a database.",
    url="https://github.com/andersinno/python-database-sanitizer",
    include_package_data=True,
    packages=[
        "database_sanitizer",
        "database_sanitizer.dump",
        "database_sanitizer.utils",
    ],
    install_requires=[
        "PyYAML>=3.12",
        "six>=1.11.0",
    ],
    platforms=["OS Independent"],
)
