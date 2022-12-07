# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

"""Query implementation for Tarantool"""
import json
from uuid import uuid4
from hashlib import sha256
from operator import itemgetter


from planetmint.backend import query
from planetmint.backend.models.dbtransaction import DbTransaction
from planetmint.backend.tarantool.const import (
    TARANT_TABLE_META_DATA,
    TARANT_TABLE_ASSETS,
    TARANT_TABLE_KEYS,
    TARANT_TABLE_TRANSACTION,
    TARANT_TABLE_INPUT,
    TARANT_TABLE_OUTPUT,
    TARANT_TABLE_SCRIPT,
    TARANT_TX_ID_SEARCH,
    TARANT_ID_SEARCH, TARANT_INDEX_TX_BY_ASSET_ID, TARANT_INDEX_SPENDING_BY_ID_AND_OUTPUT_INDEX,
)
from planetmint.backend.utils import module_dispatch_registrar
from planetmint.backend.models import Asset, Block, MetaData, Input, Script, Output
from planetmint.backend.tarantool.connection import TarantoolDBConnection

register_query = module_dispatch_registrar(query)


@register_query(TarantoolDBConnection)
def _group_transaction_by_ids(connection, txids: list) -> list[DbTransaction]:
    _transactions = []
    for txid in txids:
        tx = get_transaction_space_by_id(connection, txid)
        if tx is None:
            continue
        _transactions.append(tx)
    return _transactions


@register_query(TarantoolDBConnection)
def get_outputs_by_tx_id(connection, tx_id: str) -> list[Output]:
    _outputs = connection.run(connection.space(TARANT_TABLE_OUTPUT).select(tx_id, index=TARANT_TX_ID_SEARCH))
    _sorted_outputs = sorted(_outputs, key=itemgetter(4))
    return [Output.from_tuple(output) for output in _sorted_outputs]


@register_query(TarantoolDBConnection)
def get_transaction(connection, tx_id: str) -> DbTransaction:
    return NotImplemented


def store_transaction_outputs(connection, output: Output, index: int) -> str:
    output_id = uuid4().hex
    connection.run(connection.space(TARANT_TABLE_OUTPUT).insert((
        output_id,
        int(output.amount),
        output.public_keys,
        output.condition.to_dict(),
        index,
        output.transaction_id,
    )))
    return output_id


@register_query(TarantoolDBConnection)
def store_transactions(connection, signed_transactions: list):
    for transaction in signed_transactions:
        store_transaction(connection, transaction)
        [
            store_transaction_outputs(connection, Output.outputs_dict(output, transaction["id"]), index)
            for index, output in enumerate(transaction[TARANT_TABLE_OUTPUT])
        ]


@register_query(TarantoolDBConnection)
def store_transaction(connection, transaction):
    scripts = None
    if TARANT_TABLE_SCRIPT in transaction:
        scripts = transaction[TARANT_TABLE_SCRIPT]
    tx = (
        transaction["id"],
        transaction["operation"],
        transaction["version"],
        transaction["metadata"],
        transaction["assets"],
        transaction["inputs"],
        scripts)
    connection.run(connection.space(TARANT_TABLE_TRANSACTION).insert(tx), only_data=False)


@register_query(TarantoolDBConnection)
def get_transaction_space_by_id(connection, transaction_id):
    txs = connection.run(connection.space(TARANT_TABLE_TRANSACTION).select(transaction_id, index=TARANT_ID_SEARCH))
    if len(txs) == 0:
        return None
    return DbTransaction.from_tuple(txs[0])


@register_query(TarantoolDBConnection)
def get_transaction_single(connection, transaction_id) -> DbTransaction:
    return _group_transaction_by_ids(txids=[transaction_id], connection=connection)[0]


@register_query(TarantoolDBConnection)
def get_transactions(connection, transactions_ids: list) -> list[DbTransaction]:
    return _group_transaction_by_ids(txids=transactions_ids, connection=connection)


@register_query(TarantoolDBConnection)
def get_asset(connection, asset_id: str) -> Asset:
    _data = connection.run(connection.space(TARANT_TABLE_TRANSACTION).select(asset_id, index=TARANT_INDEX_TX_BY_ASSET_ID))
    return Asset.from_dict(_data[0])


@register_query(TarantoolDBConnection)
def get_assets(connection, assets_ids: list) -> list[Asset]:
    _returned_data = []
    for _id in list(set(assets_ids)):
        res = connection.run(connection.space(TARANT_TABLE_TRANSACTION).select(_id, index=TARANT_INDEX_TX_BY_ASSET_ID))
        if len(res) is 0:
            continue
        _returned_data.append(res[0])

    sorted_assets = sorted(_returned_data, key=lambda k: k[1], reverse=False)
    return [Asset.from_dict(asset) for asset in sorted_assets]


