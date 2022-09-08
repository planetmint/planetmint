import logging

import tarantool
from planetmint.config import Config
from planetmint.backend.utils import module_dispatch_registrar
from planetmint import backend
from planetmint.backend.tarantool.connection import TarantoolDBConnection

logger = logging.getLogger(__name__)
register_schema = module_dispatch_registrar(backend.schema)

SPACE_NAMES = (
    "abci_chains",
    "assets",
    "blocks",
    "blocks_tx",
    "elections",
    "meta_data",
    "pre_commits",
    "validators",
    "transactions",
    "inputs",
    "outputs",
    "keys",
    "utxos",
    "scripts",
)


SPACE_COMMANDS = {
    "abci_chains": "abci_chains = box.schema.space.create('abci_chains', {engine='memtx', is_sync = false})",
    "assets": "assets = box.schema.space.create('assets' , {engine='memtx' , is_sync=false})",
    "blocks": "blocks = box.schema.space.create('blocks' , {engine='memtx' , is_sync=false})",
    "blocks_tx": "blocks_tx = box.schema.space.create('blocks_tx')",
    "elections": "elections = box.schema.space.create('elections',{engine = 'memtx' , is_sync = false})",
    "meta_data": "meta_datas = box.schema.space.create('meta_data',{engine = 'memtx' , is_sync = false})",
    "pre_commits": "pre_commits = box.schema.space.create('pre_commits' , {engine='memtx' , is_sync=false})",
    "validators": "validators = box.schema.space.create('validators' , {engine = 'memtx' , is_sync = false})",
    "transactions": "transactions = box.schema.space.create('transactions',{engine='memtx' , is_sync=false})",
    "inputs": "inputs = box.schema.space.create('inputs')",
    "outputs": "outputs = box.schema.space.create('outputs')",
    "keys": "keys = box.schema.space.create('keys')",
    "utxos": "utxos = box.schema.space.create('utxos', {engine = 'memtx' , is_sync = false})",
    "scripts": "scripts = box.schema.space.create('scripts', {engine = 'memtx' , is_sync = false})",
}

