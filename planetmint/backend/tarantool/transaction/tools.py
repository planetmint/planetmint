import copy
import json

from secrets import token_hex
from transactions.common.memoize import HDict

from planetmint.backend.tarantool.const import TARANT_TABLE_META_DATA, TARANT_TABLE_ASSETS, TARANT_TABLE_KEYS, \
    TARANT_TABLE_TRANSACTION, TARANT_TABLE_INPUT, TARANT_TABLE_OUTPUT, TARANT_TABLE_SCRIPT


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

    def __create_hash(self, n: int):
        return token_hex(n)

    def __prepare_outputs(self):
        _outputs = []
        _keys = []
        output_index = 0
        for _output in self._transaction[TARANT_TABLE_OUTPUT]:
            output_id = self.__create_hash(7)
            if _output["condition"]["details"].get("subconditions") is None:
                tmp_output = (
                    self._transaction["id"],
                    _output["amount"],
                    _output["condition"]["uri"],
                    _output["condition"]["details"]["type"],
                    _output["condition"]["details"]["public_key"],
                    output_id,
                    None,
                    None,
                    output_index,
                )
            else:
                tmp_output = (
                    self._transaction["id"],
                    _output["amount"],
                    _output["condition"]["uri"],
                    _output["condition"]["details"]["type"],
                    None,
                    output_id,
                    _output["condition"]["details"]["threshold"],
                    _output["condition"]["details"]["subconditions"],
                    output_index,
                )

            _outputs.append(tmp_output)
            output_index = output_index + 1
            key_index = 0
            for _key in _output["public_keys"]:
                key_id = self.__create_hash(7)
                _keys.append((key_id, self._transaction["id"], output_id, _key, key_index))
                key_index = key_index + 1
        return _keys, _outputs

    def __prepare_transaction(self):
        _map = self.get_map()
        return (self._transaction["id"], self._transaction["operation"], self._transaction["version"], _map)

    def __prepare_script(self):
        try:
            return (self._transaction["id"], self._transaction[TARANT_TABLE_SCRIPT])
        except KeyError:
            return None

    def convert_to_tuple(self):
        self._tuple_transaction[TARANT_TABLE_TRANSACTION] = self.__prepare_transaction()
        keys, outputs = self.__prepare_outputs()
        self._tuple_transaction[TARANT_TABLE_OUTPUT] = outputs
        self._tuple_transaction[TARANT_TABLE_KEYS] = keys
        self._tuple_transaction[TARANT_TABLE_SCRIPT] = self.__prepare_script()
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

    def _get_outputs(self):
        _outputs = []
        for _output in self.db_results[TARANT_TABLE_OUTPUT]:
            _out = copy.deepcopy(self._map[TARANT_TABLE_OUTPUT][_output[-1]])
            _out["amount"] = _output[1]
            _tmp_keys = [(_key[3], _key[4]) for _key in self.db_results[TARANT_TABLE_KEYS] if _key[2] == _output[5]]
            _sorted_keys = sorted(_tmp_keys, key=lambda tup: (tup[1]))
            _out["public_keys"] = [_key[0] for _key in _sorted_keys]

            _out["condition"]["uri"] = _output[2]
            if _output[7] is None:
                _out["condition"]["details"]["type"] = _output[3]
                _out["condition"]["details"]["public_key"] = _output[4]
            else:
                _out["condition"]["details"]["subconditions"] = _output[7]
                _out["condition"]["details"]["type"] = _output[3]
                _out["condition"]["details"]["threshold"] = _output[6]
            _outputs.append(_out)
        return _outputs

    def _get_script(self):
        if self.db_results[TARANT_TABLE_SCRIPT]:
            return self.db_results[TARANT_TABLE_SCRIPT][0][1]
        else:
            return None

    def convert_to_dict(self):
        transaction = {k: None for k in list(self._map.keys())}
        transaction["id"] = self._get_transaction_id()
        transaction["version"] = self._get_transaction_version()
        transaction["operation"] = self._get_transaction_operation()
        transaction[TARANT_TABLE_OUTPUT] = self._get_outputs()
        if self._get_script():
            transaction[TARANT_TABLE_SCRIPT] = self._get_script()
        return transaction
