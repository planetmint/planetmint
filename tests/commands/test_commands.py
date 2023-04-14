# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

import json
import logging
import pytest

from unittest.mock import Mock, patch
from argparse import Namespace

from transactions.types.elections.validator_election import ValidatorElection
from transactions.types.elections.chain_migration_election import ChainMigrationElection

from planetmint.abci.rpc import ABCI_RPC
from planetmint.abci.block import Block
from planetmint.config import Config
from planetmint.commands.planetmint import run_election_show
from planetmint.commands.planetmint import run_election_new_chain_migration
from planetmint.commands.planetmint import run_election_approve
from planetmint.commands.planetmint import run_election_new_upsert_validator
from planetmint.backend.connection import Connection


from tests.utils import generate_election, generate_validators

def mock_get_validators(height):
    return [
        {
            "public_key": {"value": "zL/DasvKulXZzhSNFwx4cLRXKkSM9GPK7Y0nZ4FEylM=", "type": "ed25519-base64"},
            "voting_power": 10,
        }
    ]


@patch("planetmint.commands.utils.start")
def test_main_entrypoint(mock_start):
    from planetmint.commands.planetmint import main
    from planetmint.model.dataaccessor import DataAccessor
    
    da = DataAccessor
    del da
    main()

    assert mock_start.called

#@pytest.mark.bdb
def test_chain_migration_election_show_shows_inconclusive(b, test_abci_rpc ):
    
    from tests.utils import flush_db
    flush_db(b.models.connection, "dbname")
    validators = generate_validators([1] * 4)
    output = b.models.store_validator_set(1, [v["storage"] for v in validators])

    public_key = validators[0]["public_key"]
    private_key = validators[0]["private_key"]
    voter_keys = [v["private_key"] for v in validators]

    election, votes = generate_election(b, ChainMigrationElection, public_key, private_key, [{"data": {}}], voter_keys)

    assert not run_election_show(Namespace(election_id=election.id), b)

    b.process_block(1, [election])
    b.models.store_bulk_transactions([election])

    assert run_election_show(Namespace(election_id=election.id), b) == "status=ongoing"

    b.models.store_block(Block(height=1, transactions=[], app_hash="")._asdict())
    b.models.store_validator_set(2, [v["storage"] for v in validators])

    assert run_election_show(Namespace(election_id=election.id), b) == "status=ongoing"

    b.models.store_block(Block(height=2, transactions=[], app_hash="")._asdict())
    # TODO insert yet another block here when upgrading to Tendermint 0.22.4.

    assert run_election_show(Namespace(election_id=election.id), b) == "status=inconclusive"


@pytest.mark.bdb
def test_chain_migration_election_show_shows_concluded(b):
    validators = generate_validators([1] * 4)
    b.models.store_validator_set(1, [v["storage"] for v in validators])

    public_key = validators[0]["public_key"]
    private_key = validators[0]["private_key"]
    voter_keys = [v["private_key"] for v in validators]

    election, votes = generate_election(b, ChainMigrationElection, public_key, private_key, [{"data": {}}], voter_keys)

    assert not run_election_show(Namespace(election_id=election.id), b)

    b.models.store_bulk_transactions([election])
    b.process_block(1, [election])

    assert run_election_show(Namespace(election_id=election.id), b) == "status=ongoing"

    b.models.store_abci_chain(1, "chain-X")
    b.models.store_block(Block(height=1, transactions=[v.id for v in votes], app_hash="last_app_hash")._asdict())
    b.process_block(2, votes)

    assert (
        run_election_show(Namespace(election_id=election.id), b)
        == f'''status=concluded
chain_id=chain-X-migrated-at-height-1
app_hash=last_app_hash
validators=[{''.join([f"""
    {{
        "pub_key": {{
            "type": "tendermint/PubKeyEd25519",
            "value": "{v['public_key']}"
        }},
        "power": {v['storage']['voting_power']}
    }}{',' if i + 1 != len(validators) else ''}""" for i, v in enumerate(validators)])}
]'''
    )