INDEX_COMMANDS = {
    "abci_chains": {
        "id_search": "abci_chains:create_index('id_search' ,{type='tree', parts={'id'}})",
        "height_search": "abci_chains:create_index('height_search' ,{type='tree', unique=false, parts={'height'}})",
    },
    "assets": {
        "txid_search": "assets:create_index('txid_search', {type='tree', parts={'tx_id'}})",
        "assetid_search": "assets:create_index('assetid_search', {type='tree',unique=false, parts={'asset_id', 'tx_id'}})",  # noqa: E501
        "only_asset_search": "assets:create_index('only_asset_search', {type='tree', unique=false, parts={'asset_id'}})",  # noqa: E501
        "text_search": "assets:create_index('secondary', {unique=false,parts={1,'string'}})",
    },
    "blocks": {
        "id_search": "blocks:create_index('id_search' , {type='tree' , parts={'block_id'}})",
        "block_search": "blocks:create_index('block_search' , {type='tree', unique = false, parts={'height'}})",
        "block_id_search": "blocks:create_index('block_id_search', {type = 'hash', parts ={'block_id'}})",
    },
    "blocks_tx": {
        "id_search": "blocks_tx:create_index('id_search',{ type = 'tree', parts={'transaction_id'}})",
        "block_search": "blocks_tx:create_index('block_search', {type = 'tree',unique=false, parts={'block_id'}})",
    },
    "elections": {
        "id_search": "elections:create_index('id_search' , {type='tree', parts={'election_id'}})",
        "height_search": "elections:create_index('height_search' , {type='tree',unique=false, parts={'height'}})",
        "update_search": "elections:create_index('update_search', {type='tree', unique=false, parts={'election_id', 'height'}})",  # noqa: E501
    },
    "meta_data": {
        "id_search": "meta_datas:create_index('id_search', { type='tree' , parts={'transaction_id'}})",
        "text_search": "meta_datas:create_index('secondary', {unique=false,parts={2,'string'}})",
    },
    "pre_commits": {
        "id_search": "pre_commits:create_index('id_search', {type ='tree' , parts={'commit_id'}})",
        "height_search": "pre_commits:create_index('height_search', {type ='tree',unique=true, parts={'height'}})",
    },
    "validators": {
        "id_search": "validators:create_index('id_search' , {type='tree' , parts={'validator_id'}})",
        "height_search": "validators:create_index('height_search' , {type='tree', unique=true, parts={'height'}})",
    },
    "transactions": {
        "id_search": "transactions:create_index('id_search' , {type = 'tree' , parts={'transaction_id'}})",
        "transaction_search": "transactions:create_index('transaction_search' , {type = 'tree',unique=false, parts={'operation', 'transaction_id'}})",  # noqa: E501
    },
    "inputs": {
        "delete_search": "inputs:create_index('delete_search' , {type = 'tree', parts={'input_id'}})",
        "spent_search": "inputs:create_index('spent_search' , {type = 'tree', unique=false, parts={'fulfills_transaction_id', 'fulfills_output_index'}})",  # noqa: E501
        "id_search": "inputs:create_index('id_search', {type = 'tree', unique=false, parts = {'transaction_id'}})",
    },
    "outputs": {
        "unique_search": "outputs:create_index('unique_search' ,{type='tree', parts={'output_id'}})",
        "id_search": "outputs:create_index('id_search' ,{type='tree', unique=false, parts={'transaction_id'}})",
    },
    "keys": {
        "id_search": "keys:create_index('id_search', {type = 'tree', parts={'id'}})",
        "keys_search": "keys:create_index('keys_search', {type = 'tree', unique=false, parts={'public_key'}})",
        "txid_search": "keys:create_index('txid_search', {type = 'tree', unique=false, parts={'transaction_id'}})",
        "output_search": "keys:create_index('output_search', {type = 'tree', unique=false, parts={'output_id'}})",
    },
    "utxos": {
        "id_search": "utxos:create_index('id_search', {type='tree' , parts={'transaction_id', 'output_index'}})",
        "transaction_search": "utxos:create_index('transaction_search', {type='tree', unique=false, parts={'transaction_id'}})",  # noqa: E501
        "index_Search": "utxos:create_index('index_search', {type='tree', unique=false, parts={'output_index'}})",
    },
    "scripts": {
        "txid_search": "scripts:create_index('txid_search', {type='tree', parts={'transaction_id'}})",
    },
}


SCHEMA_COMMANDS = {
    "abci_chains": "abci_chains:format({{name='height' , type='integer'},{name='is_synched' , type='boolean'},{name='chain_id',type='string'}, {name='id', type='string'}})",  # noqa: E501
    "assets": "assets:format({{name='data' , type='string'}, {name='tx_id', type='string'}, {name='asset_id', type='string'}})",  # noqa: E501
    "blocks": "blocks:format{{name='app_hash',type='string'},{name='height' , type='integer'},{name='block_id' , type='string'}}",  # noqa: E501
    "blocks_tx": "blocks_tx:format{{name='transaction_id', type = 'string'}, {name = 'block_id', type = 'string'}}",
    "elections": "elections:format({{name='election_id' , type='string'},{name='height' , type='integer'}, {name='is_concluded' , type='boolean'}})",  # noqa: E501
    "meta_data": "meta_datas:format({{name='transaction_id' , type='string'}, {name='meta_data' , type='string'}})",  # noqa: E501
    "pre_commits": "pre_commits:format({{name='commit_id', type='string'}, {name='height',type='integer'}, {name='transactions',type=any}})",  # noqa: E501
    "validators": "validators:format({{name='validator_id' , type='string'},{name='height',type='integer'},{name='validators' , type='any'}})",  # noqa: E501
    "transactions": "transactions:format({{name='transaction_id' , type='string'}, {name='operation' , type='string'}, {name='version' ,type='string'}, {name='dict_map', type='any'}})",  # noqa: E501
    "inputs": "inputs:format({{name='transaction_id' , type='string'}, {name='fulfillment' , type='any'}, {name='owners_before' , type='array'}, {name='fulfills_transaction_id', type = 'string'}, {name='fulfills_output_index', type = 'string'}, {name='input_id', type='string'}, {name='input_index', type='number'}})",  # noqa: E501
    "outputs": "outputs:format({{name='transaction_id' , type='string'}, {name='amount' , type='string'}, {name='uri', type='string'}, {name='details_type', type='string'}, {name='details_public_key', type='any'}, {name = 'output_id', type = 'string'}, {name='treshold', type='any'}, {name='subconditions', type='any'}, {name='output_index', type='number'}})",  # noqa: E501
    "keys": "keys:format({{name = 'id', type='string'}, {name = 'transaction_id', type = 'string'} ,{name = 'output_id', type = 'string'}, {name = 'public_key', type = 'string'}, {name = 'key_index', type = 'integer'}})",  # noqa: E501
    "utxos": "utxos:format({{name='transaction_id' , type='string'}, {name='output_index' , type='integer'}, {name='utxo_dict', type='string'}})",  # noqa: E501
    "scripts": "scripts:format({{name='transaction_id', type='string'},{name='script' , type='any'}})",  # noqa: E501
}

