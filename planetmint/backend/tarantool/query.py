# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

"""Query implementation for Tarantool"""
import json
from uuid import uuid4
from hashlib import sha256
from operator import itemgetter
from tarantool.error import DatabaseError
from planetmint.backend import query
from planetmint.backend.models.keys import Keys
from planetmint.backend.tarantool.const import TARANT_TABLE_META_DATA, TARANT_TABLE_ASSETS, TARANT_TABLE_KEYS, \
    TARANT_TABLE_TRANSACTION, TARANT_TABLE_INPUT, TARANT_TABLE_OUTPUT, TARANT_TABLE_SCRIPT, TARANT_TX_ID_SEARCH, \
    TARANT_ID_SEARCH
from planetmint.backend.utils import module_dispatch_registrar
from planetmint.backend.models import Asset, MetaData, Input, Script, Output
from planetmint.backend.tarantool.connection import TarantoolDBConnection
from planetmint.backend.tarantool.transaction.tools import TransactionCompose, TransactionDecompose

register_query = module_dispatch_registrar(query)


@register_query(TarantoolDBConnection)
def _group_transaction_by_ids(connection, txids: list):
    _transactions = []
    for txid in txids:
        _txobject = connection.run(connection.space(TARANT_TABLE_TRANSACTION).select(txid, index=TARANT_ID_SEARCH))
        if len(_txobject) == 0:
            continue
        _txobject = _txobject[0]
        _txinputs = get_inputs_by_tx_id(connection, txid)
        _txoutputs = connection.run(connection.space(TARANT_TABLE_OUTPUT).select(txid, index=TARANT_ID_SEARCH))
        _txkeys = connection.run(connection.space(TARANT_TABLE_KEYS).select(txid, index=TARANT_TX_ID_SEARCH))
        _txassets = connection.run(connection.space(TARANT_TABLE_ASSETS).select(txid, index=TARANT_TX_ID_SEARCH))
        _txassets = get_assets(connection, [txid])
        _txmeta = get_metadata_by_tx_id(connection, txid)
        _txscript = get_script_by_tx_id(connection, txid)

        _txoutputs = sorted(_txoutputs, key=itemgetter(8), reverse=False)
        result_map = {
            TARANT_TABLE_TRANSACTION: _txobject,
            TARANT_TABLE_OUTPUT: _txoutputs,
            TARANT_TABLE_KEYS: _txkeys,
        }
        tx_compose = TransactionCompose(db_results=result_map)
        _transaction = tx_compose.convert_to_dict()
        _transaction[TARANT_TABLE_INPUT] = [input.to_input_dict() for input in _txinputs]
        _transaction["assets"] = [asset.data for asset in _txassets]
        _transaction["metadata"] = _txmeta.metadata
        if _txscript.script:
            _transaction[TARANT_TABLE_SCRIPT] = _txscript.script
        _transactions.append(_transaction)
    return _transactions


@register_query(TarantoolDBConnection)
def get_inputs_by_tx_id(connection, tx_id: str) -> list[Input]:
    _inputs = connection.run(connection.space(TARANT_TABLE_INPUT).select(tx_id, index=TARANT_ID_SEARCH))
    _sorted_inputs = sorted(_inputs, key=itemgetter(6))
    return [Input.from_tuple(input) for input in _sorted_inputs]


@register_query(TarantoolDBConnection)
def store_transaction_inputs(connection, input: Input, index: int):
    connection.run(connection.space(TARANT_TABLE_INPUT).insert((
        input.tx_id,
        input.fulfillment,
        input.owners_before,
        input.fulfills.transaction_id if input.fulfills else "",
        # TODO: the output_index should be an unsigned int
        str(input.fulfills.output_index) if input.fulfills else "",
        uuid4().hex,
        index
    )))


@register_query(TarantoolDBConnection)
def store_transaction_outputs_and_keys(connection, output_key: (Output, Keys), index: int):
    output_id = store_transaction_outputs(connection, output_key[0], index)
    store_transaction_keys(connection, output_key[1], output_id, index)


