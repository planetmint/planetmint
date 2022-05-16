# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

"""Query implementation for Tarantool"""

from secrets import token_hex
from operator import itemgetter

from planetmint.backend import query
from planetmint.backend.utils import module_dispatch_registrar
from planetmint.backend.tarantool.connection import TarantoolDB
from planetmint.backend.tarantool.transaction.tools import TransactionCompose, TransactionDecompose
from json import dumps, loads

register_query = module_dispatch_registrar(query)


@register_query(TarantoolDB)
def _group_transaction_by_ids(connection, txids: list):
    txspace = connection.space("transactions")
    inxspace = connection.space("inputs")
    outxspace = connection.space("outputs")
    keysxspace = connection.space("keys")
    assetsxspace = connection.space("assets")
    metaxspace = connection.space("meta_data")
    _transactions = []
    for txid in txids:
        _txobject = txspace.select(txid, index="id_search")
        if len(_txobject.data) == 0:
            continue
        _txobject = _txobject.data[0]
        _txinputs = inxspace.select(txid, index="id_search").data
        _txoutputs = outxspace.select(txid, index="id_search").data
        _txkeys = keysxspace.select(txid, index="txid_search").data
        _txassets = assetsxspace.select(txid, index="txid_search").data
        _txmeta = metaxspace.select(txid, index="id_search").data

        _txinputs = sorted(_txinputs, key=itemgetter(6), reverse=False)
        _txoutputs = sorted(_txoutputs, key=itemgetter(8), reverse=False)
        result_map = {
            "transaction": _txobject,
            "inputs": _txinputs,
            "outputs": _txoutputs,
            "keys": _txkeys,
            "asset": _txassets,
            "metadata": _txmeta,
        }
        tx_compose = TransactionCompose(db_results=result_map)
        _transaction = tx_compose.convert_to_dict()
        _transactions.append(_transaction)
    return _transactions


@register_query(TarantoolDB)
def store_transactions(connection, signed_transactions: list):
    txspace = connection.space("transactions")
    inxspace = connection.space("inputs")
    outxspace = connection.space("outputs")
    keysxspace = connection.space("keys")
    metadatasxspace = connection.space("meta_data")
    assetsxspace = connection.space("assets")

    for transaction in signed_transactions:
        txprepare = TransactionDecompose(transaction)
        txtuples = txprepare.convert_to_tuple()
        try:
            txspace.insert(txtuples["transactions"])
        except:  # This is used for omitting duplicate error in database for test -> test_bigchain_api::test_double_inclusion
            continue

        for _in in txtuples["inputs"]:
            inxspace.insert(_in)

        for _out in txtuples["outputs"]:
            outxspace.insert(_out)

        for _key in txtuples["keys"]:
            keysxspace.insert(_key)

        if txtuples["metadata"] is not None:
            metadatasxspace.insert(txtuples["metadata"])

        if txtuples["asset"] is not None:
            assetsxspace.insert(txtuples["asset"])


@register_query(TarantoolDB)
def get_transaction(connection, transaction_id: str):
    _transactions = _group_transaction_by_ids(txids=[transaction_id], connection=connection)
    return next(iter(_transactions), None)


@register_query(TarantoolDB)
def get_transactions(connection, transactions_ids: list):
    _transactions = _group_transaction_by_ids(txids=transactions_ids, connection=connection)
    return _transactions


@register_query(TarantoolDB)
def store_metadatas(connection, metadata: list):
    space = connection.space("meta_data")
    for meta in metadata:
        space.insert((meta["id"], meta["data"] if not "metadata" in meta else meta["metadata"]))


@register_query(TarantoolDB)
def get_metadata(connection, transaction_ids: list):
    _returned_data = []
    space = connection.space("meta_data")
    for _id in transaction_ids:
        metadata = space.select(_id, index="id_search").data
        if len(metadata) > 0:
            _returned_data.append(metadata)
    return _returned_data if len(_returned_data) > 0 else None


@register_query(TarantoolDB)
def store_asset(connection, asset):
    space = connection.space("assets")
    convert = lambda obj: obj if isinstance(obj, tuple) else (obj, obj["id"], obj["id"])
    try:
        space.insert(convert(asset))
    except:  # TODO Add Raise For Duplicate
        print("DUPLICATE ERROR")