def test_make_sure_we_dont_remove_any_command():
    # thanks to: http://stackoverflow.com/a/18161115/597097
    from planetmint.commands.planetmint import create_parser

    parser = create_parser()

    assert parser.parse_args(["configure", "tarantool_db"]).command
    assert parser.parse_args(["show-config"]).command
    assert parser.parse_args(["init"]).command
    assert parser.parse_args(["drop"]).command
    assert parser.parse_args(["start"]).command
    assert parser.parse_args(
        [
            "election",
            "new",
            "upsert-validator",
            "TEMP_PUB_KEYPAIR",
            "10",
            "TEMP_NODE_ID",
            "--private-key",
            "TEMP_PATH_TO_PRIVATE_KEY",
        ]
    ).command
    assert parser.parse_args(
        ["election", "new", "chain-migration", "--private-key", "TEMP_PATH_TO_PRIVATE_KEY"]
    ).command
    assert parser.parse_args(
        ["election", "approve", "ELECTION_ID", "--private-key", "TEMP_PATH_TO_PRIVATE_KEY"]
    ).command
    assert parser.parse_args(["election", "show", "ELECTION_ID"]).command
    assert parser.parse_args(["tendermint-version"]).command




@pytest.mark.bdb
def test_election_approve_called_with_bad_key(monkeypatch, caplog, b, bad_validator_path, new_validator, node_key, test_abci_rpc):
    from argparse import Namespace

    b, election_id = call_election(monkeypatch, b, new_validator, node_key, test_abci_rpc)

    # call run_upsert_validator_approve with args that point to the election, but a bad signing key
    args = Namespace(action="approve", election_id=election_id, sk=bad_validator_path, config={})

    with caplog.at_level(logging.ERROR):
        assert not run_election_approve(args, b, test_abci_rpc)
        assert (
            caplog.records[0].msg == "The key you provided does not match any of "
            "the eligible voters in this election."
        )


@patch("planetmint.config_utils.setup_logging")
@patch("planetmint.commands.planetmint._run_init")
@patch("planetmint.config_utils.autoconfigure")
def test_bigchain_run_start(mock_setup_logging, mock_run_init, mock_autoconfigure, mock_processes_start):
    from planetmint.commands.planetmint import run_start

    args = Namespace(config=None, yes=True, skip_initialize_database=False)
    run_start(args)
    assert mock_setup_logging.called


# TODO Please beware, that if debugging, the "-s" switch for pytest will
# interfere with capsys.
# See related issue: https://github.com/pytest-dev/pytest/issues/128
@pytest.mark.usefixtures("ignore_local_config_file")
def test_bigchain_show_config(capsys):
    from planetmint.commands.planetmint import run_show_config

    args = Namespace(config=None)
    _, _ = capsys.readouterr()
    run_show_config(args)
    output_config = json.loads(capsys.readouterr()[0])
    sorted_output_config = json.dumps(output_config, indent=4, sort_keys=True)
    print(f"config : {sorted_output_config}")
    # Note: This test passed previously because we were always
    # using the default configuration parameters, but since we
    # are running with docker compose now and expose parameters like
    # PLANETMINT_SERVER_BIND, PLANETMINT_WSSERVER_HOST, PLANETMINT_WSSERVER_ADVERTISED_HOST
    # the default comparison fails i.e. when config is imported at the beginning the
    # dict returned is different that what is expected after run_show_config
    # and run_show_config updates the planetmint.config
    from planetmint.config import Config

    _config = Config().get()
    sorted_config = json.dumps(_config, indent=4, sort_keys=True)
    print(f"_config : {sorted_config}")
    # del sorted_config['CONFIGURED']
    assert sorted_output_config == sorted_config


def test__run_init(mocker):
    init_db_mock = mocker.patch("planetmint.backend.tarantool.sync_io.connection.TarantoolDBConnection.init_database")

    conn = Connection()
    conn.init_database()

    init_db_mock.assert_called_once_with()