def store_transaction_outputs(connection, output: Output, index: int) -> str:
    output_id = uuid4().hex
    if output.condition.details.sub_conditions is None:
        tmp_output = (
            output.tx_id,
            output.amount,
            output.condition.uri if output.condition else "",
            output.condition.details.type if output.condition.details else "",
            output.condition.details.public_key if output.condition.details else "",
            output_id,
            None,
            None,
            index,
        )
    else:
        tmp_output = (
            output.tx_id,
            output.amount,
            output.condition.uri if output.condition else "",
            output.condition.details.type if output.condition.details else "",
            None,
            output_id,
            output.condition.details.threshold if output.condition.details else "",
            json.dumps(output.condition.details.sub_conditions, default=) if output.condition.details.sub_conditions else "",
            index,
        )

    connection.run(connection.space(TARANT_TABLE_OUTPUT).insert((
        tmp_output
    )))
    return output_id


@register_query(TarantoolDBConnection)
def store_transaction_keys(connection, keys: Keys, output_id: str, index: int):
    for key in keys.public_keys:
        connection.run(connection.space(TARANT_TABLE_KEYS).insert((
            uuid4().hex,
            keys.tx_id,
            output_id,
            key,
            index
        )))


@register_query(TarantoolDBConnection)
def store_transactions(connection, signed_transactions: list):
    for transaction in signed_transactions:
        txprepare = TransactionDecompose(transaction)
        txtuples = txprepare.convert_to_tuple()

        connection.run(connection.space(TARANT_TABLE_TRANSACTION).insert(txtuples[TARANT_TABLE_TRANSACTION]),
                       only_data=False)

        [store_transaction_inputs(connection, Input.from_dict(input, transaction["id"]), index) for
         index, input in enumerate(transaction[TARANT_TABLE_INPUT])]

        [store_transaction_outputs_and_keys(connection, Output.outputs_and_keys_dict(output, transaction["id"]), index)
         for index, output in
         enumerate(transaction[TARANT_TABLE_OUTPUT])]

        store_metadatas(connection, [MetaData(transaction["id"], transaction["metadata"])])

        assets = []
        for asset in transaction[TARANT_TABLE_ASSETS]:
            id = transaction["id"] if "id" not in asset else asset["id"]
            assets.append(Asset(id, transaction["id"], asset))
        store_assets(connection, assets)

        if TARANT_TABLE_SCRIPT in transaction:
            connection.run(
                connection.space(TARANT_TABLE_SCRIPT).insert((transaction["id"], transaction[TARANT_TABLE_SCRIPT])),
                only_data=False)


@register_query(TarantoolDBConnection)
def get_transaction(connection, transaction_id: str):
    _transactions = _group_transaction_by_ids(txids=[transaction_id], connection=connection)
    return next(iter(_transactions), None)


@register_query(TarantoolDBConnection)
def get_transactions(connection, transactions_ids: list):
    _transactions = _group_transaction_by_ids(txids=transactions_ids, connection=connection)
    return _transactions


@register_query(TarantoolDBConnection)
def store_metadatas(connection, metadata: list[MetaData]):
    for meta in metadata:
        connection.run(
            connection.space(TARANT_TABLE_META_DATA).insert(
                (meta.id, json.dumps(meta.metadata))
            )  # noqa: E713
        )


@register_query(TarantoolDBConnection)
def get_metadata(connection, transaction_ids: list) -> list[MetaData]:
    _returned_data = []
    for _id in transaction_ids:
        metadata = connection.run(connection.space(TARANT_TABLE_META_DATA).select(_id, index=TARANT_ID_SEARCH))
        if metadata is not None:
            if len(metadata) > 0:
                metadata[0] = list(metadata[0])
                metadata[0][1] = json.loads(metadata[0][1])
                metadata = MetaData(metadata[0][0], metadata[0][1])
                _returned_data.append(metadata)
    return _returned_data


@register_query(TarantoolDBConnection)
def get_metadata_by_tx_id(connection, transaction_id: str) -> MetaData:
    metadata = connection.run(connection.space(TARANT_TABLE_META_DATA).select(transaction_id, index=TARANT_ID_SEARCH))
    return MetaData.from_tuple(metadata[0]) if len(metadata) > 0 else MetaData(transaction_id)


@register_query(TarantoolDBConnection)
def store_asset(connection, asset: Asset):
    tuple_asset = (json.dumps(asset.data), asset.tx_id, asset.id)
    try:
        return connection.run(connection.space(TARANT_TABLE_ASSETS).insert(tuple_asset), only_data=False)
    except DatabaseError:
        pass