@register_query(TarantoolDB)
def store_assets(connection, assets: list):
    space = connection.space("assets")
    convert = lambda obj: obj if isinstance(obj, tuple) else (obj, obj["id"], obj["id"])
    for asset in assets:
        try:
            space.insert(convert(asset))
        except Exception as ex:  # TODO Raise ERROR for Duplicate
            print(f"EXCEPTION : {ex} ")


@register_query(TarantoolDB)
def get_asset(connection, asset_id: str):
    space = connection.space("assets")
    _data = space.select(asset_id, index="txid_search")
    _data = _data.data
    return _data[0][0] if len(_data) > 0 else []


@register_query(TarantoolDB)
def get_assets(connection, assets_ids: list) -> list:
    _returned_data = []
    for _id in list(set(assets_ids)):
        asset = get_asset(connection, _id)
        _returned_data.append(asset)
    return sorted(_returned_data, key=lambda k: k["id"], reverse=False)


@register_query(TarantoolDB)
def get_spent(connection, fullfil_transaction_id: str, fullfil_output_index: str):
    space = connection.space("inputs")
    _inputs = space.select([fullfil_transaction_id, str(fullfil_output_index)], index="spent_search")
    _inputs = _inputs.data
    _transactions = _group_transaction_by_ids(txids=[inp[0] for inp in _inputs], connection=connection)
    return _transactions


@register_query(TarantoolDB)
def get_latest_block(connection):  # TODO Here is used DESCENDING OPERATOR
    space = connection.space("blocks")
    _all_blocks = space.select()
    _all_blocks = _all_blocks.data
    block = {"app_hash": '', "height": 0, "transactions": []}

    if len(_all_blocks) > 0:
        _block = sorted(_all_blocks, key=itemgetter(1), reverse=True)[0]
        space = connection.space("blocks_tx")
        _txids = space.select(_block[2], index="block_search")
        _txids = _txids.data
        block["app_hash"] = _block[0]
        block["height"] = _block[1]
        block["transactions"] = [tx[0] for tx in _txids]
    else:
        block = None
    return block


@register_query(TarantoolDB)
def store_block(connection, block: dict):
    space = connection.space("blocks")
    block_unique_id = token_hex(8)
    space.insert((block["app_hash"],
                  block["height"],
                  block_unique_id))
    space = connection.space("blocks_tx")
    for txid in block["transactions"]:
        space.insert((txid, block_unique_id))


@register_query(TarantoolDB)
def get_txids_filtered(connection, asset_id: str, operation: str = None,
                       last_tx: any = None):  # TODO here is used 'OR' operator
    actions = {
        "CREATE": {"sets": ["CREATE", asset_id], "index": "transaction_search"},
        # 1 - operation, 2 - id (only in transactions) +
        "TRANSFER": {"sets": ["TRANSFER", asset_id], "index": "transaction_search"},
        # 1 - operation, 2 - asset.id (linked mode) + OPERATOR OR
        None: {"sets": [asset_id, asset_id]}
    }[operation]
    tx_space = connection.space("transactions")
    assets_space = connection.space("assets")
    _transactions = []
    if actions["sets"][0] == "CREATE":  # +
        _transactions = tx_space.select([operation, asset_id], index=actions["index"])
        _transactions = _transactions.data
    elif actions["sets"][0] == "TRANSFER":  # +
        _assets = assets_space.select([asset_id], index="only_asset_search").data
        for asset in _assets:
            _txid = asset[1]
            _transactions = tx_space.select([operation, _txid], index=actions["index"]).data
            if len(_transactions) != 0:
                break
    else:
        _tx_ids = tx_space.select([asset_id], index="id_search")
        # _assets_ids = tx_space.select([asset_id], index="only_asset_search")
        _assets_ids = assets_space.select([asset_id], index="only_asset_search")
        return tuple(set([sublist[1] for sublist in _assets_ids.data] + [sublist[0] for sublist in _tx_ids.data]))

    if last_tx:
        return tuple(next(iter(_transactions)))

    return tuple([elem[0] for elem in _transactions])


# @register_query(TarantoolDB)
# def text_search(conn, search, *, language='english', case_sensitive=False,
#                 # TODO review text search in tarantool (maybe, remove)
#                 diacritic_sensitive=False, text_score=False, limit=0, table='assets'):
#     cursor = conn.run(
#         conn.collection(table)
#             .find({'$text': {
#             '$search': search,
#             '$language': language,
#             '$caseSensitive': case_sensitive,
#             '$diacriticSensitive': diacritic_sensitive}},
#             {'score': {'$meta': 'textScore'}, '_id': False})
#             .sort([('score', {'$meta': 'textScore'})])
#             .limit(limit))
#
#     if text_score:
#         return cursor
#
#     return (_remove_text_score(obj) for obj in cursor)


