# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

"""Implementation of the `planetmint` command,
the command-line interface (CLI) for Planetmint Server.
"""

import os
import logging
import argparse
import json
import sys
import planetmint


from transactions.common.transaction_mode_types import BROADCAST_TX_COMMIT
from transactions.common.exceptions import DatabaseDoesNotExist, ValidationError
from transactions.types.elections.vote import Vote
from transactions.types.elections.chain_migration_election import ChainMigrationElection
from transactions.types.elections.validator_utils import election_id_to_public_key
from transactions.types.elections.validator_election import ValidatorElection
from transactions.common.transaction import Transaction


from planetmint.application.validator import Validator
from planetmint.backend import schema
from planetmint.commands import utils
from planetmint.commands.utils import configure_planetmint, input_on_stderr
from planetmint.config_utils import setup_logging
from planetmint.abci.rpc import MODE_COMMIT, MODE_LIST
from planetmint.abci.utils import load_node_key, public_key_from_base64
from planetmint.commands.election_types import elections
from planetmint.version import __tm_supported_versions__
from planetmint.config import Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Note about printing:
#   We try to print to stdout for results of a command that may be useful to
#   someone (or another program). Strictly informational text, or errors,
#   should be printed to stderr.


@configure_planetmint
def run_show_config(args):
    """Show the current configuration"""
    # TODO Proposal: remove the "hidden" configuration. Only show config. If
    # the system needs to be configured, then display information on how to
    # configure the system.
    _config = Config().get()
    del _config["CONFIGURED"]
    print(json.dumps(_config, indent=4, sort_keys=True))


@configure_planetmint
def run_configure(args):
    """Run a script to configure the current node."""
    config_path = args.config or planetmint.config_utils.CONFIG_DEFAULT_PATH

    config_file_exists = False
    # if the config path is `-` then it's stdout
    if config_path != "-":
        config_file_exists = os.path.exists(config_path)

    if config_file_exists and not args.yes:
        want = input_on_stderr(
            "Config file `{}` exists, do you want to " "override it? (cannot be undone) [y/N]: ".format(config_path)
        )
        if want != "y":
            return

    Config().init_config(args.backend)
    conf = Config().get()
    # select the correct config defaults based on the backend
    print("Generating default configuration for backend {}".format(args.backend), file=sys.stderr)

    database_keys = Config().get_db_key_map(args.backend)
    if not args.yes:
        for key in ("bind",):
            val = conf["server"][key]
            conf["server"][key] = input_on_stderr("API Server {}? (default `{}`): ".format(key, val), val)

        for key in ("scheme", "host", "port"):
            val = conf["wsserver"][key]
            conf["wsserver"][key] = input_on_stderr("WebSocket Server {}? (default `{}`): ".format(key, val), val)

        for key in database_keys:
            val = conf["database"][key]
            conf["database"][key] = input_on_stderr("Database {}? (default `{}`): ".format(key, val), val)

        for key in ("host", "port"):
            val = conf["tendermint"][key]
            conf["tendermint"][key] = input_on_stderr("Tendermint {}? (default `{}`)".format(key, val), val)

    if config_path != "-":
        planetmint.config_utils.write_config(conf, config_path)
    else:
        print(json.dumps(conf, indent=4, sort_keys=True))

    Config().set(conf)
    print("Configuration written to {}".format(config_path), file=sys.stderr)
    print("Ready to go!", file=sys.stderr)


@configure_planetmint
def run_election(args):
    """Initiate and manage elections"""

    b = Validator()

    # Call the function specified by args.action, as defined above
    globals()[f"run_election_{args.action}"](args, b)


def run_election_new(args, planet):
    election_type = args.election_type.replace("-", "_")
    globals()[f"run_election_new_{election_type}"](args, planet)