@register_query(TarantoolDBConnection)
def store_assets(connection, assets: list):
    for asset in assets:
        store_asset(connection, asset)


@register_query(TarantoolDBConnection)
def get_asset(connection, asset_id: str) -> Asset:
    _data = connection.run(connection.space(TARANT_TABLE_ASSETS).select(asset_id, index=TARANT_TX_ID_SEARCH))
    return Asset.from_tuple(_data[0])


@register_query(TarantoolDBConnection)
def get_assets(connection, assets_ids: list) -> list[Asset]:
    _returned_data = []
    for _id in list(set(assets_ids)):
        res = connection.run(connection.space(TARANT_TABLE_ASSETS).select(_id, index=TARANT_TX_ID_SEARCH))
        _returned_data.append(res[0])

    sorted_assets = sorted(_returned_data, key=lambda k: k[1], reverse=False)
    return [Asset.from_tuple(asset) for asset in sorted_assets]


@register_query(TarantoolDBConnection)
def get_spent(connection, fullfil_transaction_id: str, fullfil_output_index: str):
    _inputs = connection.run(
        connection.space(TARANT_TABLE_INPUT).select([fullfil_transaction_id, str(fullfil_output_index)],
                                                    index="spent_search")
    )
    _transactions = _group_transaction_by_ids(txids=[inp[0] for inp in _inputs], connection=connection)
    return _transactions


@register_query(TarantoolDBConnection)
def get_latest_block(connection):  # TODO Here is used DESCENDING OPERATOR
    _all_blocks = connection.run(connection.space("blocks").select())
    block = {"app_hash": "", "height": 0, TARANT_TABLE_TRANSACTION: []}

    if _all_blocks is not None:
        if len(_all_blocks) > 0:
            _block = sorted(_all_blocks, key=itemgetter(1), reverse=True)[0]
            _txids = connection.run(connection.space("blocks_tx").select(_block[2], index="block_search"))
            block["app_hash"] = _block[0]
            block["height"] = _block[1]
            block[TARANT_TABLE_TRANSACTION] = [tx[0] for tx in _txids]
        else:
            block = None
    return block


@register_query(TarantoolDBConnection)
def store_block(connection, block: dict):
    block_unique_id = uuid4().hex
    connection.run(
        connection.space("blocks").insert((block["app_hash"], block["height"], block_unique_id)), only_data=False
    )
    for txid in block[TARANT_TABLE_TRANSACTION]:
        connection.run(connection.space("blocks_tx").insert((txid, block_unique_id)), only_data=False)


@register_query(TarantoolDBConnection)
def get_txids_filtered(
        connection, asset_ids: list[str], operation: str = None, last_tx: any = None
):  # TODO here is used 'OR' operator
    actions = {
        "CREATE": {"sets": ["CREATE", asset_ids], "index": "transaction_search"},
        # 1 - operation, 2 - id (only in transactions) +
        "TRANSFER": {"sets": ["TRANSFER", asset_ids], "index": "transaction_search"},
        # 1 - operation, 2 - asset.id (linked mode) + OPERATOR OR
        None: {"sets": [asset_ids, asset_ids]},
    }[operation]
    _transactions = []
    if actions["sets"][0] == "CREATE":  # +
        _transactions = connection.run(
            connection.space(TARANT_TABLE_TRANSACTION).select([operation, asset_ids[0]], index=actions["index"])
        )
    elif actions["sets"][0] == "TRANSFER":  # +
        _assets = connection.run(connection.space(TARANT_TABLE_ASSETS).select(asset_ids, index="only_asset_search"))

        for asset in _assets:
            _txid = asset[1]
            _tmp_transactions = connection.run(
                connection.space(TARANT_TABLE_TRANSACTION).select([operation, _txid], index=actions["index"])
            )
            if len(_tmp_transactions) != 0:
                _transactions.extend(_tmp_transactions)
    else:
        _tx_ids = connection.run(connection.space(TARANT_TABLE_TRANSACTION).select(asset_ids, index=TARANT_ID_SEARCH))
        _assets_ids = connection.run(connection.space(TARANT_TABLE_ASSETS).select(asset_ids, index="only_asset_search"))
        return tuple(set([sublist[1] for sublist in _assets_ids] + [sublist[0] for sublist in _tx_ids]))

    if last_tx:
        return tuple(next(iter(_transactions)))

    return tuple([elem[0] for elem in _transactions])


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
    _transactions = _group_transaction_by_ids(txids=_transactionids, connection=connection)
    return _transactions


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
    if block_id is None:
        block_id = []
    _block = connection.run(connection.space("blocks").select(block_id, index="block_search", limit=1))
    if _block is None or len(_block) == 0:
        return []
    _block = _block[0]
    _txblock = connection.run(connection.space("blocks_tx").select(_block[2], index="block_search"))
    return {"app_hash": _block[0], "height": _block[1], TARANT_TABLE_TRANSACTION: [_tx[0] for _tx in _txblock]}


