# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

"""Query implementation for Tarantool"""
import logging
from uuid import uuid4
from operator import itemgetter
from typing import Union


from planetmint.backend import query
from planetmint.backend.models.dbtransaction import DbTransaction
from planetmint.backend.exceptions import OperationDataInsertionError
from planetmint.exceptions import CriticalDoubleSpend
from planetmint.backend.exceptions import DBConcurrencyError
from planetmint.backend.tarantool.const import (
    TARANT_TABLE_TRANSACTION,
    TARANT_TABLE_OUTPUT,
    TARANT_TABLE_SCRIPT,
    TARANT_TX_ID_SEARCH,
    TARANT_ID_SEARCH,
    TARANT_INDEX_TX_BY_ASSET_ID,
    TARANT_INDEX_SPENDING_BY_ID_AND_OUTPUT_INDEX,
    TARANT_TABLE_GOVERNANCE,
    TARANT_TABLE_ABCI_CHAINS,
    TARANT_TABLE_BLOCKS,
    TARANT_TABLE_VALIDATOR_SETS,
    TARANT_TABLE_UTXOS,
    TARANT_TABLE_PRE_COMMITS,
    TARANT_TABLE_ELECTIONS,
)
from planetmint.backend.utils import module_dispatch_registrar
from planetmint.backend.models import Asset, Block, Output
from planetmint.backend.tarantool.sync_io.connection import TarantoolDBConnection
from transactions.common.transaction import Transaction

logger = logging.getLogger(__name__)
register_query = module_dispatch_registrar(query)

from tarantool.error import OperationalError, NetworkError, SchemaError
from functools import wraps


def catch_db_exception(function_to_decorate):
    @wraps(function_to_decorate)
    def wrapper(*args, **kw):
        try:
            output = function_to_decorate(*args, **kw)
        except OperationalError as op_error:
            raise op_error
        except SchemaError as schema_error:
            raise schema_error
        except NetworkError as net_error:
            raise net_error
        except ValueError as e:
            logger.info(f"ValueError in Query/DB instruction: {e}: raising DBConcurrencyError")
            raise DBConcurrencyError
        except AttributeError as e:
            logger.info(f"Attribute in Query/DB instruction: {e}: raising DBConcurrencyError")
            raise DBConcurrencyError
        except Exception as e:
            logger.info(f"Could not insert transactions: {e}")
            if e.args[0] == 3 and e.args[1].startswith("Duplicate key exists in"):
                raise CriticalDoubleSpend()
            else:
                raise OperationDataInsertionError()
        return output

    return wrapper


@register_query(TarantoolDBConnection)
def get_complete_transactions_by_ids(connection, txids: list) -> list[DbTransaction]:
    _transactions = []
    for txid in txids:
        tx = get_transaction_by_id(connection, txid, TARANT_TABLE_TRANSACTION)
        if tx is None:
            tx = get_transaction_by_id(connection, txid, TARANT_TABLE_GOVERNANCE)
        if tx is None:
            continue
        outputs = get_outputs_by_tx_id(connection, txid)
        tx.outputs = outputs
        _transactions.append(tx)
    return _transactions


@register_query(TarantoolDBConnection)
@catch_db_exception
def get_outputs_by_tx_id(connection, tx_id: str) -> list[Output]:
    _outputs = connection.connect().select(TARANT_TABLE_OUTPUT, tx_id, index=TARANT_TX_ID_SEARCH).data
    _sorted_outputs = sorted(_outputs, key=itemgetter(4))
    return [Output.from_tuple(output) for output in _sorted_outputs]


@register_query(TarantoolDBConnection)
def get_transaction(connection, tx_id: str) -> Union[DbTransaction, None]:
    transactions = get_complete_transactions_by_ids(connection, (tx_id))
    if len(transactions) > 1 or len(transactions) == 0:
        return None
    else:
        return transactions[0]


