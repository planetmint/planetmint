# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

from argparse import Namespace
import pytest

from planetmint.config import Config

@pytest.fixture
def mock_run_configure(monkeypatch):
    from planetmint.commands import planetmint
    monkeypatch.setattr(planetmint, 'run_configure', lambda *args, **kwargs: None)


@pytest.fixture
def mock_write_config(monkeypatch):
    from planetmint import config_utils
    monkeypatch.setattr(config_utils, 'write_config', lambda *args: None)


@pytest.fixture
def mock_db_init_with_existing_db(monkeypatch):
    from planetmint.commands import planetmint
    monkeypatch.setattr(planetmint, '_run_init', lambda: None)


@pytest.fixture
def mock_processes_start(monkeypatch):
    from planetmint import start
    monkeypatch.setattr(start, 'start', lambda *args: None)


@pytest.fixture
def mock_generate_key_pair(monkeypatch):
    monkeypatch.setattr('planetmint.common.crypto.generate_key_pair', lambda: ('privkey', 'pubkey'))


@pytest.fixture
def mock_planetmint_backup_config(monkeypatch):
    _config = Config().get()
    _config['database']['host']='host'
    _config['database']['port']=12345
    _config['database']['name']='adbname'
    Config().set( _config )


@pytest.fixture
def run_start_args(request):
    param = getattr(request, 'param', {})
    return Namespace(
        config=param.get('config'),
        skip_initialize_database=param.get('skip_initialize_database', False),
    )


@pytest.fixture
def mocked_setup_logging(mocker):
    return mocker.patch(
        'planetmint.log.setup_logging',
        autospec=True,
        spec_set=True,
    )
