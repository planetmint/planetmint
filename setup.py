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
    sys.exit('Please use Python version 3.9 or higher.')

with open('README.md') as readme_file:
    readme = readme_file.read()

# get the version
version = {}
with open('planetmint/version.py') as fp:
    exec(fp.read(), version)

def check_setuptools_features():
    """Check if setuptools is up to date."""
    import pkg_resources
    try:
        list(pkg_resources.parse_requirements('foo~=1.0'))
    except ValueError:
        sys.exit('Your Python distribution comes with an incompatible version '
                 'of `setuptools`. Please run:\n'
                 ' $ pip3 install --upgrade setuptools\n'
                 'and then run this command again')

import pathlib
import pkg_resources

with pathlib.Path('docs/root/requirements.txt').open() as requirements_txt:
    docs_require= [
        str(requirement)
        for requirement
        in pkg_resources.parse_requirements(requirements_txt)
    ]

check_setuptools_features()

dev_require = [
    'ipdb',
    'ipython',
    'watchdog',
    'logging_tree',
    'pre-commit',
    'twine'
]

tests_require = [
    'coverage',
    'pep8',
    'flake8',
    'flake8-quotes==0.8.1',
    'hypothesis>=5.3.0',
    'pytest>=3.0.0',
    'pytest-cov==2.8.1',
    'pytest-mock',
    'pytest-xdist',
    'pytest-flask',
    'pytest-aiohttp',
    'pytest-asyncio',
    'tox',
] + docs_require

install_requires = [
    'chardet==3.0.4',
    'aiohttp==3.8.1',
    'abci==0.8.3',
    'planetmint-cryptoconditions>=0.9.7',
    'flask-cors==3.0.10',
    'flask-restful==0.3.9',
    'flask==2.0.1',
    'gunicorn==20.1.0',
    'jsonschema==3.2.0',
    'logstats==0.3.0',
    'packaging>=20.9',
    # TODO Consider not installing the db drivers, or putting them in extras.
    'protobuf==3.20.1',
    'pymongo==3.11.4',
    'python-rapidjson==1.0',
    'pyyaml==5.4.1',
    'requests>=2.25.1',
    'setproctitle==1.2.2',
    'werkzeug==2.0.3',
    'nest-asyncio==1.5.5',
    'protobuf==3.20.1'

]

if sys.version_info < (3, 6):
    install_requires.append('pysha3~=1.0.2')

setup(
    name='Planetmint',
    version=version['__version__'],
    description='Planetmint: The Blockchain Database',
    long_description=readme,
    long_description_content_type='text/markdown',
    url='https://github.com/Planetmint/planetmint/',
    author='Planetmint Contributors',
    author_email='contact@ipdb.global',
    license='AGPLv3',
    zip_safe=False,
    python_requires='>=3.9',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'Topic :: Database',
        'Topic :: Database :: Database Engines/Servers',
        'Topic :: Software Development',
        'Natural Language :: English',
        'License :: OSI Approved :: Apache Software License',
        'Programming Language :: Python :: 3.9',
        'Operating System :: MacOS :: MacOS X',
        'Operating System :: POSIX :: Linux',
    ],

    packages=find_packages(exclude=['tests*']),

    scripts=['pkg/scripts/planetmint-monit-config'],

    entry_points={
        'console_scripts': [
            'planetmint=planetmint.commands.planetmint:main'
        ],
    },
    install_requires=install_requires,
    setup_requires=['pytest-runner'],
    tests_require=tests_require,
    extras_require={
        'test': tests_require,
        'dev': dev_require + tests_require + docs_require,
        'docs': docs_require,
    },
    package_data={
        'planetmint.transactions.common.schema': ['v1.0/*.yaml','v2.0/*.yaml','v3.0/*.yaml' ],
    },
)
