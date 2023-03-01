import rapidjson
from itertools import chain

from transactions import Transaction
from transactions.common.exceptions import DoubleSpend
from transactions.common.crypto import public_key_from_ed25519_key
from transactions.common.exceptions import InputDoesNotExist

from planetmint import config_utils, backend
from planetmint.const import GOVERNANCE_TRANSACTION_TYPES
from planetmint.model.fastquery import FastQuery
from planetmint.abci.utils import key_from_base64
from planetmint.backend.connection import Connection
from planetmint.backend.tarantool.const import TARANT_TABLE_TRANSACTION, TARANT_TABLE_GOVERNANCE
from planetmint.backend.models.block import Block
from planetmint.backend.models.output import Output
from planetmint.backend.models.asset import Asset
from planetmint.backend.models.metadata import MetaData
from planetmint.backend.models.dbtransaction import DbTransaction


class DataAccessor:
    def __init__(self, database_connection=None, async_io: bool = False):
        config_utils.autoconfigure()
        self.connection = database_connection if database_connection is not None else Connection(async_io=async_io)

    def store_bulk_transactions(self, transactions):
        txns = []
        gov_txns = []

        for t in transactions:
            transaction = t.tx_dict if t.tx_dict else rapidjson.loads(rapidjson.dumps(t.to_dict()))
            if transaction["operation"] in GOVERNANCE_TRANSACTION_TYPES:
                gov_txns.append(transaction)
            else:
                txns.append(transaction)

        backend.query.store_transactions(self.connection, txns, TARANT_TABLE_TRANSACTION)
        backend.query.store_transactions(self.connection, gov_txns, TARANT_TABLE_GOVERNANCE)

    def delete_transactions(self, txs):
        return backend.query.delete_transactions(self.connection, txs)

    def is_committed(self, transaction_id):
        transaction = backend.query.get_transaction_single(self.connection, transaction_id)
        return bool(transaction)

    def get_transaction(self, transaction_id):
        return backend.query.get_transaction_single(self.connection, transaction_id)

    def get_transactions(self, txn_ids):
        return backend.query.get_transactions(self.connection, txn_ids)

    def get_transactions_filtered(self, asset_ids, operation=None, last_tx=False):
        """Get a list of transactions filtered on some criteria"""
        txids = backend.query.get_txids_filtered(self.connection, asset_ids, operation, last_tx)
        for txid in txids:
            yield self.get_transaction(txid)

    def get_outputs_by_tx_id(self, txid):
        return backend.query.get_outputs_by_tx_id(self.connection, txid)

    def get_outputs_filtered(self, owner, spent=None):
        """Get a list of output links filtered on some criteria

        Args:
            owner (str): base58 encoded public_key.
            spent (bool): If ``True`` return only the spent outputs. If
                          ``False`` return only unspent outputs. If spent is
                          not specified (``None``) return all outputs.

        Returns:
            :obj:`list` of TransactionLink: list of ``txid`` s and ``output`` s
            pointing to another transaction's condition
        """
        outputs = self.fastquery.get_outputs_by_public_key(owner)
        if spent is None:
            return outputs
        elif spent is True:
            return self.fastquery.filter_unspent_outputs(outputs)
        elif spent is False:
            return self.fastquery.filter_spent_outputs(outputs)

    def store_block(self, block):
        """Create a new block."""

        return backend.query.store_block(self.connection, block)

    def get_latest_block(self) -> dict:
        """Get the block with largest height."""

        return backend.query.get_latest_block(self.connection)

    def get_block(self, block_id) -> dict:
        """Get the block with the specified `block_id`.

        Returns the block corresponding to `block_id` or None if no match is
        found.

        Args:
            block_id (int): block id of the block to get.
        """

        block = backend.query.get_block(self.connection, block_id)
        latest_block = self.get_latest_block()
        latest_block_height = latest_block["height"] if latest_block else 0

        if not block and block_id > latest_block_height:
            return

        return block

    def delete_abci_chain(self, height):
        return backend.query.delete_abci_chain(self.connection, height)

    def get_latest_abci_chain(self):
        return backend.query.get_latest_abci_chain(self.connection)

    def store_election(self, election_id, height, is_concluded):
        return backend.query.store_election(self.connection, election_id, height, is_concluded)

    def store_elections(self, elections):
        return backend.query.store_elections(self.connection, elections)

    def delete_elections(self, height):
        return backend.query.delete_elections(self.connection, height)

    # NOTE: moved here from Election needs to be placed somewhere else
    def get_validators_dict(self, height=None):
        """Return a dictionary of validators with key as `public_key` and
        value as the `voting_power`
        """
        validators = {}
        for validator in self.get_validators(height):
            # NOTE: we assume that Tendermint encodes public key in base64
            public_key = public_key_from_ed25519_key(key_from_base64(validator["public_key"]["value"]))
            validators[public_key] = validator["voting_power"]

        return validators

    def get_spent(self, txid, output, current_transactions=[]) -> DbTransaction:
        transactions = backend.query.get_spent(self.connection, txid, output)

        current_spent_transactions = []
        for ctxn in current_transactions:
            for ctxn_input in ctxn.inputs:
                if ctxn_input.fulfills and ctxn_input.fulfills.txid == txid and ctxn_input.fulfills.output == output:
                    current_spent_transactions.append(ctxn)

        transaction = None
        if len(transactions) + len(current_spent_transactions) > 1:
            raise DoubleSpend('tx "{}" spends inputs twice'.format(txid))
        elif transactions:
            tx_id = transactions[0].id
            tx = backend.query.get_transaction_single(self.connection, tx_id)
            transaction = tx.to_dict()
        elif current_spent_transactions:
            transaction = current_spent_transactions[0]

        return transaction

    def get_block_containing_tx(self, txid) -> Block:
        """
        Retrieve the list of blocks (block ids) containing a
           transaction with transaction id `txid`

        Args:
            txid (str): transaction id of the transaction to query

        Returns:
            Block id list (list(int))
        """
        block = backend.query.get_block_with_transaction(self.connection, txid)

        return block

    def get_input_txs_and_conditions(self, inputs, current_transactions=[]):
        # store the inputs so that we can check if the asset ids match
        input_txs = []
        input_conditions = []

        for input_ in inputs:
            input_txid = input_.fulfills.txid
            input_tx = self.get_transaction(input_txid)
            _output = self.get_outputs_by_tx_id(input_txid)
            if input_tx is None:
                for ctxn in current_transactions:
                    if ctxn.id == input_txid:
                        ctxn_dict = ctxn.to_dict()
                        input_tx = DbTransaction.from_dict(ctxn_dict)
                        _output = [
                            Output.from_dict(output, index, ctxn.id)
                            for index, output in enumerate(ctxn_dict["outputs"])
                        ]

            if input_tx is None:
                raise InputDoesNotExist("input `{}` doesn't exist".format(input_txid))

            spent = self.get_spent(input_txid, input_.fulfills.output, current_transactions)
            if spent:
                raise DoubleSpend("input `{}` was already spent".format(input_txid))

            output = _output[input_.fulfills.output]
            input_conditions.append(output)
            tx_dict = input_tx.to_dict()
            tx_dict["outputs"] = Output.list_to_dict(_output)
            tx_dict = DbTransaction.remove_generated_fields(tx_dict)
            pm_transaction = Transaction.from_dict(tx_dict, False)
            input_txs.append(pm_transaction)

        return input_txs, input_conditions

    def get_assets(self, asset_ids) -> list[Asset]:
        """Return a list of assets that match the asset_ids

        Args:
            asset_ids (:obj:`list` of :obj:`str`): A list of asset_ids to
                retrieve from the database.

        Returns:
            list: The list of assets returned from the database.
        """
        return backend.query.get_assets(self.connection, asset_ids)

    def get_assets_by_cid(self, asset_cid, **kwargs) -> list[dict]:
        asset_txs = backend.query.get_transactions_by_asset(self.connection, asset_cid, **kwargs)
        # flatten and return all found assets
        return list(chain.from_iterable([Asset.list_to_dict(tx.assets) for tx in asset_txs]))

    def get_metadata(self, txn_ids) -> list[MetaData]:
        """Return a list of metadata that match the transaction ids (txn_ids)

        Args:
            txn_ids (:obj:`list` of :obj:`str`): A list of txn_ids to
                retrieve from the database.

        Returns:
            list: The list of metadata returned from the database.
        """
        return backend.query.get_metadata(self.connection, txn_ids)

    def get_metadata_by_cid(self, metadata_cid, **kwargs) -> list[str]:
        metadata_txs = backend.query.get_transactions_by_metadata(self.connection, metadata_cid, **kwargs)
        return [tx.metadata.metadata for tx in metadata_txs]

    def get_validator_set(self, height=None):
        return backend.query.get_validator_set(self.connection, height)

    def get_validators(self, height=None):
        result = self.get_validator_set(height)
        return [] if result is None else result["validators"]

    def get_election(self, election_id):
        return backend.query.get_election(self.connection, election_id)

    def get_pre_commit_state(self):
        return backend.query.get_pre_commit_state(self.connection)

    def store_pre_commit_state(self, state):
        return backend.query.store_pre_commit_state(self.connection, state)

    def store_validator_set(self, height, validators):
        """
        Store validator set at a given `height`.
        NOTE: If the validator set already exists at that `height` then an
        exception will be raised.
        """
        return backend.query.store_validator_set(self.connection, {"height": height, "validators": validators})

    def delete_validator_set(self, height):
        return backend.query.delete_validator_set(self.connection, height)

    def store_abci_chain(self, height, chain_id, is_synced=True):
        return backend.query.store_abci_chain(self.connection, height, chain_id, is_synced)

    def get_asset_tokens_for_public_key(self, transaction_id, election_pk):
        txns = backend.query.get_asset_tokens_for_public_key(self.connection, transaction_id, election_pk)
        return txns

    @property
    def fastquery(self):
        return FastQuery(self.connection)
