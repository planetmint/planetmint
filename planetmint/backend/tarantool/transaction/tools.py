from transactions.common.memoize import HDict

from planetmint.backend.tarantool.const import (
    TARANT_TABLE_META_DATA,
    TARANT_TABLE_ASSETS,
    TARANT_TABLE_KEYS,
    TARANT_TABLE_TRANSACTION,
    TARANT_TABLE_INPUT,
    TARANT_TABLE_OUTPUT,
    TARANT_TABLE_SCRIPT,
)


def get_items(_list):
    for item in _list:
        if type(item) is dict:
            yield item


def _save_keys_order(dictionary):
    filter_keys = ["asset", TARANT_TABLE_META_DATA]
    if type(dictionary) is dict or type(dictionary) is HDict:
        keys = list(dictionary.keys())
        _map = {}
        for key in keys:
            _map[key] = _save_keys_order(dictionary=dictionary[key]) if key not in filter_keys else None
        return _map
    elif type(dictionary) is list:
        _maps = []
        for _item in get_items(_list=dictionary):
            _map = {}
            keys = list(_item.keys())
            for key in keys:
                _map[key] = _save_keys_order(dictionary=_item[key]) if key not in filter_keys else None
            _maps.append(_map)
        return _maps
    return None


class TransactionDecompose:
    def __init__(self, _transaction):
        self._transaction = _transaction
        self._tuple_transaction = {
            TARANT_TABLE_TRANSACTION: (),
            TARANT_TABLE_INPUT: [],
            TARANT_TABLE_OUTPUT: [],
            TARANT_TABLE_KEYS: [],
            TARANT_TABLE_SCRIPT: None,
            TARANT_TABLE_META_DATA: None,
            TARANT_TABLE_ASSETS: None,
        }

    def get_map(self, dictionary: dict = None):

        return (
            _save_keys_order(dictionary=dictionary)
            if dictionary is not None
            else _save_keys_order(dictionary=self._transaction)
        )

    def __prepare_transaction(self):
        _map = self.get_map()
        return (self._transaction["id"], self._transaction["operation"], self._transaction["version"], _map)

    def convert_to_tuple(self):
        self._tuple_transaction[TARANT_TABLE_TRANSACTION] = self.__prepare_transaction()
        return self._tuple_transaction


class TransactionCompose:
    def __init__(self, db_results):
        self.db_results = db_results
        self._map = self.db_results[TARANT_TABLE_TRANSACTION][3]

    def _get_transaction_operation(self):
        return self.db_results[TARANT_TABLE_TRANSACTION][1]

    def _get_transaction_version(self):
        return self.db_results[TARANT_TABLE_TRANSACTION][2]

    def _get_transaction_id(self):
        return self.db_results[TARANT_TABLE_TRANSACTION][0]

    def convert_to_dict(self):
        transaction = {k: None for k in list(self._map.keys())}
        transaction["id"] = self._get_transaction_id()
        transaction["version"] = self._get_transaction_version()
        transaction["operation"] = self._get_transaction_operation()
        return transaction