def _remove_text_score(asset):
    asset.pop('score', None)
    return asset


@register_query(TarantoolDB)
def get_owned_ids(connection, owner: str):
    space = connection.space("keys")
    _keys = space.select(owner, index="keys_search")
    if len(_keys.data) == 0:
        return []
    _transactionids = list(set([key[1] for key in _keys.data]))
    _transactions = _group_transaction_by_ids(txids=_transactionids, connection=connection)
    return _transactions


@register_query(TarantoolDB)
def get_spending_transactions(connection, inputs):
    _transactions = []

    for inp in inputs:
        _trans_list = get_spent(fullfil_transaction_id=inp["transaction_id"],
                                fullfil_output_index=inp["output_index"],
                                connection=connection)
        _transactions.extend(_trans_list)

    return _transactions


@register_query(TarantoolDB)
def get_block(connection, block_id=[]):
    space = connection.space("blocks")
    _block = space.select(block_id, index="block_search", limit=1)
    _block = _block.data
    if len(_block) == 0:
        return []
    _block = _block[0]
    space = connection.space("blocks_tx")
    _txblock = space.select(_block[2], index="block_search")
    _txblock = _txblock.data
    return {"app_hash": _block[0], "height": _block[1], "transactions": [_tx[0] for _tx in _txblock]}


@register_query(TarantoolDB)
def get_block_with_transaction(connection, txid: str):
    space = connection.space("blocks_tx")
    _all_blocks_tx = space.select(txid, index="id_search")
    _all_blocks_tx = _all_blocks_tx.data
    if len(_all_blocks_tx) == 0:
        return []
    space = connection.space("blocks")
    _block = space.select(_all_blocks_tx[0][1], index="block_id_search")
    _block = _block.data[0]
    return {"app_hash": _block[0], "height": _block[1], "transactions": [_tx[0] for _tx in _all_blocks_tx]}


@register_query(TarantoolDB)
def delete_transactions(connection, txn_ids: list):
    tx_space = connection.space("transactions")
    for _id in txn_ids:
        tx_space.delete(_id)
    inputs_space = connection.space("inputs")
    outputs_space = connection.space("outputs")
    k_space = connection.space("keys")
    for _id in txn_ids:
        _inputs = inputs_space.select(_id, index="id_search")
        _outputs = outputs_space.select(_id, index="id_search")
        _keys = k_space.select(_id, index="txid_search")
        for _kID in _keys:
            k_space.delete(_kID[0], index="id_search")
        for _inpID in _inputs:
            inputs_space.delete(_inpID[5], index="delete_search")
        for _outpID in _outputs:
            outputs_space.delete(_outpID[5], index="unique_search")

    meta_space = connection.space("meta_data")
    for _id in txn_ids:
        meta_space.delete(_id, index="id_search")

    assets_space = connection.space("assets")
    for _id in txn_ids:
        assets_space.delete(_id, index="txid_search")


@register_query(TarantoolDB)
def store_unspent_outputs(connection, *unspent_outputs: list):
    space = connection.space('utxos')
    result = []
    if unspent_outputs:
        for utxo in unspent_outputs:
            output = space.insert((utxo['transaction_id'], utxo['output_index'], dumps(utxo)))
            result.append(output.data)
    return result

@register_query(TarantoolDB)
def delete_unspent_outputs(connection, *unspent_outputs: list):
    space = connection.space('utxos')
    result = []
    if unspent_outputs:
        for utxo in unspent_outputs:
            output = space.delete((utxo['transaction_id'], utxo['output_index']))
            result.append(output.data)
    return result


@register_query(TarantoolDB)
def get_unspent_outputs(connection, query=None):  # for now we don't have implementation for 'query'.
    space = connection.space('utxos')
    _utxos = space.select([]).data
    return [loads(utx[2]) for utx in _utxos]


@register_query(TarantoolDB)
def store_pre_commit_state(connection, state: dict):
    space = connection.space("pre_commits")
    _precommit = space.select(state["height"], index="height_search", limit=1)
    unique_id = token_hex(8) if (len(_precommit.data) == 0) else _precommit.data[0][0]
    space.upsert((unique_id, state["height"], state["transactions"]),
                 op_list=[('=', 0, unique_id),
                          ('=', 1, state["height"]),
                          ('=', 2, state["transactions"])],
                 limit=1)


