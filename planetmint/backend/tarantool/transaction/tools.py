from secrets import token_hex


def _save_keys_order(dictionary):
    filter_keys = ["asset", "metadata"]
    if type(dictionary) is dict:
        keys = list(dictionary.keys())
        _map = {}
        for key in keys:
            _map[key] = _save_keys_order(dictionary=dictionary[key]) if key not in filter_keys else None

        return _map
    elif type(dictionary) is list:
        dictionary = next(iter(dictionary), None)
        if dictionary is not None and type(dictionary) is dict:
            _map = {}
            keys = list(dictionary.keys())
            for key in keys:
                _map[key] = _save_keys_order(dictionary=dictionary[key]) if key not in filter_keys else None

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
            "metadata": None,
            "asset": None
        }
        print(f"Transaction ::::: {self._transaction}")

    def get_map(self, dictionary: dict = None):

        return _save_keys_order(dictionary=dictionary) if dictionary is not None else _save_keys_order(
            dictionary=self._transaction)

    def __create_hash(self, n: int):
        return token_hex(n)

    def _metadata_check(self):
        metadata = self._transaction.get("metadata")
        if metadata is None:
            return

        self._tuple_transaction["metadata"] = (self._transaction["id"], metadata)

    def __asset_check(self):
        _asset = self._transaction.get("asset")
        if _asset is None:
            return
        asset_id = _asset["id"] if _asset.get("id") is not None else self._transaction["id"]
        self._tuple_transaction["asset"] = (_asset, self._transaction["id"], asset_id)

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

    def __init__(self, db_results):
        self.db_results = db_results
        self._map = self.db_results["transaction"][3]

    def _get_transaction_operation(self):
        return self.db_results["transaction"][1]

    def _get_transaction_version(self):
        return self.db_results["transaction"][2]

    def _get_transaction_id(self):
        return self.db_results["transaction"][0]

    def _get_asset(self):
        print( f" asset : {self.db_results}" )
        _asset = iter(self.db_results["asset"])
        #return _asset
        return next(iter(next(_asset, iter([]))), None)

    def _get_metadata(self):
        return self.db_results["metadata"][0][1] if len(self.db_results["metadata"]) == 1 else None

    def _get_inputs(self):
        _inputs = []
        for _input in self.db_results["inputs"]:
            _in = self._map["inputs"].copy()
            _in["fulfillment"] = _input[1]
            if _in["fulfills"] is not None:
                _in["fulfills"]["transaction_id"] = _input[3]
                _in["fulfills"]["output_index"] = int(_input[4])
            _in["owners_before"] = _input[2]
            _inputs.append(_in)
        return _inputs

    def _get_outputs(self):
        _outputs = []
        for _output in self.db_results["outputs"]:
            _out = self._map["outputs"].copy()
            _out["amount"] = _output[1]
            _out["public_keys"] = [_key[3] for _key in self.db_results["keys"] if _key[2] == _output[5]]
            _out["condition"]["uri"] = _output[2]
            if self.db_results["outputs"][0][7] is None:
                _out["condition"]["details"]["type"] = _output[3]
                _out["condition"]["details"]["public_key"] = _output[4]
            else:
                _out["condition"]["details"]["subconditions"] = _output[7]
                _out["condition"]["type"] = _output[3]
                _out["condition"]["treshold"] = _output[6]
            _outputs.append(_out)
        return _outputs

    def convert_to_dict(self):
        transaction = {k: None for k in list(self._map.keys())}
        transaction["id"] = self._get_transaction_id()
        transaction["asset"] = self._get_asset()
        transaction["metadata"] = self._get_metadata()
        transaction["version"] = self._get_transaction_version()
        transaction["operation"] = self._get_transaction_operation()
        transaction["inputs"] = self._get_inputs()
        transaction["outputs"] = self._get_outputs()
        test = transaction["asset"]
        print(f"compose asset : {test}")
        return transaction
