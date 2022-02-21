# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

"""Query implementation for MongoDB"""

from pymongo import DESCENDING

from secrets import token_hex
from operator import itemgetter

from planetmint import backend
from planetmint.backend.exceptions import DuplicateKeyError
from planetmint.backend.utils import module_dispatch_registrar
from planetmint.common.transaction import Transaction

register_query = module_dispatch_registrar(backend.query)


def _group_transaction_by_ids(txids: list, connection):
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
        _txassets = assetsxspace.select(txid, index="assetid_search").data
        _txmeta = metaxspace.select(txid, index="id_search").data
        _obj = {
            "id": txid,
            "version": _txobject[2],
            "operation": _txobject[1],
            "inputs": [
                {
                    "owners_before": _in[2],
                    "fulfills": {"transaction_id": _in[3], "output_index": int(_in[4])} if len(_in[3]) > 0 and len(
                        # TODO Now it is working because of data type cast to INTEGER for field "output_index"
                        _in[4]) > 0 else None,
                    "fulfillment": _in[1]
                } for _in in _txinputs
            ],
            "outputs": [
                {
                    "public_keys": [_key[3] for _key in _txkeys if _key[2] == _out[5]],
                    "amount": _out[1],
                    "condition": {"details": {"type": _out[3], "public_key": _out[4]}, "uri": _out[2]}
                } for _out in _txoutputs
            ]
        }
        if len(_txobject[3]) > 0:
            _obj["asset"] = {
                "id": _txobject[3]
            }
        elif len(_txassets) == 1:
            _obj["asset"] = {
                "data": _txassets[0][1]
            }
        _obj["metadata"] = _txmeta[0][1] if len(_txmeta) == 1 else None
        _transactions.append(_obj)

    return _transactions


def __asset_check(object: dict, connection):
    res = object.get("asset").get("id")
    res = "" if res is None else res
    data = object.get("asset").get("data")
    if data is not None:
        store_asset(connection=connection, asset=object["asset"], tx_id=object["id"], is_data=True)

    return res


def __metadata_check(object: dict, connection):
    metadata = object.get("metadata")
    if metadata is not None:
        space = connection.space("meta_data")
        space.insert((object["id"], metadata))


# @register_query(LocalMongoDBConnection)
def store_transactions(signed_transactions: list,
                       connection):
    txspace = connection.space("transactions")
    inxspace = connection.space("inputs")
    outxspace = connection.space("outputs")
    keysxspace = connection.space("keys")
    for transaction in signed_transactions:
        __metadata_check(object=transaction, connection=connection)
        txspace.insert((transaction["id"],
                        transaction["operation"],
                        transaction["version"],
                        __asset_check(object=transaction, connection=connection)
                        ))
        for _in in transaction["inputs"]:
            input_id = token_hex(7)
            inxspace.insert((transaction["id"],
                             _in["fulfillment"],
                             _in["owners_before"],
                             _in["fulfills"]["transaction_id"] if _in["fulfills"] is not None else "",
                             str(_in["fulfills"]["output_index"]) if _in["fulfills"] is not None else "",
                             input_id))
        for _out in transaction["outputs"]:
            output_id = token_hex(7)
            outxspace.insert((transaction["id"],
                              _out["amount"],
                              _out["condition"]["uri"],
                              _out["condition"]["details"]["type"],
                              _out["condition"]["details"]["public_key"],
                              output_id
                              ))
            for _key in _out["public_keys"]:
                unique_id = token_hex(8)
                keysxspace.insert((unique_id, transaction["id"], output_id, _key))


# @register_query(LocalMongoDBConnection)
def get_transaction(transaction_id: str, connection):
    _transactions = _group_transaction_by_ids(txids=[transaction_id], connection=connection)
    return next(iter(_transactions), None)


# @register_query(LocalMongoDBConnection)
def get_transactions(transactions_ids: list, connection):
    _transactions = _group_transaction_by_ids(txids=transactions_ids, connection=connection)
    return _transactions


# @register_query(LocalMongoDBConnection)
def store_metadatas(metadata: list, connection):
    space = connection.space("meta_data")
    for meta in metadata:
        space.insert((meta["id"], meta["data"] if not "metadata" in meta else meta["metadata"]))


# @register_query(LocalMongoDBConnection)
def get_metadata(transaction_ids: list, connection):
    _returned_data = []
    space = connection.space("meta_data")
    for _id in transaction_ids:
        metadata = space.select(_id, index="id_search")
        _returned_data.append({"id": metadata.data[0][0], "metadata": metadata.data[0][1]})
    return _returned_data


