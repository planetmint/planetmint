from secrets import token_hex


def _save_keys_order(dictionary):
    if type(dictionary) is dict:
        keys = list(dictionary.keys())
        _map = {}
        for key in keys:
            _map[key] = _save_keys_order(dictionary=dictionary[key])

        return _map
    elif type(dictionary) is list:
        dictionary = next(iter(dictionary), None)
        if dictionary is not None and type(dictionary) is dict:
            _map = {}
            keys = list(dictionary.keys())
            for key in keys:
                _map[key] = _save_keys_order(dictionary=dictionary[key])

            return _map
    else:
        return None


class TransactionDecompose:
    def __init__(self, _transaction):
        self._transaction = _transaction
        self._tuple_transaction = {
            "transactions": (),
            "inputs": [],
            "outputs": [],
            "keys": [],
            "metadata": (),
            "asset": "",
            "asset_data": (),
            "is_data": False
        }
        self.if_key = lambda dct, key: False if not key in dct.keys() else dct[key]

    def get_map(self, dictionary: dict = None):
        return _save_keys_order(dictionary=dictionary) if dictionary is not None else _save_keys_order(
            dictionary=self._transaction)

    def __create_hash(self, n: int):
        return token_hex(n)

    def _metadata_check(self):
        metadata = self._transaction.get("metadata")
        self._tuple_transaction["metadata"] = (self._transaction["id"], metadata) if metadata is not None else ()

    def __asset_check(self):
        _asset = self._transaction.get("asset")
        if _asset is None:
            self._tuple_transaction["asset"] = ""
            return

        _id = self.if_key(dct=_asset, key="id")
        if _id is not False:
            self._tuple_transaction["asset"] = _id
            return

        self._tuple_transaction["is_data"] = True
        self._tuple_transaction["asset_data"] = (self._transaction["id"], _asset)
        self._tuple_transaction["asset"] = ""

    def __prepare_inputs(self):
        _inputs = []
        input_index = 0
        for _input in self._transaction["inputs"]:
            _inputs.append((self._transaction["id"],
                            _input["fulfillment"],
                            _input["owners_before"],
                            _input["fulfills"]["transaction_id"] if _input["fulfills"] is not None else "",
                            str(_input["fulfills"]["output_index"]) if _input["fulfills"] is not None else "",
                            self.__create_hash(7),
                            input_index))
            input_index = input_index + 1
        return _inputs

    def __prepare_outputs(self):
        _outputs = []
        _keys = []
        output_index = 0
        for _output in self._transaction["outputs"]:
            output_id = self.__create_hash(7)
            if _output["condition"]["details"].get("subconditions") is None:
                _outputs.append((self._transaction["id"],
                                 _output["amount"],
                                 _output["condition"]["uri"],
                                 _output["condition"]["details"]["type"],
                                 _output["condition"]["details"]["public_key"],
                                 output_id,
                                 None,
                                 None,
                                 output_index
                                 ))
            else:
                _outputs.append((self._transaction["id"],
                                 _output["amount"],
                                 _output["condition"]["uri"],
                                 _output["condition"]["details"]["type"],
                                 None,
                                 output_id,
                                 _output["condition"]["details"]["threshold"],
                                 _output["condition"]["details"]["subconditions"],
                                 output_index
                                 ))
            output_index = output_index + 1
            for _key in _output["public_keys"]:
                key_id = self.__create_hash(7)
                _keys.append((key_id, self._transaction["id"], output_id, _key))
        return _keys, _outputs

    def __prepare_transaction(self):
        return (self._transaction["id"],
                self._transaction["operation"],
                self._transaction["version"],
                self._tuple_transaction["asset"],
                self.get_map())

    def convert_to_tuple(self):
        self._metadata_check()
        self.__asset_check()
        self._tuple_transaction["transactions"] = self.__prepare_transaction()
        self._tuple_transaction["inputs"] = self.__prepare_inputs()
        keys, outputs = self.__prepare_outputs()
        self._tuple_transaction["outputs"] = outputs
        self._tuple_transaction["keys"] = keys
        return self._tuple_transaction


class TransactionCompose:
    def convert_to_dict(self, db_results):
        transaction_map = db_results["transaction"][4]