@register_query(TarantoolDBConnection)
@catch_db_exception
def get_transactions_by_asset(connection, asset: str, limit: int = 1000) -> list[DbTransaction]:
    txs = (
        connection.connect()
        .select(TARANT_TABLE_TRANSACTION, asset, limit=limit, index="transactions_by_asset_cid")
        .data
    )
    tx_ids = [tx[0] for tx in txs]
    return get_complete_transactions_by_ids(connection, tx_ids)


@register_query(TarantoolDBConnection)
@catch_db_exception
def get_transactions_by_metadata(connection, metadata: str, limit: int = 1000) -> list[DbTransaction]:
    txs = (
        connection.connect()
        .select(TARANT_TABLE_TRANSACTION, metadata, limit=limit, index="transactions_by_metadata_cid")
        .data
    )
    tx_ids = [tx[0] for tx in txs]
    return get_complete_transactions_by_ids(connection, tx_ids)


@catch_db_exception
def store_transaction_outputs(connection, output: Output, index: int) -> str:
    output_id = uuid4().hex
    connection.connect().insert(
        TARANT_TABLE_OUTPUT,
        (
            output_id,
            int(output.amount),
            output.public_keys,
            output.condition.to_dict(),
            index,
            output.transaction_id,
        ),
    ).data
    return output_id


@register_query(TarantoolDBConnection)
def store_transactions(connection, signed_transactions: list, table=TARANT_TABLE_TRANSACTION):
    for transaction in signed_transactions:
        store_transaction(connection, transaction, table)
        [
            store_transaction_outputs(connection, Output.outputs_dict(output, transaction["id"]), index)
            for index, output in enumerate(transaction[TARANT_TABLE_OUTPUT])
        ]


@register_query(TarantoolDBConnection)
@catch_db_exception
def store_transaction(connection, transaction, table=TARANT_TABLE_TRANSACTION):
    scripts = None
    if TARANT_TABLE_SCRIPT in transaction:
        scripts = transaction[TARANT_TABLE_SCRIPT]
    asset_obj = Transaction.get_assets_tag(transaction["version"])
    if transaction["version"] == "2.0":
        asset_array = [transaction[asset_obj]]
    else:
        asset_array = transaction[asset_obj]
    tx = (
        transaction["id"],
        transaction["operation"],
        transaction["version"],
        transaction["metadata"],
        asset_array,
        transaction["inputs"],
        scripts,
    )
    connection.connect().insert(table, tx)


@register_query(TarantoolDBConnection)
@catch_db_exception
def get_transaction_by_id(connection, transaction_id, table=TARANT_TABLE_TRANSACTION):
    txs = connection.connect().select(table, transaction_id, index=TARANT_ID_SEARCH)
    if len(txs) == 0:
        return None
    return DbTransaction.from_tuple(txs[0])


@register_query(TarantoolDBConnection)
def get_transaction_single(connection, transaction_id) -> Union[DbTransaction, None]:
    txs = get_complete_transactions_by_ids(txids=[transaction_id], connection=connection)
    return txs[0] if len(txs) == 1 else None


@register_query(TarantoolDBConnection)
def get_transactions(connection, transactions_ids: list) -> list[DbTransaction]:
    return get_complete_transactions_by_ids(txids=transactions_ids, connection=connection)


@register_query(TarantoolDBConnection)
@catch_db_exception
def get_asset(connection, asset_id: str) -> Asset:
    connection.connect().select(TARANT_TABLE_TRANSACTION, asset_id, index=TARANT_INDEX_TX_BY_ASSET_ID).data
    return Asset.from_dict(_data[0])


@register_query(TarantoolDBConnection)
@catch_db_exception
def get_assets(connection, assets_ids: list) -> list[Asset]:
    _returned_data = []
    for _id in list(set(assets_ids)):
        res = connection.connect().select(TARANT_TABLE_TRANSACTION, _id, index=TARANT_INDEX_TX_BY_ASSET_ID).data
        if len(res) == 0:
            continue
        _returned_data.append(res[0])

    sorted_assets = sorted(_returned_data, key=lambda k: k[1], reverse=False)
    return [Asset.from_dict(asset) for asset in sorted_assets]