@register_query(TarantoolDB)
def get_pre_commit_state(connection):
    space = connection.space("pre_commits")
    _commit = space.select([], index="id_search").data
    if len(_commit) == 0:
        return None
    _commit = sorted(_commit, key=itemgetter(1), reverse=True)[0]
    return {"height": _commit[1], "transactions": _commit[2]}


@register_query(TarantoolDB)
def store_validator_set(conn, validators_update: dict):
    space = conn.space("validators")
    _validator = space.select(validators_update["height"], index="height_search", limit=1)
    unique_id = token_hex(8) if (len(_validator.data) == 0) else _validator.data[0][0]
    space.upsert((unique_id, validators_update["height"], validators_update["validators"]),
                 op_list=[('=', 0, unique_id),
                          ('=', 1, validators_update["height"]),
                          ('=', 2, validators_update["validators"])],
                 limit=1)


@register_query(TarantoolDB)
def delete_validator_set(connection, height: int):
    space = connection.space("validators")
    _validators = space.select(height, index="height_search")
    for _valid in _validators.data:
        space.delete(_valid[0])


@register_query(TarantoolDB)
def store_election(connection, election_id: str, height: int, is_concluded: bool):
    space = connection.space("elections")
    space.upsert((election_id, height, is_concluded),
                 op_list=[('=', 0, election_id),
                          ('=', 1, height),
                          ('=', 2, is_concluded)],
                 limit=1)


@register_query(TarantoolDB)
def store_elections(connection, elections: list):
    space = connection.space("elections")
    for election in elections:
        _election = space.insert((election["election_id"],
                                  election["height"],
                                  election["is_concluded"]))


@register_query(TarantoolDB)
def delete_elections(connection, height: int):
    space = connection.space("elections")
    _elections = space.select(height, index="height_search")
    for _elec in _elections.data:
        space.delete(_elec[0])


@register_query(TarantoolDB)
def get_validator_set(connection, height: int = None):
    space = connection.space("validators")
    _validators = space.select()
    _validators = _validators.data
    if height is not None:
        _validators = [{"height": validator[1], "validators": validator[2]} for validator in _validators if
                       validator[1] <= height]
        return next(iter(sorted(_validators, key=lambda k: k["height"], reverse=True)), None)
    else:
        _validators = [{"height": validator[1], "validators": validator[2]} for validator in _validators]
        return next(iter(sorted(_validators, key=lambda k: k["height"], reverse=True)), None)


@register_query(TarantoolDB)
def get_election(connection, election_id: str):
    space = connection.space("elections")
    _elections = space.select(election_id, index="id_search")
    _elections = _elections.data
    if len(_elections) == 0:
        return None
    _election = sorted(_elections, key=itemgetter(0), reverse=True)[0]
    return {"election_id": _election[0], "height": _election[1], "is_concluded": _election[2]}


@register_query(TarantoolDB)
def get_asset_tokens_for_public_key(connection, asset_id: str, public_key: str):
    space = connection.space("keys")
    # _keys = space.select([public_key], index="keys_search")
    space = connection.space("assets")
    _transactions = space.select([asset_id], index="assetid_search")
    # _transactions = _transactions
    # _keys = _keys.data
    _grouped_transactions = _group_transaction_by_ids(connection=connection, txids=[_tx[1] for _tx in _transactions])
    return _grouped_transactions


@register_query(TarantoolDB)
def store_abci_chain(connection, height: int, chain_id: str, is_synced: bool = True):
    space = connection.space("abci_chains")
    space.upsert((height, is_synced, chain_id),
                 op_list=[('=', 0, height),
                          ('=', 1, is_synced),
                          ('=', 2, chain_id)],
                 limit=1)


@register_query(TarantoolDB)
def delete_abci_chain(connection, height: int):
    space = connection.space("abci_chains")
    _chains = space.select(height, index="height_search")
    for _chain in _chains.data:
        space.delete(_chain[2])


@register_query(TarantoolDB)
def get_latest_abci_chain(connection):
    space = connection.space("abci_chains")
    _all_chains = space.select().data
    if len(_all_chains) == 0:
        return None
    _chain = sorted(_all_chains, key=itemgetter(0), reverse=True)[0]
    return {"height": _chain[0], "is_synced": _chain[1], "chain_id": _chain[2]}