@patch("planetmint.backend.schema.drop_database")
def test_drop_db_when_assumed_yes(mock_db_drop):
    from planetmint.commands.planetmint import run_drop

    args = Namespace(config=None, yes=True)

    run_drop(args)
    assert mock_db_drop.called


@patch("planetmint.backend.schema.drop_database")
def test_drop_db_when_interactive_yes(mock_db_drop, monkeypatch):
    from planetmint.commands.planetmint import run_drop

    args = Namespace(config=None, yes=False)
    monkeypatch.setattr("planetmint.commands.planetmint.input_on_stderr", lambda x: "y")

    run_drop(args)
    assert mock_db_drop.called


@patch("planetmint.backend.schema.drop_database")
def test_drop_db_when_db_does_not_exist(mock_db_drop, capsys):
    from transactions.common.exceptions import DatabaseDoesNotExist
    from planetmint.commands.planetmint import run_drop

    args = Namespace(config=None, yes=True)
    mock_db_drop.side_effect = DatabaseDoesNotExist

    run_drop(args)
    output_message = capsys.readouterr()[1]
    assert output_message == "Drop was executed, but spaces doesn't exist.\n"
    # assert output_message == "Cannot drop '{name}'. The database does not exist.\n".format(
    #      name=Config().get()['database']['name'])


@patch("planetmint.backend.schema.drop_database")
def test_drop_db_does_not_drop_when_interactive_no(mock_db_drop, monkeypatch):
    from planetmint.commands.planetmint import run_drop

    args = Namespace(config=None, yes=False)
    monkeypatch.setattr("planetmint.commands.planetmint.input_on_stderr", lambda x: "n")

    run_drop(args)
    assert not mock_db_drop.called


# TODO Beware if you are putting breakpoints in there, and using the '-s'
# switch with pytest. It will just hang. Seems related to the monkeypatching of
# input_on_stderr.
def test_run_configure_when_config_does_not_exist(
    monkeypatch, mock_write_config, mock_generate_key_pair, mock_planetmint_backup_config
):
    from planetmint.commands.planetmint import run_configure

    monkeypatch.setattr("os.path.exists", lambda path: False)
    monkeypatch.setattr("builtins.input", lambda: "\n")
    args = Namespace(config=None, backend="localmongodb", yes=True)
    return_value = run_configure(args)
    assert return_value is None


def test_run_configure_when_config_does_exist(
    monkeypatch, mock_write_config, mock_generate_key_pair, mock_planetmint_backup_config
):
    value = {}

    def mock_write_config(newconfig):
        value["return"] = newconfig

    from planetmint.commands.planetmint import run_configure

    monkeypatch.setattr("os.path.exists", lambda path: True)
    monkeypatch.setattr("builtins.input", lambda: "\n")
    monkeypatch.setattr("planetmint.config_utils.write_config", mock_write_config)

    args = Namespace(config=None, yes=None)
    run_configure(args)
    assert value == {}


@pytest.mark.skip
@pytest.mark.parametrize("backend", ("localmongodb",))
def test_run_configure_with_backend(backend, monkeypatch, mock_write_config):
    import planetmint
    from planetmint.commands.planetmint import run_configure

    value = {}

    def mock_write_config(new_config, filename=None):
        value["return"] = new_config

    monkeypatch.setattr("os.path.exists", lambda path: False)
    monkeypatch.setattr("builtins.input", lambda: "\n")
    monkeypatch.setattr("planetmint.config_utils.write_config", mock_write_config)

    args = Namespace(config=None, backend=backend, yes=True)
    expected_config = Config().get()
    run_configure(args)

    # update the expected config with the correct backend and keypair
    backend_conf = getattr(planetmint, "_database_" + backend)
    expected_config.update({"database": backend_conf, "keypair": value["return"]["keypair"]})

    assert value["return"] == expected_config