@register_query(TarantoolDBConnection)
@catch_db_exception
def get_spent(connection, fullfil_transaction_id: str, fullfil_output_index: str) -> list[DbTransaction]:
    _inputs = (
        connection.connect()
        .select(
            TARANT_TABLE_TRANSACTION,
            [fullfil_transaction_id, fullfil_output_index],
            index=TARANT_INDEX_SPENDING_BY_ID_AND_OUTPUT_INDEX,
        )
        .data
    )
    return get_complete_transactions_by_ids(txids=[inp[0] for inp in _inputs], connection=connection)


@register_query(TarantoolDBConnection)
@catch_db_exception
def get_latest_block(connection) -> Union[dict, None]:
    blocks = connection.connect().select(TARANT_TABLE_BLOCKS).data
    if not blocks:
        return None

    blocks = sorted(blocks, key=itemgetter(2), reverse=True)
    latest_block = Block.from_tuple(blocks[0])
    return latest_block.to_dict()


@register_query(TarantoolDBConnection)
@catch_db_exception
def store_block(connection, block: dict):
    block_unique_id = uuid4().hex
    connection.connect().insert(
        TARANT_TABLE_BLOCKS, (block_unique_id, block["app_hash"], block["height"], block[TARANT_TABLE_TRANSACTION])
    )


@register_query(TarantoolDBConnection)
@catch_db_exception
def get_txids_filtered(connection, asset_ids: list[str], operation: str = "", last_tx: bool = False) -> list[str]:
    transactions = []
    if operation == "CREATE":
        transactions = (
            connection.connect()
            .select(TARANT_TABLE_TRANSACTION, [asset_ids[0], operation], index="transactions_by_id_and_operation")
            .data
        )
    elif operation == "TRANSFER":
        transactions = (
            connection.connect().select(TARANT_TABLE_TRANSACTION, asset_ids, index=TARANT_INDEX_TX_BY_ASSET_ID).data
        )
    else:
        txs = connection.connect().select(TARANT_TABLE_TRANSACTION, asset_ids, index=TARANT_ID_SEARCH).data
        asset_txs = (
            connection.connect().select(TARANT_TABLE_TRANSACTION, asset_ids, index=TARANT_INDEX_TX_BY_ASSET_ID).data
        )
        transactions = txs + asset_txs

    ids = tuple([tx[0] for tx in transactions])

    # NOTE: check when and where this is used and remove if not
    if last_tx:
        return ids[0]

    return ids


@register_query(TarantoolDBConnection)
@catch_db_exception
def get_owned_ids(connection, owner: str) -> list[DbTransaction]:
    outputs = connection.connect().select(TARANT_TABLE_OUTPUT, owner, index="public_keys").data
    if len(outputs) == 0:
        return []
    txids = [output[5] for output in outputs]
    unique_set_txids = set(txids)
    return get_complete_transactions_by_ids(connection, unique_set_txids)


@register_query(TarantoolDBConnection)
def get_spending_transactions(connection, inputs):
    _transactions = []

    for inp in inputs:
        _trans_list = get_spent(
            fullfil_transaction_id=inp["transaction_id"],
            fullfil_output_index=inp["output_index"],
            connection=connection,
        )
        _transactions.extend(_trans_list)

    return _transactions


@register_query(TarantoolDBConnection)
@catch_db_exception
def get_block(connection, block_id=None) -> Union[dict, None]:
    _block = connection.connect().select(TARANT_TABLE_BLOCKS, block_id, index="height", limit=1).data
    if len(_block) == 0:
        return
    _block = Block.from_tuple(_block[0])
    return _block.to_dict()


@register_query(TarantoolDBConnection)
@catch_db_exception
def get_block_with_transaction(connection, txid: str) -> Union[dict, None]:
    _block = connection.connect().select(TARANT_TABLE_BLOCKS, txid, index="block_by_transaction_id").data
    if len(_block) == 0:
        return
    _block = Block.from_tuple(_block[0])
    return _block.to_dict()