@register_query(TarantoolDBConnection)
def get_block_with_transaction(connection, txid: str):
    _all_blocks_tx = connection.run(connection.space("blocks_tx").select(txid, index=TARANT_ID_SEARCH))
    if _all_blocks_tx is None or len(_all_blocks_tx) == 0:
        return []
    _block = connection.run(connection.space("blocks").select(_all_blocks_tx[0][1], index="block_id_search"))
    return [{"height": _height[1]} for _height in _block]


@register_query(TarantoolDBConnection)
def delete_transactions(connection, txn_ids: list):
    for _id in txn_ids:
        connection.run(connection.space(TARANT_TABLE_TRANSACTION).delete(_id), only_data=False)
    for _id in txn_ids:
        _inputs = connection.run(connection.space(TARANT_TABLE_INPUT).select(_id, index=TARANT_ID_SEARCH),
                                 only_data=False)
        _outputs = connection.run(connection.space(TARANT_TABLE_OUTPUT).select(_id, index=TARANT_ID_SEARCH),
                                  only_data=False)
        _keys = connection.run(connection.space(TARANT_TABLE_KEYS).select(_id, index=TARANT_TX_ID_SEARCH),
                               only_data=False)
        for _kID in _keys:
            connection.run(connection.space(TARANT_TABLE_KEYS).delete(_kID[0], index=TARANT_ID_SEARCH), only_data=False)
        for _inpID in _inputs:
            connection.run(connection.space(TARANT_TABLE_INPUT).delete(_inpID[5], index="delete_search"),
                           only_data=False)
        for _outpID in _outputs:
            connection.run(connection.space(TARANT_TABLE_OUTPUT).delete(_outpID[5], index="unique_search"),
                           only_data=False)

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
    _validator = conn.run(conn.space("validators").select(validators_update["height"], index="height_search", limit=1))
    unique_id = uuid4().hex if _validator is None or len(_validator) == 0 else _validator[0][0]
    conn.run(
        conn.space("validators").upsert(
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
    _elections = connection.run(connection.space("elections").select(height, index="height_search"))
    for _elec in _elections:
        connection.run(connection.space("elections").delete(_elec[0]), only_data=False)


@register_query(TarantoolDBConnection)
def get_validator_set(connection, height: int = None):
    _validators = connection.run(connection.space("validators").select())
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
    _grouped_transactions = _group_transaction_by_ids(connection=connection, txids=[_tx[1] for _tx in _transactions])
    return _grouped_transactions


@register_query(TarantoolDBConnection)
def store_abci_chain(connection, height: int, chain_id: str, is_synced: bool = True):
    hash_id_primarykey = sha256(json.dumps(obj={"height": height}).encode()).hexdigest()
    connection.run(
        connection.space("abci_chains").upsert(
            (height, is_synced, chain_id, hash_id_primarykey),
            op_list=[("=", 0, height), ("=", 1, is_synced), ("=", 2, chain_id)],
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
    _chain = sorted(_all_chains, key=itemgetter(0), reverse=True)[0]
    return {"height": _chain[0], "is_synced": _chain[1], "chain_id": _chain[2]}


@register_query(TarantoolDBConnection)
def get_script_by_tx_id(connection, tx_id: str) -> Script:
    script = connection.run(connection.space(TARANT_TABLE_SCRIPT).select(tx_id, index=TARANT_TX_ID_SEARCH))
    return Script.from_tuple(script[0]) if len(script) < 0 else Script(tx_id)
