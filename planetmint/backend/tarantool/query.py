# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

"""Query implementation for Tarantool"""
import json
import logging
from uuid import uuid4
from operator import itemgetter
from typing import Union


from planetmint.backend import query
from planetmint.backend.models.dbtransaction import DbTransaction
from planetmint.backend.exceptions import OperationDataInsertionError
from planetmint.exceptions import CriticalDoubleSpend
from planetmint.backend.tarantool.const import (
    TARANT_TABLE_META_DATA,
    TARANT_TABLE_ASSETS,
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
from planetmint.backend.tarantool.connection import TarantoolDBConnection
from transactions.common.transaction import Transaction


logger = logging.getLogger(__name__)
register_query = module_dispatch_registrar(query)


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
def get_outputs_by_tx_id(connection, tx_id: str) -> list[Output]:
    _outputs = connection.run(connection.space(TARANT_TABLE_OUTPUT).select(tx_id, index=TARANT_TX_ID_SEARCH))
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
def get_transactions_by_asset(connection, asset: str, limit: int = 1000) -> list[DbTransaction]:
    txs = connection.run(
        connection.space(TARANT_TABLE_TRANSACTION).select(asset, limit=limit, index="transactions_by_asset_cid")
    )
    tx_ids = [tx[0] for tx in txs]
    return get_complete_transactions_by_ids(connection, tx_ids)


@register_query(TarantoolDBConnection)
def get_transactions_by_metadata(connection, metadata: str, limit: int = 1000) -> list[DbTransaction]:
    txs = connection.run(
        connection.space(TARANT_TABLE_TRANSACTION).select(metadata, limit=limit, index="transactions_by_metadata_cid")
    )
    tx_ids = [tx[0] for tx in txs]
    return get_complete_transactions_by_ids(connection, tx_ids)


def store_transaction_outputs(connection, output: Output, index: int) -> str:
    output_id = uuid4().hex
    try:
        connection.run(
            connection.space(TARANT_TABLE_OUTPUT).insert(
                (
                    output_id,
                    int(output.amount),
                    output.public_keys,
                    output.condition.to_dict(),
                    index,
                    output.transaction_id,
                )
            )
        )
        return output_id
    except Exception as e:
        logger.info(f"Could not insert Output: {e}")
        raise OperationDataInsertionError()


@register_query(TarantoolDBConnection)
def store_transactions(connection, signed_transactions: list, table=TARANT_TABLE_TRANSACTION):
    for transaction in signed_transactions:
        store_transaction(connection, transaction, table)
        [
            store_transaction_outputs(connection, Output.outputs_dict(output, transaction["id"]), index)
            for index, output in enumerate(transaction[TARANT_TABLE_OUTPUT])
        ]


@register_query(TarantoolDBConnection)
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
    try:
        connection.run(connection.space(table).insert(tx), only_data=False)
    except Exception as e:
        logger.info(f"Could not insert transactions: {e}")
        if e.args[0] == 3 and e.args[1].startswith("Duplicate key exists in"):
            raise CriticalDoubleSpend()
        else:
            raise OperationDataInsertionError()


@register_query(TarantoolDBConnection)
def get_transaction_by_id(connection, transaction_id, table=TARANT_TABLE_TRANSACTION):
    txs = connection.run(connection.space(table).select(transaction_id, index=TARANT_ID_SEARCH), only_data=False)
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
def get_asset(connection, asset_id: str) -> Asset:
    _data = connection.run(
        connection.space(TARANT_TABLE_TRANSACTION).select(asset_id, index=TARANT_INDEX_TX_BY_ASSET_ID)
    )
    return Asset.from_dict(_data[0])


@register_query(TarantoolDBConnection)
def get_assets(connection, assets_ids: list) -> list[Asset]:
    _returned_data = []
    for _id in list(set(assets_ids)):
        res = connection.run(connection.space(TARANT_TABLE_TRANSACTION).select(_id, index=TARANT_INDEX_TX_BY_ASSET_ID))
        if len(res) == 0:
            continue
        _returned_data.append(res[0])

    sorted_assets = sorted(_returned_data, key=lambda k: k[1], reverse=False)
    return [Asset.from_dict(asset) for asset in sorted_assets]


@register_query(TarantoolDBConnection)
def get_spent(connection, fullfil_transaction_id: str, fullfil_output_index: str) -> list[DbTransaction]:
    _inputs = connection.run(
        connection.space(TARANT_TABLE_TRANSACTION).select(
            [fullfil_transaction_id, fullfil_output_index], index=TARANT_INDEX_SPENDING_BY_ID_AND_OUTPUT_INDEX
        )
    )
    return get_complete_transactions_by_ids(txids=[inp[0] for inp in _inputs], connection=connection)


@register_query(TarantoolDBConnection)
def get_latest_block(connection) -> Union[dict, None]:
    blocks = connection.run(connection.space(TARANT_TABLE_BLOCKS).select())
    if not blocks:
        return None

    blocks = sorted(blocks, key=itemgetter(2), reverse=True)
    latest_block = Block.from_tuple(blocks[0])
    return latest_block.to_dict()


@register_query(TarantoolDBConnection)
def store_block(connection, block: dict):
    block_unique_id = uuid4().hex
    try:
        connection.run(
            connection.space(TARANT_TABLE_BLOCKS).insert(
                (block_unique_id, block["app_hash"], block["height"], block[TARANT_TABLE_TRANSACTION])
            ),
            only_data=False,
        )
    except Exception as e:
        logger.info(f"Could not insert block: {e}")
        raise OperationDataInsertionError()


@register_query(TarantoolDBConnection)
def get_txids_filtered(connection, asset_ids: list[str], operation: str = "", last_tx: bool = False) -> list[str]:
    transactions = []
    if operation == "CREATE":
        transactions = connection.run(
            connection.space(TARANT_TABLE_TRANSACTION).select(
                [asset_ids[0], operation], index="transactions_by_id_and_operation"
            )
        )
    elif operation == "TRANSFER":
        transactions = connection.run(
            connection.space(TARANT_TABLE_TRANSACTION).select(asset_ids, index=TARANT_INDEX_TX_BY_ASSET_ID)
        )
    else:
        txs = connection.run(connection.space(TARANT_TABLE_TRANSACTION).select(asset_ids, index=TARANT_ID_SEARCH))
        asset_txs = connection.run(
            connection.space(TARANT_TABLE_TRANSACTION).select(asset_ids, index=TARANT_INDEX_TX_BY_ASSET_ID)
        )
        transactions = txs + asset_txs

    ids = tuple([tx[0] for tx in transactions])

    # NOTE: check when and where this is used and remove if not
    if last_tx:
        return ids[0]

    return ids


@register_query(TarantoolDBConnection)
def text_search(conn, search, table=TARANT_TABLE_ASSETS, limit=0):
    pattern = ".{}.".format(search)
    field_no = 1 if table == TARANT_TABLE_ASSETS else 2  # 2 for meta_data
    res = conn.run(conn.space(table).call("indexed_pattern_search", (table, field_no, pattern)))

    to_return = []

    if len(res[0]):  # NEEDS BEAUTIFICATION
        if table == TARANT_TABLE_ASSETS:
            for result in res[0]:
                to_return.append({"data": json.loads(result[0])["data"], "id": result[1]})
        else:
            for result in res[0]:
                to_return.append({TARANT_TABLE_META_DATA: json.loads(result[1]), "id": result[0]})

    return to_return if limit == 0 else to_return[:limit]


@register_query(TarantoolDBConnection)
def get_owned_ids(connection, owner: str) -> list[DbTransaction]:
    outputs = connection.run(connection.space(TARANT_TABLE_OUTPUT).select(owner, index="public_keys"))
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
def get_block(connection, block_id=None) -> Union[dict, None]:
    _block = connection.run(connection.space(TARANT_TABLE_BLOCKS).select(block_id, index="height", limit=1))
    if len(_block) == 0:
        return
    _block = Block.from_tuple(_block[0])
    return _block.to_dict()


@register_query(TarantoolDBConnection)
def get_block_with_transaction(connection, txid: str) -> Union[dict, None]:
    _block = connection.run(connection.space(TARANT_TABLE_BLOCKS).select(txid, index="block_by_transaction_id"))
    if len(_block) == 0:
        return
    _block = Block.from_tuple(_block[0])
    return _block.to_dict()


@register_query(TarantoolDBConnection)
def delete_transactions(connection, txn_ids: list):
    try:
        for _id in txn_ids:
            _outputs = get_outputs_by_tx_id(connection, _id)
            for x in range(len(_outputs)):
                connection.connect().call("delete_output", (_outputs[x].id))
        for _id in txn_ids:
            connection.run(connection.space(TARANT_TABLE_TRANSACTION).delete(_id), only_data=False)
            connection.run(connection.space(TARANT_TABLE_GOVERNANCE).delete(_id), only_data=False)
    except Exception as e:
        logger.info(f"Could not insert unspent output: {e}")
        raise OperationDataInsertionError()


@register_query(TarantoolDBConnection)
def store_unspent_outputs(connection, *unspent_outputs: list):
    result = []
    if unspent_outputs:
        for utxo in unspent_outputs:
            try:
                output = connection.run(
                    connection.space(TARANT_TABLE_UTXOS).insert(
                        (uuid4().hex, utxo["transaction_id"], utxo["output_index"], utxo)
                    )
                )
                result.append(output)
            except Exception as e:
                logger.info(f"Could not insert unspent output: {e}")
                raise OperationDataInsertionError()
    return result


@register_query(TarantoolDBConnection)
def delete_unspent_outputs(connection, *unspent_outputs: list):
    result = []
    if unspent_outputs:
        for utxo in unspent_outputs:
            output = connection.run(
                connection.space(TARANT_TABLE_UTXOS).delete(
                    (utxo["transaction_id"], utxo["output_index"]), index="utxo_by_transaction_id_and_output_index"
                )
            )
            result.append(output)
    return result


@register_query(TarantoolDBConnection)
def get_unspent_outputs(connection, query=None):  # for now we don't have implementation for 'query'.
    _utxos = connection.run(connection.space(TARANT_TABLE_UTXOS).select([]))
    return [utx[3] for utx in _utxos]


@register_query(TarantoolDBConnection)
def store_pre_commit_state(connection, state: dict):
    _precommit = connection.run(connection.space(TARANT_TABLE_PRE_COMMITS).select([], limit=1))
    _precommitTuple = (
        (uuid4().hex, state["height"], state[TARANT_TABLE_TRANSACTION])
        if _precommit is None or len(_precommit) == 0
        else _precommit[0]
    )
    try:
        connection.run(
            connection.space(TARANT_TABLE_PRE_COMMITS).upsert(
                _precommitTuple,
                op_list=[("=", 1, state["height"]), ("=", 2, state[TARANT_TABLE_TRANSACTION])],
                limit=1,
            ),
            only_data=False,
        )
    except Exception as e:
        logger.info(f"Could not insert pre commit state: {e}")
        raise OperationDataInsertionError()


@register_query(TarantoolDBConnection)
def get_pre_commit_state(connection) -> dict:
    _commit = connection.run(connection.space(TARANT_TABLE_PRE_COMMITS).select([], index=TARANT_ID_SEARCH))
    if _commit is None or len(_commit) == 0:
        return None
    _commit = sorted(_commit, key=itemgetter(1), reverse=False)[0]
    return {"height": _commit[1], TARANT_TABLE_TRANSACTION: _commit[2]}


@register_query(TarantoolDBConnection)
def store_validator_set(conn, validators_update: dict):
    _validator = conn.run(
        conn.space(TARANT_TABLE_VALIDATOR_SETS).select(validators_update["height"], index="height", limit=1)
    )
    unique_id = uuid4().hex if _validator is None or len(_validator) == 0 else _validator[0][0]
    try:
        conn.run(
            conn.space(TARANT_TABLE_VALIDATOR_SETS).upsert(
                (unique_id, validators_update["height"], validators_update["validators"]),
                op_list=[("=", 1, validators_update["height"]), ("=", 2, validators_update["validators"])],
                limit=1,
            ),
            only_data=False,
        )
    except Exception as e:
        logger.info(f"Could not insert validator set: {e}")
        raise OperationDataInsertionError()


@register_query(TarantoolDBConnection)
def delete_validator_set(connection, height: int):
    _validators = connection.run(connection.space(TARANT_TABLE_VALIDATOR_SETS).select(height, index="height"))
    for _valid in _validators:
        connection.run(connection.space(TARANT_TABLE_VALIDATOR_SETS).delete(_valid[0]), only_data=False)


@register_query(TarantoolDBConnection)
def store_election(connection, election_id: str, height: int, is_concluded: bool):
    try:
        connection.run(
            connection.space(TARANT_TABLE_ELECTIONS).upsert(
                (election_id, height, is_concluded), op_list=[("=", 1, height), ("=", 2, is_concluded)], limit=1
            ),
            only_data=False,
        )
    except Exception as e:
        logger.info(f"Could not insert election: {e}")
        raise OperationDataInsertionError()


@register_query(TarantoolDBConnection)
def store_elections(connection, elections: list):
    try:
        for election in elections:
            _election = connection.run(  # noqa: F841
                connection.space(TARANT_TABLE_ELECTIONS).insert(
                    (election["election_id"], election["height"], election["is_concluded"])
                ),
                only_data=False,
            )
    except Exception as e:
        logger.info(f"Could not insert elections: {e}")
        raise OperationDataInsertionError()


@register_query(TarantoolDBConnection)
def delete_elections(connection, height: int):
    _elections = connection.run(connection.space(TARANT_TABLE_ELECTIONS).select(height, index="height"))
    for _elec in _elections:
        connection.run(connection.space(TARANT_TABLE_ELECTIONS).delete(_elec[0]), only_data=False)


@register_query(TarantoolDBConnection)
def get_validator_set(connection, height: int = None):
    _validators = connection.run(connection.space(TARANT_TABLE_VALIDATOR_SETS).select())
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
def get_election(connection, election_id: str) -> dict:
    _elections = connection.run(connection.space(TARANT_TABLE_ELECTIONS).select(election_id, index=TARANT_ID_SEARCH))
    if _elections is None or len(_elections) == 0:
        return None
    _election = sorted(_elections, key=itemgetter(0), reverse=True)[0]
    return {"election_id": _election[0], "height": _election[1], "is_concluded": _election[2]}


@register_query(TarantoolDBConnection)
def get_asset_tokens_for_public_key(connection, asset_id: str, public_key: str) -> list[DbTransaction]:
    id_transactions = connection.run(connection.space(TARANT_TABLE_GOVERNANCE).select([asset_id]))
    asset_id_transactions = connection.run(
        connection.space(TARANT_TABLE_GOVERNANCE).select([asset_id], index="governance_by_asset_id")
    )
    transactions = id_transactions + asset_id_transactions
    return get_complete_transactions_by_ids(connection, [_tx[0] for _tx in transactions])


@register_query(TarantoolDBConnection)
def store_abci_chain(connection, height: int, chain_id: str, is_synced: bool = True):
    try:
        connection.run(
            connection.space(TARANT_TABLE_ABCI_CHAINS).upsert(
                (chain_id, height, is_synced),
                op_list=[("=", 0, chain_id), ("=", 1, height), ("=", 2, is_synced)],
            ),
            only_data=False,
        )
    except Exception as e:
        logger.info(f"Could not insert abci-chain: {e}")
        raise OperationDataInsertionError()


@register_query(TarantoolDBConnection)
def delete_abci_chain(connection, height: int):
    chains = connection.run(connection.space(TARANT_TABLE_ABCI_CHAINS).select(height, index="height"), only_data=False)
    connection.run(connection.space(TARANT_TABLE_ABCI_CHAINS).delete(chains[0][0], index="id"), only_data=False)


@register_query(TarantoolDBConnection)
def get_latest_abci_chain(connection) -> Union[dict, None]:
    _all_chains = connection.run(connection.space(TARANT_TABLE_ABCI_CHAINS).select())
    if _all_chains is None or len(_all_chains) == 0:
        return None
    _chain = sorted(_all_chains, key=itemgetter(1), reverse=True)[0]
    return {"chain_id": _chain[0], "height": _chain[1], "is_synced": _chain[2]}