@patch("planetmint.commands.utils.start")
def test_calling_main(start_mock, monkeypatch):
    from planetmint.commands.planetmint import main

    argparser_mock = Mock()
    parser = Mock()
    subparsers = Mock()
    subsubparsers = Mock()
    subparsers.add_parser.return_value = subsubparsers
    parser.add_subparsers.return_value = subparsers
    argparser_mock.return_value = parser
    monkeypatch.setattr("argparse.ArgumentParser", argparser_mock)
    main()

    assert argparser_mock.called is True
    parser.add_subparsers.assert_called_with(title="Commands", dest="command")
    subparsers.add_parser.assert_any_call("configure", help="Prepare the config file.")
    subparsers.add_parser.assert_any_call("show-config", help="Show the current " "configuration")
    subparsers.add_parser.assert_any_call("init", help="Init the database")
    subparsers.add_parser.assert_any_call("drop", help="Drop the database")

    subparsers.add_parser.assert_any_call("start", help="Start Planetmint")
    subparsers.add_parser.assert_any_call("tendermint-version", help="Show the Tendermint supported " "versions")

    assert start_mock.called is True


@patch("planetmint.application.validator.Validator.rollback")
@patch("planetmint.start.start")
def test_recover_db_on_start(mock_rollback, mock_start, mocked_setup_logging):
    from planetmint.commands.planetmint import run_start

    args = Namespace(config=None, yes=True, skip_initialize_database=False)
    run_start(args)

    assert mock_rollback.called
    assert mock_start.called


@pytest.mark.bdb
def test_run_recover(b, alice, bob, test_models):
    from transactions.types.assets.create import Create
    from planetmint.abci.block import Block
    from planetmint.backend import query

    tx1 = Create.generate(
        [alice.public_key],
        [([alice.public_key], 1)],
        assets=[{"data": "QmaozNR7DZHQK1ZcU9p7QdrshMvXqWK6gpu5rmrkPdT3L4"}],
        metadata="QmaozNR7DZHQK1ZcU9p7QdrshMvXqWK6gpu5rmrkPdT3L4",
    ).sign([alice.private_key])
    tx2 = Create.generate(
        [bob.public_key],
        [([bob.public_key], 1)],
        assets=[{"data": "QmaozNR7DZHQK1ZcU9p7QdrshMvXqWK6gpu5rmrkPdT3L4"}],
        metadata="QmaozNR7DZHQK1ZcU9p7QdrshMvXqWK6gpu5rmrkPdT3L4",
    ).sign([bob.private_key])

    # store the transactions
    b.models.store_bulk_transactions([tx1, tx2])

    # create a random block
    block8 = Block(app_hash="random_app_hash1", height=8, transactions=["txid_doesnt_matter"])._asdict()
    b.models.store_block(block8)

    # create the next block
    block9 = Block(app_hash="random_app_hash1", height=9, transactions=[tx1.id])._asdict()
    b.models.store_block(block9)

    # create a pre_commit state which is ahead of the commit state
    pre_commit_state = dict(height=10, transactions=[tx2.id])
    b.models.store_pre_commit_state(pre_commit_state)

    b.rollback()

    assert not query.get_transaction(b.models.connection, tx2.id)


# Helper
class MockResponse:
    def __init__(self, height):
        self.height = height

    def json(self):
        return {"result": {"latest_block_height": self.height}}


@pytest.mark.abci
def test_election_new_upsert_validator_with_tendermint(b, priv_validator_path, user_sk, validators, test_abci_rpc):
    new_args = Namespace(
        action="new",
        election_type="upsert-validator",
        public_key="HHG0IQRybpT6nJMIWWFWhMczCLHt6xcm7eP52GnGuPY=",
        power=1,
        node_id="unique_node_id_for_test_upsert_validator_new_with_tendermint",
        sk=priv_validator_path,
        config={},
    )

    election_id = run_election_new_upsert_validator(new_args, b, test_abci_rpc)

    assert b.models.get_transaction(election_id)