@register_query(TarantoolDBConnection)
def get_spent(connection, fullfil_transaction_id: str, fullfil_output_index: str):
    _inputs = connection.run(
        connection.space(TARANT_TABLE_TRANSACTION).select(
            [fullfil_transaction_id, fullfil_output_index], index=TARANT_INDEX_SPENDING_BY_ID_AND_OUTPUT_INDEX
        )
    )
    return _group_transaction_by_ids(txids=[inp[0] for inp in _inputs], connection=connection)


@register_query(TarantoolDBConnection)
def get_latest_block(connection):
    blocks = connection.run(connection.space("blocks").select())
    if not blocks:
        return None

    blocks = sorted(blocks, key=itemgetter(2), reverse=True)
    latest_block = Block.from_tuple(blocks[0])
    return latest_block.to_dict()


@register_query(TarantoolDBConnection)
def store_block(connection, block: dict):
    block_unique_id = uuid4().hex
    connection.run(
        connection.space("blocks").insert((block_unique_id, block["app_hash"], block["height"], block[TARANT_TABLE_TRANSACTION])), only_data=False
    )


@register_query(TarantoolDBConnection)
def get_txids_filtered(connection, asset_ids: list[str], operation: str = "", last_tx: bool = False):
    transactions = []
    if operation == "CREATE":
        transactions = connection.run(
            connection.space(TARANT_TABLE_TRANSACTION).select([asset_ids[0], operation], index="transactions_by_id_and_operation")
        )
    elif operation == "TRANSFER":
        transactions = connection.run(
            connection.space(TARANT_TABLE_TRANSACTION).select(["", operation, asset_ids], index="transactions_by_id_and_operation")
        )
    else:
        txs = connection.run(connection.space(TARANT_TABLE_TRANSACTION).select(asset_ids, index=TARANT_ID_SEARCH))
        asset_txs = connection.run(
            connection.space(TARANT_TABLE_TRANSACTION).select(asset_ids, index="transactions_by_asset")
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
def get_owned_ids(connection, owner: str):
    _keys = connection.run(connection.space(TARANT_TABLE_KEYS).select(owner, index="keys_search"))
    if _keys is None or len(_keys) == 0:
        return []
    _transactionids = list(set([key[1] for key in _keys]))
    return _group_transaction_by_ids(txids=_transactionids, connection=connection)


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
def get_block(connection, block_id=None):
    _block = connection.run(connection.space("blocks").select(block_id, index="id", limit=1))
    _block = Block.from_tuple(_block[0])
    return _block.to_dict()


@register_query(TarantoolDBConnection)
def get_block_with_transaction(connection, txid: str):
    _block = connection.run(connection.space("blocks").select(txid, index="block_by_transaction_id"))
    return _block[0] if len(_block) == 1 else []


@register_query(TarantoolDBConnection)
def delete_transactions(connection, txn_ids: list):
    for _id in txn_ids:
        connection.run(connection.space(TARANT_TABLE_TRANSACTION).delete(_id), only_data=False)
    for _id in txn_ids:
        _inputs = connection.run(
            connection.space(TARANT_TABLE_INPUT).select(_id, index=TARANT_ID_SEARCH), only_data=False
        )
        _outputs = connection.run(
            connection.space(TARANT_TABLE_OUTPUT).select(_id, index=TARANT_ID_SEARCH), only_data=False
        )
        _keys = connection.run(
            connection.space(TARANT_TABLE_KEYS).select(_id, index=TARANT_TX_ID_SEARCH), only_data=False
        )
        for _kID in _keys:
            connection.run(
                connection.space(TARANT_TABLE_KEYS).delete(_kID[0], index=TARANT_ID_SEARCH), only_data=False
            )
        for _inpID in _inputs:
            connection.run(
                connection.space(TARANT_TABLE_INPUT).delete(_inpID[5], index="delete_search"), only_data=False
            )
        for _outpID in _outputs:
            connection.run(
                connection.space(TARANT_TABLE_OUTPUT).delete(_outpID[5], index="unique_search"), only_data=False
            )

    for _id in txn_ids:
        connection.run(connection.space(TARANT_TABLE_META_DATA).delete(_id, index=TARANT_ID_SEARCH), only_data=False)

    for _id in txn_ids:
        connection.run(connection.space(TARANT_TABLE_ASSETS).delete(_id, index=TARANT_TX_ID_SEARCH), only_data=False)


@register_query(TarantoolDBConnection)
def store_unspent_outputs(connection, *unspent_outputs: list):
    result = []
    if unspent_outputs:
        for utxo in unspent_outputs:
            output = connection.run(
                connection.space("utxos").insert((utxo["transaction_id"], utxo["output_index"], json.dumps(utxo)))
            )
            result.append(output)
    return result


@register_query(TarantoolDBConnection)
def delete_unspent_outputs(connection, *unspent_outputs: list):
    result = []
    if unspent_outputs:
        for utxo in unspent_outputs:
            output = connection.run(connection.space("utxos").delete((utxo["transaction_id"], utxo["output_index"])))
            result.append(output)
    return result


@register_query(TarantoolDBConnection)
def get_unspent_outputs(connection, query=None):  # for now we don't have implementation for 'query'.
    _utxos = connection.run(connection.space("utxos").select([]))
    return [json.loads(utx[2]) for utx in _utxos]


@register_query(TarantoolDBConnection)
def store_pre_commit_state(connection, state: dict):
    _precommit = connection.run(connection.space("pre_commits").select([], limit=1))
    _precommitTuple = (
        (uuid4().hex, state["height"], state[TARANT_TABLE_TRANSACTION])
        if _precommit is None or len(_precommit) == 0
        else _precommit[0]
    )
    connection.run(
        connection.space("pre_commits").upsert(
            _precommitTuple, op_list=[("=", 1, state["height"]), ("=", 2, state[TARANT_TABLE_TRANSACTION])], limit=1
        ),
        only_data=False,
    )


@register_query(TarantoolDBConnection)
def get_pre_commit_state(connection):
    _commit = connection.run(connection.space("pre_commits").select([], index=TARANT_ID_SEARCH))
    if _commit is None or len(_commit) == 0:
        return None
    _commit = sorted(_commit, key=itemgetter(1), reverse=False)[0]
    return {"height": _commit[1], TARANT_TABLE_TRANSACTION: _commit[2]}


@register_query(TarantoolDBConnection)
def store_validator_set(conn, validators_update: dict):
    _validator = conn.run(conn.space("validator_sets").select(validators_update["height"], index="height", limit=1))
    unique_id = uuid4().hex if _validator is None or len(_validator) == 0 else _validator[0][0]
    conn.run(
        conn.space("validator_sets").upsert(
            (unique_id, validators_update["height"], validators_update["validators"]),
            op_list=[("=", 1, validators_update["height"]), ("=", 2, validators_update["validators"])],
            limit=1,
        ),
        only_data=False,
    )


@register_query(TarantoolDBConnection)
def delete_validator_set(connection, height: int):
    _validators = connection.run(connection.space("validators").select(height, index="height_search"))
    for _valid in _validators:
        connection.run(connection.space("validators").delete(_valid[0]), only_data=False)


@register_query(TarantoolDBConnection)
def store_election(connection, election_id: str, height: int, is_concluded: bool):
    connection.run(
        connection.space("elections").upsert(
            (election_id, height, is_concluded), op_list=[("=", 1, height), ("=", 2, is_concluded)], limit=1
        ),
        only_data=False,
    )


@register_query(TarantoolDBConnection)
def store_elections(connection, elections: list):
    for election in elections:
        _election = connection.run(  # noqa: F841
            connection.space("elections").insert(
                (election["election_id"], election["height"], election["is_concluded"])
            ),
            only_data=False,
        )


@register_query(TarantoolDBConnection)
def delete_elections(connection, height: int):
    _elections = connection.run(connection.space("elections").select(height, index="height"))
    for _elec in _elections:
        connection.run(connection.space("elections").delete(_elec[0]), only_data=False)


@register_query(TarantoolDBConnection)
def get_validator_set(connection, height: int = None):
    _validators = connection.run(connection.space("validator_sets").select())
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
def get_election(connection, election_id: str):
    _elections = connection.run(connection.space("elections").select(election_id, index=TARANT_ID_SEARCH))
    if _elections is None or len(_elections) == 0:
        return None
    _election = sorted(_elections, key=itemgetter(0), reverse=True)[0]
    return {"election_id": _election[0], "height": _election[1], "is_concluded": _election[2]}


@register_query(TarantoolDBConnection)
def get_asset_tokens_for_public_key(
        connection, asset_id: str, public_key: str
):  # FIXME Something can be wrong with this function ! (public_key) is not used  # noqa: E501
    # space = connection.space("keys")
    # _keys = space.select([public_key], index="keys_search")
    _transactions = connection.run(connection.space(TARANT_TABLE_ASSETS).select([asset_id], index="assetid_search"))
    # _transactions = _transactions
    # _keys = _keys.data
    return _group_transaction_by_ids(connection=connection, txids=[_tx[1] for _tx in _transactions])


@register_query(TarantoolDBConnection)
def store_abci_chain(connection, height: int, chain_id: str, is_synced: bool = True):
    connection.run(
        connection.space("abci_chains").upsert(
            (chain_id, height, is_synced),
            op_list=[("=", 0, chain_id), ("=", 1, height), ("=", 2, is_synced)],
        ),
        only_data=False,
    )


@register_query(TarantoolDBConnection)
def delete_abci_chain(connection, height: int):
    hash_id_primarykey = sha256(json.dumps(obj={"height": height}).encode()).hexdigest()
    connection.run(connection.space("abci_chains").delete(hash_id_primarykey), only_data=False)


@register_query(TarantoolDBConnection)
def get_latest_abci_chain(connection):
    _all_chains = connection.run(connection.space("abci_chains").select())
    if _all_chains is None or len(_all_chains) == 0:
        return None
    _chain = sorted(_all_chains, key=itemgetter(1), reverse=True)[0]
    return {"chain_id": _chain[0], "height": _chain[1], "is_synced": _chain[2]}