@register_query(TarantoolDBConnection)
@catch_db_exception
def delete_transactions(connection, txn_ids: list):
    for _id in txn_ids:
        _outputs = get_outputs_by_tx_id(connection, _id)
        for x in range(len(_outputs)):
            connection.connect().call("delete_output", (_outputs[x].id))
    for _id in txn_ids:
        connection.connect().delete(TARANT_TABLE_TRANSACTION, _id)
        connection.connect().delete(TARANT_TABLE_GOVERNANCE, _id)


@register_query(TarantoolDBConnection)
@catch_db_exception
def store_unspent_outputs(connection, *unspent_outputs: list):
    result = []
    if unspent_outputs:
        for utxo in unspent_outputs:
            try:
                output = (
                    connection.connect()
                    .insert(TARANT_TABLE_UTXOS, (uuid4().hex, utxo["transaction_id"], utxo["output_index"], utxo))
                    .data
                )
                result.append(output)
            except Exception as e:
                logger.info(f"Could not insert unspent output: {e}")
                raise OperationDataInsertionError()
    return result


@register_query(TarantoolDBConnection)
@catch_db_exception
def delete_unspent_outputs(connection, *unspent_outputs: list):
    result = []
    if unspent_outputs:
        for utxo in unspent_outputs:
            output = (
                connection.connect()
                .delete(
                    TARANT_TABLE_UTXOS,
                    (utxo["transaction_id"], utxo["output_index"]),
                    index="utxo_by_transaction_id_and_output_index",
                )
                .data
            )
            result.append(output)
    return result


@register_query(TarantoolDBConnection)
@catch_db_exception
def get_unspent_outputs(connection, query=None):  # for now we don't have implementation for 'query'.
    _utxos = connection.connect().select(TARANT_TABLE_UTXOS, []).data
    return [utx[3] for utx in _utxos]


@register_query(TarantoolDBConnection)
@catch_db_exception
def store_pre_commit_state(connection, state: dict):
    _precommit = connection.connect().select(TARANT_TABLE_PRE_COMMITS, [], limit=1).data
    _precommitTuple = (
        (uuid4().hex, state["height"], state[TARANT_TABLE_TRANSACTION])
        if _precommit is None or len(_precommit) == 0
        else _precommit[0]
    )
    connection.connect().upsert(
        TARANT_TABLE_PRE_COMMITS,
        _precommitTuple,
        op_list=[("=", 1, state["height"]), ("=", 2, state[TARANT_TABLE_TRANSACTION])],
    )


@register_query(TarantoolDBConnection)
@catch_db_exception
def get_pre_commit_state(connection) -> dict:
    _commit = connection.connect().select(TARANT_TABLE_PRE_COMMITS, [], index=TARANT_ID_SEARCH).data
    if _commit is None or len(_commit) == 0:
        return None
    _commit = sorted(_commit, key=itemgetter(1), reverse=False)[0]
    return {"height": _commit[1], TARANT_TABLE_TRANSACTION: _commit[2]}


@register_query(TarantoolDBConnection)
@catch_db_exception
def store_validator_set(conn, validators_update: dict):
    _validator = (
        conn.connect().select(TARANT_TABLE_VALIDATOR_SETS, validators_update["height"], index="height", limit=1).data
    )
    unique_id = uuid4().hex if _validator is None or len(_validator) == 0 else _validator[0][0]
    conn.connect().upsert(
        TARANT_TABLE_VALIDATOR_SETS,
        (unique_id, validators_update["height"], validators_update["validators"]),
        op_list=[("=", 1, validators_update["height"]), ("=", 2, validators_update["validators"])],
    )


@register_query(TarantoolDBConnection)
@catch_db_exception
def delete_validator_set(connection, height: int):
    _validators = connection.connect().select(TARANT_TABLE_VALIDATOR_SETS, height, index="height").data
    for _valid in _validators:
        connection.connect().delete(TARANT_TABLE_VALIDATOR_SETS, _valid[0])