# @register_query(LocalMongoDBConnection)
# asset: {"id": "asset_id"}
# asset: {"data": any} -> insert (tx_id, asset["data"]).
def store_asset(asset: dict, connection, tx_id=None, is_data=False):  # TODO convert to str all asset["id"]
    space = connection.space("assets")
    try:
        if is_data and tx_id is not None:
            space.insert((tx_id, asset["data"]))
        else:
            space.insert((str(asset["id"]), asset["data"]))
    except:  # TODO Add Raise For Duplicate
        pass


# @register_query(LocalMongoDBConnection)
def store_assets(assets: list, connection):
    space = connection.space("assets")
    for asset in assets:
        try:
            space.insert((asset["id"], asset["data"]))
        except:  # TODO Raise ERROR for Duplicate
            pass


# @register_query(LocalMongoDBConnection)
def get_asset(asset_id: str, connection):
    space = connection.space("assets")
    _data = space.select(asset_id, index="assetid_search")
    _data = _data.data[0]
    return {"data": _data[1]}


# @register_query(LocalMongoDBConnection)
def get_assets(assets_ids: list, connection) -> list:
    _returned_data = []
    space = connection.space("assets")
    for _id in list(set(assets_ids)):
        asset = space.select(str(_id), index="assetid_search")
        asset = asset.data[0]
        _returned_data.append({"id": str(asset[0]), "data": asset[1]})
    return sorted(_returned_data, key=lambda k: k["id"], reverse=False)


# @register_query(LocalMongoDBConnection)
def get_spent(fullfil_transaction_id: str, fullfil_output_index: str, connection):
    space = connection.space("inputs")
    _inputs = space.select([fullfil_transaction_id, str(fullfil_output_index)], index="spent_search")
    _inputs = _inputs.data
    _transactions = _group_transaction_by_ids(txids=[inp[0] for inp in _inputs], connection=connection)
    return _transactions


# @register_query(LocalMongoDBConnection)
def latest_block(connection):  # TODO Here is used DESCENDING OPERATOR
    space = connection.space("blocks")
    _all_blocks = space.select()
    _all_blocks = _all_blocks.data
    _block = sorted(_all_blocks, key=itemgetter(1))[0]
    space = connection.space("blocks_tx")
    _txids = space.select(_block[2], index="block_search")
    _txids = _txids.data
    return {"app_hash": _block[1], "height": _block[1], "transactions": [tx[0] for tx in _txids]}


# @register_query(LocalMongoDBConnection)
def store_block(block: dict, connection):
    space = connection.space("blocks")
    block_unique_id = token_hex(8)
    space.insert((block["app_hash"],
                  block["height"],
                  block_unique_id))
    space = connection.space("blocks_tx")
    for txid in block["transactions"]:
        space.insert((txid, block_unique_id))


# @register_query(LocalMongoDBConnection)
def get_txids_filtered(connection, asset_id: str, operation: str = None,
                       last_tx: any = None):  # TODO here is used 'OR' operator
    actions = {
        "CREATE": {"sets": ["CREATE", asset_id], "index": "transaction_search"},
        # 1 - operation, 2 - id (only in transactions) +
        "TRANSFER": {"sets": ["TRANSFER", asset_id], "index": "asset_search"},
        # 1 - operation, 2 - asset.id (linked mode) + OPERATOR OR
        None: {"sets": [asset_id, asset_id]}
    }[operation]
    space = connection.space("transactions")
    if actions["sets"][0] == "CREATE":
        _transactions = space.select([operation, asset_id], index=actions["index"])
        _transactions = _transactions.data
    elif actions["sets"][0] == "TRANSFER":
        _transactions = space.select([operation, asset_id], index=actions["index"])
        _transactions = _transactions.data
    else:
        _tx_ids = space.select([asset_id], index="id_search")
        _assets_ids = space.select([asset_id], index="only_asset_search")
        return tuple(set([sublist[0] for sublist in _assets_ids.data] + [sublist[0] for sublist in _tx_ids.data]))

    if last_tx:
        return tuple(next(iter(_transactions)))

    return tuple([elem[0] for elem in _transactions])