def create_new_election(sk, planet, election_class, data, abci_rpc):
    try:
        key = load_node_key(sk)
        voters = planet.get_recipients_list()
        election = election_class.generate([key.public_key], voters, data, None).sign([key.private_key])
        planet.validate_election(election)
    except ValidationError as e:
        logger.error(e)
        return False
    except FileNotFoundError as fd_404:
        logger.error(fd_404)
        return False

    resp = abci_rpc.write_transaction(
        MODE_LIST, abci_rpc.tendermint_rpc_endpoint, MODE_COMMIT, election, BROADCAST_TX_COMMIT
    )
    if resp == (202, ""):
        logger.info("[SUCCESS] Submitted proposal with id: {}".format(election.id))
        return election.id
    else:
        logger.error("Failed to commit election proposal")
        return False


def run_election_new_upsert_validator(args, planet, abci_rpc):
    """Initiates an election to add/update/remove a validator to an existing Planetmint network

    :param args: dict
        args = {
        'public_key': the public key of the proposed peer, (str)
        'power': the proposed validator power for the new peer, (str)
        'node_id': the node_id of the new peer (str)
        'sk': the path to the private key of the node calling the election (str)
        }
    :param planet: an instance of Planetmint
    :return: election_id or `False` in case of failure
    """

    new_validator = [
        {
            "data": {
                "public_key": {"value": public_key_from_base64(args.public_key), "type": "ed25519-base16"},
                "power": args.power,
                "node_id": args.node_id,
            }
        }
    ]

    return create_new_election(args.sk, planet, ValidatorElection, new_validator, abci_rpc)


def run_election_new_chain_migration(args, planet, abci_rpc):
    """Initiates an election to halt block production

    :param args: dict
        args = {
        'sk': the path to the private key of the node calling the election (str)
        }
    :param planet: an instance of Planetmint
    :return: election_id or `False` in case of failure
    """

    return create_new_election(args.sk, planet, ChainMigrationElection, [{"data": {}}], abci_rpc)


def run_election_approve(args, validator: Validator, abci_rpc):
    """Approve an election

    :param args: dict
        args = {
        'election_id': the election_id of the election (str)
        'sk': the path to the private key of the signer (str)
        }
    :param planet: an instance of Planetmint
    :return: success log message or `False` in case of error
    """

    key = load_node_key(args.sk)
    tx = validator.models.get_transaction(args.election_id)
    voting_powers = [v.amount for v in tx.outputs if key.public_key in v.public_keys]
    if len(voting_powers) > 0:
        voting_power = voting_powers[0]
    else:
        logger.error("The key you provided does not match any of the eligible voters in this election.")
        return False

    tx_converted = Transaction.from_dict(tx.to_dict(), True)
    inputs = [i for i in tx_converted.to_inputs() if key.public_key in i.owners_before]
    election_pub_key = election_id_to_public_key(tx.id)
    approval = Vote.generate(inputs, [([election_pub_key], voting_power)], [tx.id]).sign([key.private_key])
    validator.validate_transaction(approval)

    resp = abci_rpc.write_transaction(
        MODE_LIST, abci_rpc.tendermint_rpc_endpoint, MODE_COMMIT, approval, BROADCAST_TX_COMMIT
    )

    if resp == (202, ""):
        logger.info("[SUCCESS] Your vote has been submitted")
        return approval.id
    else:
        logger.error("Failed to commit vote")
        return False


def run_election_show(args, validator: Validator):
    """Retrieves information about an election

    :param args: dict
        args = {
        'election_id': the transaction_id for an election (str)
        }
    :param planet: an instance of Planetmint
    """

    election = validator.models.get_transaction(args.election_id)
    if not election:
        logger.error(f"No election found with election_id {args.election_id}")
        return

    response = validator.show_election_status(election)

    logger.info(response)

    return response


def _run_init():
    validator = Validator()
    schema.init_database(validator.models.connection)


@configure_planetmint
def run_init(args):
    """Initialize the database"""
    _run_init()


@configure_planetmint
def run_drop(args):
    """Drop the database"""

    if not args.yes:
        response = input_on_stderr("Do you want to drop `{}` database? [y/n]: ")
        if response != "y":
            return

    from planetmint.backend.connection import Connection

    conn = Connection()
    try:
        schema.drop_database(conn)
    except DatabaseDoesNotExist:
        print("Drop was executed, but spaces doesn't exist.", file=sys.stderr)