SCHEMA_DROP_COMMANDS = {
    "abci_chains": "box.space.abci_chains:drop()",
    "assets": "box.space.assets:drop()",
    "blocks": "box.space.blocks:drop()",
    "blocks_tx": "box.space.blocks_tx:drop()",
    "elections": "box.space.elections:drop()",
    "meta_data": "box.space.meta_data:drop()",
    "pre_commits": "box.space.pre_commits:drop()",
    "validators": "box.space.validators:drop()",
    "transactions": "box.space.transactions:drop()",
    "inputs": "box.space.inputs:drop()",
    "outputs": "box.space.outputs:drop()",
    "keys": "box.space.keys:drop()",
    "utxos": "box.space.utxos:drop()",
    "scripts": "box.space.scripts:drop()",
}


@register_schema(TarantoolDBConnection)
def drop_database(connection, not_used=None):
    for _space in SPACE_NAMES:
        try:
            cmd = SCHEMA_DROP_COMMANDS[_space].encode()
            run_command_with_output(command=cmd)
            print(f"Space '{_space}' was dropped succesfuly.")
        except Exception:
            print(f"Unexpected error while trying to drop space '{_space}'")


@register_schema(TarantoolDBConnection)
def create_database(connection, dbname):
    """

    For tarantool implementation, this function runs
    create_tables, to initiate spaces, schema and indexes.

    """
    logger.info("Create database `%s`.", dbname)


def run_command_with_output(command):
    from subprocess import run

    host_port = "%s:%s" % (
        Config().get()["database"]["host"],
        Config().get()["database"]["port"],
    )
    output = run(["tarantoolctl", "connect", host_port], input=command, capture_output=True)
    if output.returncode != 0:
        raise Exception(f"Error while trying to execute cmd {command} on host:port {host_port}: {output.stderr}")
    return output.stdout


@register_schema(TarantoolDBConnection)
def create_tables(connection, dbname):
    for _space in SPACE_NAMES:
        try:
            cmd = SPACE_COMMANDS[_space].encode()
            run_command_with_output(command=cmd)
            print(f"Space '{_space}' created.")
        except Exception as err:
            print(f"Unexpected error while trying to create '{_space}': {err}")
        create_schema(space_name=_space)
        create_indexes(space_name=_space)


def create_indexes(space_name):
    indexes = INDEX_COMMANDS[space_name]
    for index_name, index_cmd in indexes.items():
        try:
            run_command_with_output(command=index_cmd.encode())
            print(f"Index '{index_name}' created succesfully.")
        except Exception as err:
            print(f"Unexpected error while trying to create index '{index_name}': '{err}'")


def create_schema(space_name):
    try:
        cmd = SCHEMA_COMMANDS[space_name].encode()
        run_command_with_output(command=cmd)
        print(f"Schema created for {space_name} succesfully.")
    except Exception as unexpected_error:
        print(f"Got unexpected error when creating index for '{space_name}' Space.\n {unexpected_error}")