# @register_query(LocalMongoDBConnection)
def text_search(conn, search, *, language='english', case_sensitive=False,
                # TODO review text search in tarantool (maybe, remove)
                diacritic_sensitive=False, text_score=False, limit=0, table='assets'):
    cursor = conn.run(
        conn.collection(table)
            .find({'$text': {
            '$search': search,
            '$language': language,
            '$caseSensitive': case_sensitive,
            '$diacriticSensitive': diacritic_sensitive}},
            {'score': {'$meta': 'textScore'}, '_id': False})
            .sort([('score', {'$meta': 'textScore'})])
            .limit(limit))

    if text_score:
        return cursor

    return (_remove_text_score(obj) for obj in cursor)


def _remove_text_score(asset):
    asset.pop('score', None)
    return asset


# @register_query(LocalMongoDBConnection)
def get_owned_ids(connection, owner: str):
    space = connection.space("keys")
    _keys = space.select(owner, index="keys_search")
    if len(_keys.data) == 0:
        return []
    _transactionids = list(set([key[1] for key in _keys.data]))
    _transactions = _group_transaction_by_ids(txids=_transactionids, connection=connection)
    return _transactions


# @register_query(LocalMongoDBConnection)
def get_spending_transactions(inputs, connection):
    _transactions = []

    for inp in inputs:
        _trans_list = get_spent(fullfil_transaction_id=inp["transaction_id"],
                                fullfil_output_index=inp["output_index"],
                                connection=connection)
        _transactions.extend(_trans_list)

    return _transactions


# @register_query(LocalMongoDBConnection)
def get_block(block_id=[], connection=None):
    space = connection.space("blocks")
    _block = space.select(block_id, index="block_search", limit=1)
    _block = _block.data[0]
    space = connection.space("blocks_tx")
    _txblock = space.select(_block[2], index="block_search")
    _txblock = _txblock.data
    return {"app_hash": _block[0], "height": _block[1], "transactions": [_tx[0] for _tx in _txblock]}


# @register_query(LocalMongoDBConnection)
def get_block_with_transaction(txid: str, connection):
    space = connection.space("blocks_tx")
    _all_blocks_tx = space.select(txid, index="id_search")
    _all_blocks_tx = _all_blocks_tx.data
    space = connection.space("blocks")

    _block = space.select(_all_blocks_tx[0][1], index="block_id_search")
    _block = _block.data[0]
    return {"app_hash": _block[0], "height": _block[1], "transactions": [_tx[0] for _tx in _all_blocks_tx]}


# @register_query(LocalMongoDBConnection)
def delete_transactions(connection, txn_ids: list):
    space = connection.space("transactions")
    for _id in txn_ids:
        space.delete(_id)
    inputs_space = connection.space("inputs")
    outputs_space = connection.space("outputs")
    k_space = connection.space("keys")
    for _id in txn_ids:
        _inputs = inputs_space.select(_id, index="id_search")
        _outputs = outputs_space.select(_id, index="id_search")
        _keys = k_space.select(_id, index="txid_search")
        for _kID in _keys:
            k_space.delete(_kID[2], index="keys_search")
        for _inpID in _inputs:
            inputs_space.delete(_inpID[5], index="delete_search")
        for _outpID in _outputs:
            outputs_space.delete(_outpID[5], index="unique_search")

# # @register_query(LocalMongoDBConnection)
# def store_unspent_outputs(conn, *unspent_outputs: list):
#     if unspent_outputs:
#         try:
#             return conn.run(
#                 conn.collection('utxos').insert_many(
#                     unspent_outputs,
#                     ordered=False,
#                 )
#             )
#         except DuplicateKeyError:
#             # TODO log warning at least
#             pass
#
#
# # @register_query(LocalMongoDBConnection)
# def delete_unspent_outputs(conn, *unspent_outputs: list):
#     if unspent_outputs:
#         return conn.run(
#             conn.collection('utxos').delete_many({
#                 '$or': [{
#                     '$and': [
#                         {'transaction_id': unspent_output['transaction_id']},
#                         {'output_index': unspent_output['output_index']},
#                     ],
#                 } for unspent_output in unspent_outputs]
#             })
#         )
#
#
# # @register_query(LocalMongoDBConnection)
# def get_unspent_outputs(conn, *, query=None):
#     if query is None:
#         query = {}
#     return conn.run(conn.collection('utxos').find(query,
#                                                   projection={'_id': False}))


# @register_query(LocalMongoDBConnection)