@configure_planetmint
def run_start(args):
    """Start the processes to run the node"""
    logger.info("Planetmint Version %s", planetmint.version.__version__)

    # Configure Logging
    setup_logging()

    if not args.skip_initialize_database:
        logger.info("Initializing database")
        _run_init()

    validator = Validator()
    validator.rollback()
    del validator

    logger.info("Starting Planetmint main process.")
    from planetmint.start import start

    start(args)


def run_tendermint_version(args):
    """Show the supported Tendermint version(s)"""
    supported_tm_ver = {
        "description": "Planetmint supports the following Tendermint version(s)",
        "tendermint": __tm_supported_versions__,
    }
    print(json.dumps(supported_tm_ver, indent=4, sort_keys=True))


def create_parser():
    parser = argparse.ArgumentParser(description="Control your Planetmint node.", parents=[utils.base_parser])

    # all the commands are contained in the subparsers object,
    # the command selected by the user will be stored in `args.command`
    # that is used by the `main` function to select which other
    # function to call.
    subparsers = parser.add_subparsers(title="Commands", dest="command")

    # parser for writing a config file
    config_parser = subparsers.add_parser("configure", help="Prepare the config file.")

    config_parser.add_argument(
        "backend",
        choices=["tarantool_db", "localmongodb"],
        default="tarantool_db",
        const="tarantool_db",
        nargs="?",
        help="The backend to use. It can only be " '"tarantool_db", currently.',
    )

    # parser for managing elections
    election_parser = subparsers.add_parser("election", help="Manage elections.")

    election_subparser = election_parser.add_subparsers(title="Action", dest="action")

    new_election_parser = election_subparser.add_parser("new", help="Calls a new election.")

    new_election_subparser = new_election_parser.add_subparsers(title="Election_Type", dest="election_type")

    # Parser factory for each type of new election, so we get a bunch of commands that look like this:
    # election new <some_election_type> <args>...
    for name, data in elections.items():
        args = data["args"]
        generic_parser = new_election_subparser.add_parser(name, help=data["help"])
        for arg, kwargs in args.items():
            generic_parser.add_argument(arg, **kwargs)

    approve_election_parser = election_subparser.add_parser("approve", help="Approve the election.")
    approve_election_parser.add_argument("election_id", help="The election_id of the election.")
    approve_election_parser.add_argument(
        "--private-key", dest="sk", required=True, help="Path to the private key of the election initiator."
    )

    show_election_parser = election_subparser.add_parser("show", help="Provides information about an election.")

    show_election_parser.add_argument("election_id", help="The transaction id of the election you wish to query.")

    # parsers for showing/exporting config values
    subparsers.add_parser("show-config", help="Show the current configuration")

    # parser for database-level commands
    subparsers.add_parser("init", help="Init the database")

    subparsers.add_parser("drop", help="Drop the database")

    # parser for starting Planetmint
    start_parser = subparsers.add_parser("start", help="Start Planetmint")

    start_parser.add_argument(
        "--no-init",
        dest="skip_initialize_database",
        default=False,
        action="store_true",
        help="Skip database initialization",
    )

    subparsers.add_parser("tendermint-version", help="Show the Tendermint supported versions")

    start_parser.add_argument(
        "--experimental-parallel-validation",
        dest="experimental_parallel_validation",
        default=False,
        action="store_true",
        help="💀 EXPERIMENTAL: parallelize validation for better throughput 💀",
    )

    start_parser.add_argument(
        "--web-api-only",
        dest="web_api_only",
        default=False,
        action="store_true",
        help="💀 EXPERIMENTAL: seperate web API from ABCI server 💀",
    )
    start_parser.add_argument(
        "--abci-only",
        dest="abci_only",
        default=False,
        action="store_true",
        help="💀 EXPERIMENTAL: seperate web API from ABCI server 💀",
    )

    return parser


def main():
    utils.start(create_parser(), sys.argv[1:], globals())