@pytest.mark.bdb
def test_election_new_upsert_validator_without_tendermint(caplog, b, priv_validator_path, user_sk, test_abci_rpc):
    def mock_write(modelist, endpoint, mode_commit, transaction, mode):
        b.models.store_bulk_transactions([transaction])
        return (202, "")

    b.models.get_validators = mock_get_validators
    test_abci_rpc.write_transaction = mock_write

    args = Namespace(
        action="new",
        election_type="upsert-validator",
        public_key="CJxdItf4lz2PwEf4SmYNAu/c/VpmX39JEgC5YpH7fxg=",
        power=1,
        node_id="fb7140f03a4ffad899fabbbf655b97e0321add66",
        sk=priv_validator_path,
        config={},
    )

    with caplog.at_level(logging.INFO):
        election_id = run_election_new_upsert_validator(args, b, test_abci_rpc)
        assert caplog.records[0].msg == "[SUCCESS] Submitted proposal with id: " + election_id
        assert b.models.get_transaction(election_id)


@pytest.mark.abci
def test_election_new_chain_migration_with_tendermint(b, priv_validator_path, user_sk, validators, test_abci_rpc):
    new_args = Namespace(action="new", election_type="migration", sk=priv_validator_path, config={})

    election_id = run_election_new_chain_migration(new_args, b, test_abci_rpc)

    assert b.models.get_transaction(election_id)


@pytest.mark.bdb
def test_election_new_chain_migration_without_tendermint(caplog, b, priv_validator_path, user_sk, test_abci_rpc):
    def mock_write(modelist, endpoint, mode_commit, transaction, mode):
        b.models.store_bulk_transactions([transaction])
        return (202, "")

    b.models.get_validators = mock_get_validators
    test_abci_rpc.write_transaction = mock_write

    args = Namespace(action="new", election_type="migration", sk=priv_validator_path, config={})

    with caplog.at_level(logging.INFO):
        election_id = run_election_new_chain_migration(args, b, test_abci_rpc)
        assert caplog.records[0].msg == "[SUCCESS] Submitted proposal with id: " + election_id
        assert b.models.get_transaction(election_id)


@pytest.mark.bdb
def test_election_new_upsert_validator_invalid_election(caplog, b, priv_validator_path, user_sk, test_abci_rpc):
    args = Namespace(
        action="new",
        election_type="upsert-validator",
        public_key="CJxdItf4lz2PwEf4SmYNAu/c/VpmX39JEgC5YpH7fxg=",
        power=10,
        node_id="fb7140f03a4ffad899fabbbf655b97e0321add66",
        sk="/tmp/invalid/path/key.json",
        config={},
    )

    with caplog.at_level(logging.ERROR):
        assert not run_election_new_upsert_validator(args, b, test_abci_rpc)
        assert caplog.records[0].msg.__class__ == FileNotFoundError


@pytest.mark.bdb
def test_election_new_upsert_validator_invalid_power(caplog, b, priv_validator_path, user_sk, test_abci_rpc):
    from transactions.common.exceptions import InvalidPowerChange

    def mock_write(modelist, endpoint, mode_commit, transaction, mode):
        b.models.store_bulk_transactions([transaction])
        return (400, "")

    test_abci_rpc.write_transaction = mock_write
    b.models.get_validators = mock_get_validators
    args = Namespace(
        action="new",
        election_type="upsert-validator",
        public_key="CJxdItf4lz2PwEf4SmYNAu/c/VpmX39JEgC5YpH7fxg=",
        power=10,
        node_id="fb7140f03a4ffad899fabbbf655b97e0321add66",
        sk=priv_validator_path,
        config={},
    )

    with caplog.at_level(logging.ERROR):
        assert not run_election_new_upsert_validator(args, b, test_abci_rpc)
        assert caplog.records[0].msg.__class__ == InvalidPowerChange


