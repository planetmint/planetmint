# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

"""
Planetmint: The Blockchain Database

For full docs visit https://docs.planetmint.com

"""

import sys
from setuptools import setup, find_packages

if sys.version_info < (3, 9):
    sys.exit("Please use Python version 3.9 or higher.")

with open("README.md") as readme_file:
    readme = readme_file.read()

# get the version
version = {}
with open("planetmint/version.py") as fp:
    exec(fp.read(), version)


def check_setuptools_features():
    """Check if setuptools is up to date."""
    import pkg_resources

    try:
        list(pkg_resources.parse_requirements("foo~=1.0"))
    except ValueError:
        sys.exit(
            "Your Python distribution comes with an incompatible version "
            "of `setuptools`. Please run:\n"
            " $ pip3 install --upgrade setuptools\n"
            "and then run this command again"
        )


import pathlib
import pkg_resources

docs_require = [
    "aafigure==0.6",
    "alabaster==0.7.12",
    "Babel==2.10.1",
    "certifi==2021.10.8",
    "charset-normalizer==2.0.12",
    "commonmark==0.9.1",
    "docutils==0.17.1",
    "idna==2.10",  # version conflict with requests lib (required version <3)
    "imagesize==1.3.0",
    "importlib-metadata==4.11.3",
    "Jinja2==3.0.0",
    "markdown-it-py==2.1.0",
    "MarkupSafe==2.1.1",
    "mdit-py-plugins==0.3.0",
    "mdurl==0.1.1",
    "myst-parser==0.17.2",
    "packaging==21.3",
    "pockets==0.9.1",
    "Pygments==2.12.0",
    "pyparsing==3.0.8",
    "pytz==2022.1",
    "PyYAML>=5.4.0",
    "requests>=2.25i.1",
    "six==1.16.0",
    "snowballstemmer==2.2.0",
    "Sphinx==4.5.0",
    "sphinx-rtd-theme==1.0.0",
    "sphinxcontrib-applehelp==1.0.2",
    "sphinxcontrib-devhelp==1.0.2",
    "sphinxcontrib-htmlhelp==2.0.0",
    "sphinxcontrib-httpdomain==1.8.0",
    "sphinxcontrib-jsmath==1.0.1",
    "sphinxcontrib-napoleon==0.7",
    "sphinxcontrib-qthelp==1.0.3",
    "sphinxcontrib-serializinghtml==1.1.5",
    "urllib3==1.26.9",
    "wget==3.2",
    "zipp==3.8.0",
    "nest-asyncio==1.5.5",
    "sphinx-press-theme==0.8.0",
    "sphinx-documatt-theme",
]

check_setuptools_features()

dev_require = ["ipdb", "ipython", "watchdog", "logging_tree", "pre-commit", "twine", "ptvsd"]

tests_require = [
    "coverage",
    "pep8",
    "black",
    "hypothesis>=5.3.0",
    "pytest>=3.0.0",
    "pytest-cov==2.8.1",
    "pytest-mock",
    "pytest-xdist",
    "pytest-flask",
    "pytest-aiohttp",
    "pytest-asyncio",
    "tox",
] + docs_require

install_requires = [
    "chardet==3.0.4",
    "base58==2.1.1",
    "aiohttp==3.8.1",
    "abci==0.8.3",
    "planetmint-cryptoconditions>=0.10.0",
    "flask-cors==3.0.10",
    "flask-restful==0.3.9",
    "flask==2.1.2",
    "gunicorn==20.1.0",
    "jsonschema==3.2.0",
    "logstats==0.3.0",
    "packaging>=20.9",
    # TODO Consider not installing the db drivers, or putting them in extras.
    "pymongo==3.11.4",
    "tarantool==0.7.1",
    "python-rapidjson==1.0",
    "pyyaml==5.4.1",
    "requests==2.25.1",
    "setproctitle==1.2.2",
    "werkzeug==2.0.3",
    "nest-asyncio==1.5.5",
    "protobuf==3.20.1",
    "planetmint-ipld>=0.0.3",
    "pyasn1",
    "zenroom==2.1.0.dev1655293214",
    "base58>=2.1.0",
    "PyNaCl==1.4.0",
    "pyasn1>=0.4.8",
    "cryptography==3.4.7",
]

setup(
    name="Planetmint",
    version=version["__version__"],
    description="Planetmint: The Blockchain Database",
    long_description=readme,
    long_description_content_type="text/markdown",
    url="https://github.com/Planetmint/planetmint/",
    author="Planetmint Contributors",
    author_email="contact@ipdb.global",
    license="AGPLv3",
    zip_safe=False,
    python_requires=">=3.9",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "Topic :: Database",
        "Topic :: Database :: Database Engines/Servers",
        "Topic :: Software Development",
        "Natural Language :: English",
        "License :: OSI Approved :: Apache Software License",
        "Programming Language :: Python :: 3.9",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX :: Linux",
    ],
    packages=find_packages(exclude=["tests*"]),
    scripts=["pkg/scripts/planetmint-monit-config"],
    entry_points={
        "console_scripts": ["planetmint=planetmint.commands.planetmint:main"],
    },
    install_requires=install_requires,
    setup_requires=["pytest-runner"],
    tests_require=tests_require,
    extras_require={
        "test": tests_require,
        "dev": dev_require + tests_require + docs_require,
        "docs": docs_require,
    },
    package_data={
        "planetmint.transactions.common.schema": [
            "v1.0/*.yaml",
            "v2.0/*.yaml",
            "v3.0/*.yaml",
        ],
        "planetmint.backend.tarantool": ["*.lua"],
    },
)