@register_query(TarantoolDBConnection)
@catch_db_exception
def store_election(connection, election_id: str, height: int, is_concluded: bool):
    connection.connect().upsert(
        TARANT_TABLE_ELECTIONS, (election_id, height, is_concluded), op_list=[("=", 1, height), ("=", 2, is_concluded)]
    )


@register_query(TarantoolDBConnection)
@catch_db_exception
def store_elections(connection, elections: list):
    for election in elections:
        _election = connection.connect().insert(
            TARANT_TABLE_ELECTIONS, (election["election_id"], election["height"], election["is_concluded"])
        )


@register_query(TarantoolDBConnection)
@catch_db_exception
def delete_elections(connection, height: int):
    _elections = connection.connect().select(TARANT_TABLE_ELECTIONS, height, index="height").data
    for _elec in _elections:
        connection.connect().delete(TARANT_TABLE_ELECTIONS, _elec[0])


@register_query(TarantoolDBConnection)
@catch_db_exception
def get_validator_set(connection, height: int = None):
    _validators = connection.connect().select(TARANT_TABLE_VALIDATOR_SETS).data
    if height is not None and _validators is not None:
        _validators = [
            {"height": validator[1], "validators": validator[2]} for validator in _validators if validator[1] <= height
        ]
        return next(iter(sorted(_validators, key=lambda k: k["height"], reverse=True)), None)
    elif _validators is not None:
        _validators = [{"height": validator[1], "validators": validator[2]} for validator in _validators]
        return next(iter(sorted(_validators, key=lambda k: k["height"], reverse=True)), None)
    return None


@register_query(TarantoolDBConnection)
@catch_db_exception
def get_election(connection, election_id: str) -> dict:
    _elections = connection.connect().select(TARANT_TABLE_ELECTIONS, election_id, index=TARANT_ID_SEARCH).data
    if _elections is None or len(_elections) == 0:
        return None
    _election = sorted(_elections, key=itemgetter(0), reverse=True)[0]
    return {"election_id": _election[0], "height": _election[1], "is_concluded": _election[2]}


@register_query(TarantoolDBConnection)
@catch_db_exception
def get_asset_tokens_for_public_key(connection, asset_id: str, public_key: str) -> list[DbTransaction]:
    id_transactions = connection.connect().select(TARANT_TABLE_GOVERNANCE, [asset_id]).data
    asset_id_transactions = (
        connection.connect().select(TARANT_TABLE_GOVERNANCE, [asset_id], index="governance_by_asset_id").data
    )

    transactions = id_transactions + asset_id_transactions
    return get_complete_transactions_by_ids(connection, [_tx[0] for _tx in transactions])


@register_query(TarantoolDBConnection)
@catch_db_exception
def store_abci_chain(connection, height: int, chain_id: str, is_synced: bool = True):
    connection.connect().upsert(
        TARANT_TABLE_ABCI_CHAINS,
        (chain_id, height, is_synced),
        op_list=[("=", 0, chain_id), ("=", 1, height), ("=", 2, is_synced)],
    )


@register_query(TarantoolDBConnection)
@catch_db_exception
def delete_abci_chain(connection, height: int):
    chains = connection.connect().select(TARANT_TABLE_ABCI_CHAINS, height, index="height")
    connection.connect().delete(TARANT_TABLE_ABCI_CHAINS, chains[0][0], index="id")


@register_query(TarantoolDBConnection)
@catch_db_exception
def get_latest_abci_chain(connection) -> Union[dict, None]:
    _all_chains = connection.connect().select(TARANT_TABLE_ABCI_CHAINS).data
    if _all_chains is None or len(_all_chains) == 0:
        return None
    _chain = sorted(_all_chains, key=itemgetter(1), reverse=True)[0]
    return {"chain_id": _chain[0], "height": _chain[1], "is_synced": _chain[2]}