def store_pre_commit_state(state: dict, connection):
    space = connection.space("pre_commits")
    # precommit = space.select(state["height"], index="height_search", limit=1)
    # unique_id = token_hex(8) if (len(_precommit.data) == 0) else _precommit.data[0][0]
    space.upsert((state["commit_id"], state["height"], state["transactions"]),
                 op_list=[('=', 0, state["id"]),
                          ('=', 1, state["height"]),
                          ('=', 2, state["transactions"])],
                 limit=1)


# @register_query(LocalMongoDBConnection)
def get_pre_commit_state(connection) -> dict:
    space = connection.space("pre_commits")
    _commit = space.select([], index="id_search", limit=1).data
    if len(_commit) == 0:
        return {}
    _commit = _commit[0]
    return {"height": _commit[0], "transactions": _commit[1]}


# @register_query(LocalMongoDBConnection)
def store_validator_set(validators_update: dict, connection):
    space = connection.space("validators")
    _validator = space.select(validators_update["height"], index="height_search", limit=1)
    unique_id = token_hex(8) if (len(_validator.data) == 0) else _validator.data[0][0]
    space.upsert((unique_id, validators_update["height"], validators_update["validators"]),
                 op_list=[('=', 0, unique_id),
                          ('=', 1, validators_update["height"]),
                          ('=', 2, validators_update["validators"])],
                 limit=1)


# @register_query(LocalMongoDBConnection)
def delete_validator_set(connection, height: int):
    space = connection.space("validators")
    _validators = space.select(height, index="height_search")
    for _valid in _validators.data:
        space.delete(_valid[0])


# @register_query(LocalMongoDBConnection)
def store_election(election_id: str, height: int, is_concluded: bool, connection):
    space = connection.space("elections")
    space.upsert((election_id, height, is_concluded),
                 op_list=[('=', 0, election_id),
                          ('=', 1, height),
                          ('=', 2, is_concluded)],
                 limit=1)


# @register_query(LocalMongoDBConnection)
def store_elections(elections: list, connection):
    space = connection.space("elections")
    for election in elections:
        _election = space.insert((election["election_id"],
                                  election["height"],
                                  election["is_concluded"]))


# @register_query(LocalMongoDBConnection)
def delete_elections(connection, height: int):
    space = connection.space("elections")
    _elections = space.select(height, index="height_search")
    for _elec in _elections.data:
        space.delete(_elec[0])


# @register_query(LocalMongoDBConnection)
def get_validator_set(connection, height: int = None):
    space = connection.space("validators")
    _validators = space.select()
    _validators = _validators.data
    if height is not None:
        _validators = [validator for validator in _validators if validator[1] <= height]
        return next(iter(sorted(_validators, key=itemgetter(1))), None)

    return next(iter(sorted(_validators, key=itemgetter(1))), None)


# @register_query(LocalMongoDBConnection)
def get_election(election_id: str, connection):
    space = connection.space("elections")
    _elections = space.select(election_id, index="id_search")
    _elections = _elections.data
    _election = sorted(_elections, key=itemgetter(0))[0]
    return {"election_id": _election[0], "height": _election[1], "is_concluded": _election[2]}


# @register_query(LocalMongoDBConnection)
def get_asset_tokens_for_public_key(connection, asset_id: str, public_key: str):
    space = connection.space("keys")
    _keys = space.select([public_key], index="keys_search")
    space = connection.space("transactions")
    _transactions = space.select([asset_id], index="only_asset_search")
    _transactions = _transactions.data
    _keys = _keys.data
    _grouped_transactions = _group_transaction_by_ids(connection=connection, txids=[_tx[0] for _tx in _transactions])
    return _grouped_transactions


# @register_query(LocalMongoDBConnection)
def store_abci_chain(height: int, chain_id: str, connection, is_synced: bool = True):
    space = connection.space("abci_chains")
    space.upsert((height, chain_id, is_synced),
                 op_list=[('=', 0, height),
                          ('=', 1, chain_id),
                          ('=', 2, is_synced)],
                 limit=1)


# @register_query(LocalMongoDBConnection)
def delete_abci_chain(connection, height: int):
    space = connection.space("abci_chains")
    _chains = space.select(height, index="height_search")
    for _chain in _chains.data:
        space.delete(_chain[2])


# @register_query(LocalMongoDBConnection)
def get_latest_abci_chain(connection):
    space = connection.space("abci_chains")
    _all_chains = space.select()
    _chain = sorted(_all_chains.data, key=itemgetter(0))[0]
    return {"height": _chain[0], "is_synced": _chain[1], "chain_id": _chain[2]}