@pytest.mark.abci
def test_election_approve_with_tendermint(b, priv_validator_path, user_sk, validators, test_abci_rpc):
    public_key = "CJxdItf4lz2PwEf4SmYNAu/c/VpmX39JEgC5YpH7fxg="
    new_args = Namespace(
        action="new",
        election_type="upsert-validator",
        public_key=public_key,
        power=1,
        node_id="fb7140f03a4ffad899fabbbf655b97e0321add66",
        sk=priv_validator_path,
        config={},
    )

    election_id = run_election_new_upsert_validator(new_args, b, test_abci_rpc)
    assert election_id

    args = Namespace(action="approve", election_id=election_id, sk=priv_validator_path, config={})
    approve = run_election_approve(args, b, test_abci_rpc)

    assert b.models.get_transaction(approve)


@pytest.mark.bdb
def test_election_approve_without_tendermint(monkeypatch, caplog, b, priv_validator_path, new_validator, node_key, test_abci_rpc):
    from planetmint.commands.planetmint import run_election_approve
    from argparse import Namespace

    b, election_id = call_election(monkeypatch, b, new_validator, node_key, test_abci_rpc)

    # call run_election_approve with args that point to the election
    args = Namespace(action="approve", election_id=election_id, sk=priv_validator_path, config={})

    # assert returned id is in the db
    with caplog.at_level(logging.INFO):
        approval_id = run_election_approve(args, b, test_abci_rpc)
        assert caplog.records[0].msg == "[SUCCESS] Your vote has been submitted"
        assert b.models.get_transaction(approval_id)



from unittest import mock
@pytest.mark.bdb
def test_election_approve_failure(monkeypatch, caplog, b, priv_validator_path, new_validator, node_key, test_abci_rpc):
    from argparse import Namespace

    b, election_id = call_election(monkeypatch, b, new_validator, node_key, test_abci_rpc)

    def mock_write(modelist, endpoint, mode_commit, transaction, mode):
        b.models.store_bulk_transactions([transaction])
        return (400, "")

    test_abci_rpc.write_transaction = mock_write

    # call run_upsert_validator_approve with args that point to the election
    args = Namespace(action="approve", election_id=election_id, sk=priv_validator_path, config={})

    with caplog.at_level(logging.ERROR):
        assert not run_election_approve(args, b, test_abci_rpc)
        assert caplog.records[0].msg == "Failed to commit vote"


def test_bigchain_tendermint_version(capsys):
    from planetmint.commands.planetmint import run_tendermint_version

    args = Namespace(config=None)
    _, _ = capsys.readouterr()
    run_tendermint_version(args)
    output_config = json.loads(capsys.readouterr()[0])
    from planetmint.version import __tm_supported_versions__

    assert len(output_config["tendermint"]) == len(__tm_supported_versions__)
    assert sorted(output_config["tendermint"]) == sorted(__tm_supported_versions__)



def call_election(monkeypatch, b, new_validator, node_key, abci_rpc):

    def mock_write(self, modelist, endpoint, mode_commit, transaction, mode):
        b.models.store_bulk_transactions([transaction])
        return (202, "")
    with monkeypatch.context() as m:
        m.setattr("planetmint.model.dataaccessor.DataAccessor.get_validators", mock_get_validators)
        m.setattr("planetmint.abci.rpc.ABCI_RPC.write_transaction", mock_write)
        
        # patch the validator set. We now have one validator with power 10
        #b.models.get_validators = mock_get_validators
        #abci_rpc.write_transaction = mock_write

        # our voters is a list of length 1, populated from our mocked validator
        voters = b.get_recipients_list()
        # and our voter is the public key from the voter list
        voter = node_key.public_key
        valid_election = ValidatorElection.generate([voter], voters, new_validator, None).sign([node_key.private_key])

        # patch in an election with a vote issued to the user
        election_id = valid_election.id
        b.models.store_bulk_transactions([valid_election])
        
        m.undo()
        return b, election_id
