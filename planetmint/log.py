# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

import planetmint
import logging

from planetmint.transactions.common.exceptions import ConfigurationError
from logging.config import dictConfig as set_logging_config
import os


DEFAULT_LOG_DIR = os.getcwd()

DEFAULT_LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'console': {
            'class': 'logging.Formatter',
            'format': ('[%(asctime)s] [%(levelname)s] (%(name)s) '
                       '%(message)s (%(processName)-10s - pid: %(process)d)'),
            'datefmt': '%Y-%m-%d %H:%M:%S',
        },
        'file': {
            'class': 'logging.Formatter',
            'format': ('[%(asctime)s] [%(levelname)s] (%(name)s) '
                       '%(message)s (%(processName)-10s - pid: %(process)d)'),
            'datefmt': '%Y-%m-%d %H:%M:%S',
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'console',
            'level': logging.INFO,
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(DEFAULT_LOG_DIR, 'planetmint.log'),
            'mode': 'w',
            'maxBytes': 209715200,
            'backupCount': 5,
            'formatter': 'file',
            'level': logging.INFO,
        },
        'errors': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.path.join(DEFAULT_LOG_DIR, 'planetmint-errors.log'),
            'mode': 'w',
            'maxBytes': 209715200,
            'backupCount': 5,
            'formatter': 'file',
            'level': logging.ERROR,
        }
    },
    'loggers': {},
    'root': {
        'level': logging.DEBUG,
        'handlers': ['console', 'file', 'errors'],
    },
}


def _normalize_log_level(level):
    try:
        return level.upper()
    except AttributeError as exc:
        raise ConfigurationError('Log level must be a string!') from exc


def setup_logging():
    """Function to configure log hadlers.

    .. important::

        Configuration, if needed, should be applied before invoking this
        decorator, as starting the subscriber process for logging will
        configure the root logger for the child process based on the
        state of :obj:`planetmint.config` at the moment this decorator
        is invoked.

    """

    logging_configs = DEFAULT_LOGGING_CONFIG
    new_logging_configs = planetmint.config['log']

    if 'file' in new_logging_configs:
        filename = new_logging_configs['file']
        logging_configs['handlers']['file']['filename'] = filename

    if 'error_file' in new_logging_configs:
        error_filename = new_logging_configs['error_file']
        logging_configs['handlers']['errors']['filename'] = error_filename

    if 'level_console' in new_logging_configs:
        level = _normalize_log_level(new_logging_configs['level_console'])
        logging_configs['handlers']['console']['level'] = level

    if 'level_logfile' in new_logging_configs:
        level = _normalize_log_level(new_logging_configs['level_logfile'])
        logging_configs['handlers']['file']['level'] = level

    if 'fmt_console' in new_logging_configs:
        fmt = new_logging_configs['fmt_console']
        logging_configs['formatters']['console']['format'] = fmt

    if 'fmt_logfile' in new_logging_configs:
        fmt = new_logging_configs['fmt_logfile']
        logging_configs['formatters']['file']['format'] = fmt

    if 'datefmt_console' in new_logging_configs:
        fmt = new_logging_configs['datefmt_console']
        logging_configs['formatters']['console']['datefmt'] = fmt

    if 'datefmt_logfile' in new_logging_configs:
        fmt = new_logging_configs['datefmt_logfile']
        logging_configs['formatters']['file']['datefmt'] = fmt

    log_levels = new_logging_configs.get('granular_levels', {})

    for logger_name, level in log_levels.items():
        level = _normalize_log_level(level)
        try:
            logging_configs['loggers'][logger_name]['level'] = level
        except KeyError:
            logging_configs['loggers'][logger_name] = {'level': level}

    set_logging_config(logging_configs)
