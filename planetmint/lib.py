# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

"""Module containing main contact points with Tendermint and
MongoDB.

"""
import logging
from collections import namedtuple
from uuid import uuid4
from planetmint.backend.connection import Connection

import rapidjson
from hashlib import sha3_256
import json
import rapidjson
import requests
import planetmint

from collections import namedtuple, OrderedDict
from uuid import uuid4
from hashlib import sha3_256
from transactions import Transaction, Vote
from transactions.common.crypto import public_key_from_ed25519_key
from transactions.common.exceptions import (
    SchemaValidationError,
    ValidationError,
    DuplicateTransaction,
    InvalidSignature,
    DoubleSpend,
    InputDoesNotExist,
    AssetIdMismatch,
    AmountError,
    MultipleInputsError,
    InvalidProposer,
    UnequalValidatorSet,
    InvalidPowerChange,
)
from transactions.common.transaction import VALIDATOR_ELECTION, CHAIN_MIGRATION_ELECTION
from transactions.common.transaction_mode_types import BROADCAST_TX_COMMIT, BROADCAST_TX_ASYNC, BROADCAST_TX_SYNC
from transactions.types.elections.election import Election
from transactions.types.elections.validator_utils import election_id_to_public_key
from planetmint.config import Config
from planetmint import backend, config_utils, fastquery
from planetmint.tendermint_utils import (
    encode_transaction,
    merkleroot,
    key_from_base64,
    public_key_to_base64,
    encode_validator,
    new_validator_set,
)
from planetmint import exceptions as core_exceptions
from planetmint.validation import BaseValidationRules

logger = logging.getLogger(__name__)


class Planetmint(object):
    """Planetmint API

    Create, read, sign, write transactions to the database
    """

    def __init__(self, connection=None):
        """Initialize the Planetmint instance

        A Planetmint instance has several configuration parameters (e.g. host).
        If a parameter value is passed as an argument to the Planetmint
        __init__ method, then that is the value it will have.
        Otherwise, the parameter value will come from an environment variable.
        If that environment variable isn't set, then the value
        will come from the local configuration file. And if that variable
        isn't in the local configuration file, then the parameter will have
        its default value (defined in planetmint.__init__).

        Args:
            connection (:class:`~planetmint.backend.connection.Connection`):
                A connection to the database.
        """
        config_utils.autoconfigure()
        self.mode_commit = BROADCAST_TX_COMMIT
        self.mode_list = (BROADCAST_TX_ASYNC, BROADCAST_TX_SYNC, self.mode_commit)
        self.tendermint_host = Config().get()["tendermint"]["host"]
        self.tendermint_port = Config().get()["tendermint"]["port"]
        self.endpoint = "http://{}:{}/".format(self.tendermint_host, self.tendermint_port)

        validationPlugin = Config().get().get("validation_plugin")

        if validationPlugin:
            self.validation = config_utils.load_validation_plugin(validationPlugin)
        else:
            self.validation = BaseValidationRules
        self.connection = connection if connection is not None else Connection()

    def post_transaction(self, transaction, mode):
        """Submit a valid transaction to the mempool."""
        if not mode or mode not in self.mode_list:
            raise ValidationError("Mode must be one of the following {}.".format(", ".join(self.mode_list)))

        tx_dict = transaction.tx_dict if transaction.tx_dict else transaction.to_dict()
        payload = {"method": mode, "jsonrpc": "2.0", "params": [encode_transaction(tx_dict)], "id": str(uuid4())}
        # TODO: handle connection errors!
        return requests.post(self.endpoint, json=payload)

    def write_transaction(self, transaction, mode):
        # This method offers backward compatibility with the Web API.
        """Submit a valid transaction to the mempool."""
        response = self.post_transaction(transaction, mode)
        return self._process_post_response(response.json(), mode)

    def _process_post_response(self, response, mode):
        logger.debug(response)

        error = response.get("error")
        if error:
            status_code = 500
            message = error.get("message", "Internal Error")
            data = error.get("data", "")

            if "Tx already exists in cache" in data:
                status_code = 400

            return (status_code, message + " - " + data)

        result = response["result"]
        if mode == self.mode_commit:
            check_tx_code = result.get("check_tx", {}).get("code", 0)
            deliver_tx_code = result.get("deliver_tx", {}).get("code", 0)
            error_code = check_tx_code or deliver_tx_code
        else:
            error_code = result.get("code", 0)

        if error_code:
            return (500, "Transaction validation failed")

        return (202, "")

    def store_bulk_transactions(self, transactions):
        txns = []
        assets = []
        txn_metadatas = []

        for tx in transactions:
            transaction = tx.tx_dict if tx.tx_dict else rapidjson.loads(rapidjson.dumps(tx.to_dict()))

            tx_assets = transaction.pop(Transaction.get_assets_tag(tx.version))
            metadata = transaction.pop("metadata")

            tx_assets = backend.convert.prepare_asset(
                self.connection,
                tx,
                filter_operation=[
                    Transaction.CREATE,
                    Transaction.VALIDATOR_ELECTION,
                    Transaction.CHAIN_MIGRATION_ELECTION,
                ],
                assets=tx_assets,
            )

            metadata = backend.convert.prepare_metadata(self.connection, tx, metadata=metadata)

            txn_metadatas.append(metadata)
            assets.append(tx_assets)
            txns.append(transaction)

        backend.query.store_metadatas(self.connection, txn_metadatas)
        if assets:
            backend.query.store_assets(self.connection, assets)
        return backend.query.store_transactions(self.connection, txns)

    def delete_transactions(self, txs):
        return backend.query.delete_transactions(self.connection, txs)

    def update_utxoset(self, transaction):
        self.updated__ = """Update the UTXO set given ``transaction``. That is, remove
        the outputs that the given ``transaction`` spends, and add the
        outputs that the given ``transaction`` creates.

        Args:
            transaction (:obj:`~planetmint.models.Transaction`): A new
                transaction incoming into the system for which the UTXOF
                set needs to be updated.
        """
        spent_outputs = [spent_output for spent_output in transaction.spent_outputs]
        if spent_outputs:
            self.delete_unspent_outputs(*spent_outputs)
        self.store_unspent_outputs(*[utxo._asdict() for utxo in transaction.unspent_outputs])

    def store_unspent_outputs(self, *unspent_outputs):
        """Store the given ``unspent_outputs`` (utxos).

        Args:
            *unspent_outputs (:obj:`tuple` of :obj:`dict`): Variable
                length tuple or list of unspent outputs.
        """
        if unspent_outputs:
            return backend.query.store_unspent_outputs(self.connection, *unspent_outputs)

    def get_utxoset_merkle_root(self):
        """Returns the merkle root of the utxoset. This implies that
        the utxoset is first put into a merkle tree.

        For now, the merkle tree and its root will be computed each
        time. This obviously is not efficient and a better approach
        that limits the repetition of the same computation when
        unnecesary should be sought. For instance, future optimizations
        could simply re-compute the branches of the tree that were
        affected by a change.

        The transaction hash (id) and output index should be sufficient
        to uniquely identify a utxo, and consequently only that
        information from a utxo record is needed to compute the merkle
        root. Hence, each node of the merkle tree should contain the
        tuple (txid, output_index).

        .. important:: The leaves of the tree will need to be sorted in
            some kind of lexicographical order.

        Returns:
            str: Merkle root in hexadecimal form.
        """
        utxoset = backend.query.get_unspent_outputs(self.connection)
        # TODO Once ready, use the already pre-computed utxo_hash field.
        # See common/transactions.py for details.
        hashes = [
            sha3_256("{}{}".format(utxo["transaction_id"], utxo["output_index"]).encode()).digest() for utxo in utxoset
        ]
        # TODO Notice the sorted call!
        return merkleroot(sorted(hashes))

    def get_unspent_outputs(self):
        """Get the utxoset.

        Returns:
            generator of unspent_outputs.
        """
        cursor = backend.query.get_unspent_outputs(self.connection)
        return (record for record in cursor)

    def delete_unspent_outputs(self, *unspent_outputs):
        """Deletes the given ``unspent_outputs`` (utxos).

        Args:
            *unspent_outputs (:obj:`tuple` of :obj:`dict`): Variable
                length tuple or list of unspent outputs.
        """
        if unspent_outputs:
            return backend.query.delete_unspent_outputs(self.connection, *unspent_outputs)

    def is_committed(self, transaction_id):
        transaction = backend.query.get_transaction(self.connection, transaction_id)
        return bool(transaction)

    def get_transaction(self, transaction_id):
        transaction = backend.query.get_transaction(self.connection, transaction_id)
        if transaction:
            assets = backend.query.get_assets(self.connection, [transaction_id])
            metadata = backend.query.get_metadata(self.connection, [transaction_id])
            # NOTE: assets must not be replaced for transfer transactions
            # NOTE: assets should be appended for all txs that define new assets otherwise the ids are already stored in tx
            if transaction["operation"] != "TRANSFER" and transaction["operation"] != "VOTE" and assets:
                transaction["assets"] = assets[0][0]

            if "metadata" not in transaction:
                metadata = metadata[0] if metadata else None
                if metadata:
                    metadata = metadata.get("metadata")

                transaction.update({"metadata": metadata})

            transaction = Transaction.from_dict(transaction, False)

        return transaction

    def get_transactions(self, txn_ids):
        return backend.query.get_transactions(self.connection, txn_ids)

    def get_transactions_filtered(self, asset_ids, operation=None, last_tx=None):
        """Get a list of transactions filtered on some criteria"""
        txids = backend.query.get_txids_filtered(self.connection, asset_ids, operation, last_tx)
        for txid in txids:
            yield self.get_transaction(txid)

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

    def get_spent(self, txid, output, current_transactions=[]):
        transactions = backend.query.get_spent(self.connection, txid, output)
        transactions = list(transactions) if transactions else []
        if len(transactions) > 1:
            raise core_exceptions.CriticalDoubleSpend(
                "`{}` was spent more than once. There is a problem" " with the chain".format(txid)
            )

        current_spent_transactions = []
        for ctxn in current_transactions:
            for ctxn_input in ctxn.inputs:
                if ctxn_input.fulfills and ctxn_input.fulfills.txid == txid and ctxn_input.fulfills.output == output:
                    current_spent_transactions.append(ctxn)

        transaction = None
        if len(transactions) + len(current_spent_transactions) > 1:
            raise DoubleSpend('tx "{}" spends inputs twice'.format(txid))
        elif transactions:
            transaction = backend.query.get_transaction(self.connection, transactions[0]["id"])
            transaction = Transaction.from_dict(transaction, False)
        elif current_spent_transactions:
            transaction = current_spent_transactions[0]

        return transaction

    def store_block(self, block):
        """Create a new block."""

        return backend.query.store_block(self.connection, block)

    def get_latest_block(self):
        """Get the block with largest height."""

        return backend.query.get_latest_block(self.connection)

    def get_block(self, block_id):
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

        result = {"height": block_id, "transactions": []}

        if block:
            transactions = backend.query.get_transactions(self.connection, block["transactions"])
            result["transactions"] = [t.to_dict() for t in self.tx_from_db(transactions)]

        return result

    def get_block_containing_tx(self, txid):
        """Retrieve the list of blocks (block ids) containing a
           transaction with transaction id `txid`

        Args:
            txid (str): transaction id of the transaction to query

        Returns:
            Block id list (list(int))
        """
        blocks = list(backend.query.get_block_with_transaction(self.connection, txid))
        if len(blocks) > 1:
            logger.critical("Transaction id %s exists in multiple blocks", txid)

        return [block["height"] for block in blocks]

    def validate_transaction(self, tx, current_transactions=[]):
        """Validate a transaction against the current status of the database."""

        transaction = tx

        # CLEANUP: The conditional below checks for transaction in dict format.
        # It would be better to only have a single format for the transaction
        # throught the code base.
        if isinstance(transaction, dict):
            try:
                transaction = Transaction.from_dict(tx, False)
            except SchemaValidationError as e:
                logger.warning("Invalid transaction schema: %s", e.__cause__.message)
                return False
            except ValidationError as e:
                logger.warning("Invalid transaction (%s): %s", type(e).__name__, e)
                return False

        if transaction.operation == Transaction.CREATE:
            duplicates = any(txn for txn in current_transactions if txn.id == transaction.id)
            if self.is_committed(transaction.id) or duplicates:
                raise DuplicateTransaction("transaction `{}` already exists".format(transaction.id))
        elif transaction.operation in [Transaction.TRANSFER, Transaction.VOTE]:
            self.validate_transfer_inputs(transaction, current_transactions)

        return transaction

    def validate_transfer_inputs(self, tx, current_transactions=[]):
        # store the inputs so that we can check if the asset ids match
        input_txs = []
        input_conditions = []
        for input_ in tx.inputs:
            input_txid = input_.fulfills.txid
            input_tx = self.get_transaction(input_txid)
            if input_tx is None:
                for ctxn in current_transactions:
                    if ctxn.id == input_txid:
                        input_tx = ctxn

            if input_tx is None:
                raise InputDoesNotExist("input `{}` doesn't exist".format(input_txid))

            spent = self.get_spent(input_txid, input_.fulfills.output, current_transactions)
            if spent:
                raise DoubleSpend("input `{}` was already spent".format(input_txid))

            output = input_tx.outputs[input_.fulfills.output]
            input_conditions.append(output)
            input_txs.append(input_tx)

        # Validate that all inputs are distinct
        links = [i.fulfills.to_uri() for i in tx.inputs]
        if len(links) != len(set(links)):
            raise DoubleSpend('tx "{}" spends inputs twice'.format(tx.id))

        # validate asset id
        asset_id = tx.get_asset_id(input_txs)
        if asset_id != Transaction.read_out_asset_id(tx):
            raise AssetIdMismatch(("The asset id of the input does not" " match the asset id of the" " transaction"))

        if not tx.inputs_valid(input_conditions):
            raise InvalidSignature("Transaction signature is invalid.")

        input_amount = sum([input_condition.amount for input_condition in input_conditions])
        output_amount = sum([output_condition.amount for output_condition in tx.outputs])

        if output_amount != input_amount:
            raise AmountError(
                (
                    "The amount used in the inputs `{}`" " needs to be same as the amount used" " in the outputs `{}`"
                ).format(input_amount, output_amount)
            )

        return True

    def is_valid_transaction(self, tx, current_transactions=[]):
        # NOTE: the function returns the Transaction object in case
        # the transaction is valid
        try:
            return self.validate_transaction(tx, current_transactions)
        except ValidationError as e:
            logger.warning("Invalid transaction (%s): %s", type(e).__name__, e)
            return False

    def text_search(self, search, *, limit=0, table="assets"):
        """Return an iterator of assets that match the text search

        Args:
            search (str): Text search string to query the text index
            limit (int, optional): Limit the number of returned documents.

        Returns:
            iter: An iterator of assets that match the text search.
        """
        return backend.query.text_search(self.connection, search, limit=limit, table=table)

    def get_assets(self, asset_ids):
        """Return a list of assets that match the asset_ids

        Args:
            asset_ids (:obj:`list` of :obj:`str`): A list of asset_ids to
                retrieve from the database.

        Returns:
            list: The list of assets returned from the database.
        """
        return backend.query.get_assets(self.connection, asset_ids)

    def get_metadata(self, txn_ids):
        """Return a list of metadata that match the transaction ids (txn_ids)

        Args:
            txn_ids (:obj:`list` of :obj:`str`): A list of txn_ids to
                retrieve from the database.

        Returns:
            list: The list of metadata returned from the database.
        """
        return backend.query.get_metadata(self.connection, txn_ids)

    @property
    def fastquery(self):
        return fastquery.FastQuery(self.connection)

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
        """Store validator set at a given `height`.
        NOTE: If the validator set already exists at that `height` then an
        exception will be raised.
        """
        return backend.query.store_validator_set(self.connection, {"height": height, "validators": validators})

    def delete_validator_set(self, height):
        return backend.query.delete_validator_set(self.connection, height)

    def store_abci_chain(self, height, chain_id, is_synced=True):
        return backend.query.store_abci_chain(self.connection, height, chain_id, is_synced)

    def delete_abci_chain(self, height):
        return backend.query.delete_abci_chain(self.connection, height)

    def get_latest_abci_chain(self):
        return backend.query.get_latest_abci_chain(self.connection)

    def migrate_abci_chain(self):
        """Generate and record a new ABCI chain ID. New blocks are not
        accepted until we receive an InitChain ABCI request with
        the matching chain ID and validator set.

        Chain ID is generated based on the current chain and height.
        `chain-X` => `chain-X-migrated-at-height-5`.
        `chain-X-migrated-at-height-5` => `chain-X-migrated-at-height-21`.

        If there is no known chain (we are at genesis), the function returns.
        """
        latest_chain = self.get_latest_abci_chain()
        if latest_chain is None:
            return

        block = self.get_latest_block()

        suffix = "-migrated-at-height-"
        chain_id = latest_chain["chain_id"]
        block_height_str = str(block["height"])
        new_chain_id = chain_id.split(suffix)[0] + suffix + block_height_str

        self.store_abci_chain(block["height"] + 1, new_chain_id, False)

    def store_election(self, election_id, height, is_concluded):
        return backend.query.store_election(self.connection, election_id, height, is_concluded)

    def store_elections(self, elections):
        return backend.query.store_elections(self.connection, elections)

    def delete_elections(self, height):
        return backend.query.delete_elections(self.connection, height)

    def tx_from_db(self, tx_dict_list):
        """Helper method that reconstructs a transaction dict that was returned
        from the database. It checks what asset_id to retrieve, retrieves the
        asset from the asset table and reconstructs the transaction.

        Args:
            tx_dict_list (:list:`dict` or :obj:`dict`): The transaction dict or
                list of transaction dict as returned from the database.

        Returns:
            :class:`~Transaction`

        """
        return_list = True
        if isinstance(tx_dict_list, dict):
            tx_dict_list = [tx_dict_list]
            return_list = False

        tx_map = {}
        tx_ids = []
        for tx in tx_dict_list:
            tx.update({"metadata": None})
            tx_map[tx["id"]] = tx
            tx_ids.append(tx["id"])

        assets = list(self.get_assets(tx_ids))
        for asset in assets:
            if asset is not None:
                # This is tarantool specific behaviour needs to be addressed
                tx = tx_map[asset[1]]
                tx["asset"] = asset[0]

        tx_ids = list(tx_map.keys())
        metadata_list = list(self.get_metadata(tx_ids))
        for metadata in metadata_list:
            if "id" in metadata:
                tx = tx_map[metadata["id"]]
                tx.update({"metadata": metadata.get("metadata")})

        if return_list:
            tx_list = []
            for tx_id, tx in tx_map.items():
                tx_list.append(Transaction.from_dict(tx))
            return tx_list
        else:
            tx = list(tx_map.values())[0]
            return Transaction.from_dict(tx)

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

    def validate_election(self, transaction, current_transactions=[]):  # TODO: move somewhere else
        """Validate election transaction

        NOTE:
        * A valid election is initiated by an existing validator.

        * A valid election is one where voters are validators and votes are
          allocated according to the voting power of each validator node.

        Args:
            :param planet: (Planetmint) an instantiated planetmint.lib.Planetmint object.
            :param current_transactions: (list) A list of transactions to be validated along with the election

        Returns:
            Election: a Election object or an object of the derived Election subclass.

        Raises:
            ValidationError: If the election is invalid
        """

        duplicates = any(txn for txn in current_transactions if txn.id == transaction.id)
        if self.is_committed(transaction.id) or duplicates:
            raise DuplicateTransaction("transaction `{}` already exists".format(transaction.id))

        current_validators = self.get_validators_dict()

        # NOTE: Proposer should be a single node
        if len(transaction.inputs) != 1 or len(transaction.inputs[0].owners_before) != 1:
            raise MultipleInputsError("`tx_signers` must be a list instance of length one")

        # NOTE: Check if the proposer is a validator.
        [election_initiator_node_pub_key] = transaction.inputs[0].owners_before
        if election_initiator_node_pub_key not in current_validators.keys():
            raise InvalidProposer("Public key is not a part of the validator set")

        # NOTE: Check if all validators have been assigned votes equal to their voting power
        if not self.is_same_topology(current_validators, transaction.outputs):
            raise UnequalValidatorSet("Validator set much be exactly same to the outputs of election")

        if transaction.operation == VALIDATOR_ELECTION:
            self.validate_validator_election(transaction)

        return transaction

    def validate_validator_election(self, transaction):  # TODO: move somewhere else
        """For more details refer BEP-21: https://github.com/planetmint/BEPs/tree/master/21"""

        current_validators = self.get_validators_dict()

        # NOTE: change more than 1/3 of the current power is not allowed
        if transaction.assets[0]["data"]["power"] >= (1 / 3) * sum(current_validators.values()):
            raise InvalidPowerChange("`power` change must be less than 1/3 of total power")

    def get_election_status(self, transaction):
        election = self.get_election(transaction.id)
        if election and election["is_concluded"]:
            return Election.CONCLUDED

        return Election.INCONCLUSIVE if self.has_validator_set_changed(transaction) else Election.ONGOING

    def has_validator_set_changed(self, transaction):  # TODO: move somewhere else
        latest_change = self.get_validator_change()
        if latest_change is None:
            return False

        latest_change_height = latest_change["height"]

        election = self.get_election(transaction.id)

        return latest_change_height > election["height"]

    def get_validator_change(self):  # TODO: move somewhere else
        """Return the validator set from the most recent approved block

        :return: {
            'height': <block_height>,
            'validators': <validator_set>
        }
        """
        latest_block = self.get_latest_block()
        if latest_block is None:
            return None
        return self.get_validator_set(latest_block["height"])

    def get_validator_dict(self, height=None):
        """Return a dictionary of validators with key as `public_key` and
        value as the `voting_power`
        """
        validators = {}
        for validator in self.get_validators(height):
            # NOTE: we assume that Tendermint encodes public key in base64
            public_key = public_key_from_ed25519_key(key_from_base64(validator["public_key"]["value"]))
            validators[public_key] = validator["voting_power"]

        return validators

    def get_recipients_list(self):
        """Convert validator dictionary to a recipient list for `Transaction`"""

        recipients = []
        for public_key, voting_power in self.get_validator_dict().items():
            recipients.append(([public_key], voting_power))

        return recipients

    def show_election_status(self, transaction):
        data = transaction.assets[0]["data"]
        if "public_key" in data.keys():
            data["public_key"] = public_key_to_base64(data["public_key"]["value"])
        response = ""
        for k, v in data.items():
            if k != "seed":
                response += f"{k}={v}\n"
        response += f"status={self.get_election_status(transaction)}"

        if transaction.operation == CHAIN_MIGRATION_ELECTION:
            response = self.append_chain_migration_status(response)

        return response

    def append_chain_migration_status(self, status):
        chain = self.get_latest_abci_chain()
        if chain is None or chain["is_synced"]:
            return status

        status += f'\nchain_id={chain["chain_id"]}'
        block = self.get_latest_block()
        status += f'\napp_hash={block["app_hash"]}'
        validators = [
            {
                "pub_key": {
                    "type": "tendermint/PubKeyEd25519",
                    "value": k,
                },
                "power": v,
            }
            for k, v in self.get_validator_dict().items()
        ]
        status += f"\nvalidators={json.dumps(validators, indent=4)}"
        return status

    def is_same_topology(cls, current_topology, election_topology):
        voters = {}
        for voter in election_topology:
            if len(voter.public_keys) > 1:
                return False

            [public_key] = voter.public_keys
            voting_power = voter.amount
            voters[public_key] = voting_power

        # Check whether the voters and their votes is same to that of the
        # validators and their voting power in the network
        return current_topology == voters

    def count_votes(self, election_pk, transactions, getter=getattr):
        votes = 0
        for txn in transactions:
            if getter(txn, "operation") == Vote.OPERATION:
                for output in getter(txn, "outputs"):
                    # NOTE: We enforce that a valid vote to election id will have only
                    # election_pk in the output public keys, including any other public key
                    # along with election_pk will lead to vote being not considered valid.
                    if len(getter(output, "public_keys")) == 1 and [election_pk] == getter(output, "public_keys"):
                        votes = votes + int(getter(output, "amount"))
        return votes

    def get_commited_votes(self, transaction, election_pk=None):  # TODO: move somewhere else
        if election_pk is None:
            election_pk = election_id_to_public_key(transaction.id)
        txns = list(backend.query.get_asset_tokens_for_public_key(self.connection, transaction.id, election_pk))
        return self.count_votes(election_pk, txns, dict.get)

    def _get_initiated_elections(self, height, txns):  # TODO: move somewhere else
        elections = []
        for tx in txns:
            if not isinstance(tx, Election):
                continue

            elections.append({"election_id": tx.id, "height": height, "is_concluded": False})
        return elections

    def _get_votes(self, txns):  # TODO: move somewhere else
        elections = OrderedDict()
        for tx in txns:
            if not isinstance(tx, Vote):
                continue

            election_id = tx.assets[0]["id"]
            if election_id not in elections:
                elections[election_id] = []
            elections[election_id].append(tx)
        return elections

    def process_block(self, new_height, txns):  # TODO: move somewhere else
        """Looks for election and vote transactions inside the block, records
        and processes elections.

        Every election is recorded in the database.

        Every vote has a chance to conclude the corresponding election. When
        an election is concluded, the corresponding database record is
        marked as such.

        Elections and votes are processed in the order in which they
        appear in the block. Elections are concluded in the order of
        appearance of their first votes in the block.

        For every election concluded in the block, calls its `on_approval`
        method. The returned value of the last `on_approval`, if any,
        is a validator set update to be applied in one of the following blocks.

        `on_approval` methods are implemented by elections of particular type.
        The method may contain side effects but should be idempotent. To account
        for other concluded elections, if it requires so, the method should
        rely on the database state.
        """
        # elections initiated in this block
        initiated_elections = self._get_initiated_elections(new_height, txns)

        if initiated_elections:
            self.store_elections(initiated_elections)

        # elections voted for in this block and their votes
        elections = self._get_votes(txns)

        validator_update = None
        for election_id, votes in elections.items():
            election = self.get_transaction(election_id)
            if election is None:
                continue

            if not self.has_election_concluded(election, votes):
                continue

            validator_update = self.approve_election(election, new_height)
            self.store_election(election.id, new_height, is_concluded=True)

        return [validator_update] if validator_update else []

    def has_election_concluded(self, transaction, current_votes=[]):  # TODO: move somewhere else
        """Check if the election can be concluded or not.

        * Elections can only be concluded if the validator set has not changed
          since the election was initiated.
        * Elections can be concluded only if the current votes form a supermajority.

        Custom elections may override this function and introduce additional checks.
        """
        if self.has_validator_set_changed(transaction):
            return False

        if transaction.operation == VALIDATOR_ELECTION:
            if not self.has_validator_election_concluded():
                return False

        if transaction.operation == CHAIN_MIGRATION_ELECTION:
            if not self.has_chain_migration_concluded():
                return False

        election_pk = election_id_to_public_key(transaction.id)
        votes_committed = self.get_commited_votes(transaction, election_pk)
        votes_current = self.count_votes(election_pk, current_votes)

        total_votes = sum(output.amount for output in transaction.outputs)
        if (votes_committed < (2 / 3) * total_votes) and (votes_committed + votes_current >= (2 / 3) * total_votes):
            return True

        return False

    def has_validator_election_concluded(self):  # TODO: move somewhere else
        latest_block = self.get_latest_block()
        if latest_block is not None:
            latest_block_height = latest_block["height"]
            latest_validator_change = self.get_validator_set()["height"]

            # TODO change to `latest_block_height + 3` when upgrading to Tendermint 0.24.0.
            if latest_validator_change == latest_block_height + 2:
                # do not conclude the election if there is a change assigned already
                return False

        return True

    def has_chain_migration_concluded(self):  # TODO: move somewhere else
        chain = self.get_latest_abci_chain()
        if chain is not None and not chain["is_synced"]:
            # do not conclude the migration election if
            # there is another migration in progress
            return False

        return True

    def rollback_election(self, new_height, txn_ids):  # TODO: move somewhere else
        """Looks for election and vote transactions inside the block and
        cleans up the database artifacts possibly created in `process_blocks`.

        Part of the `end_block`/`commit` crash recovery.
        """

        # delete election records for elections initiated at this height and
        # elections concluded at this height
        self.delete_elections(new_height)

        txns = [self.get_transaction(tx_id) for tx_id in txn_ids]

        elections = self._get_votes(txns)
        for election_id in elections:
            election = self.get_transaction(election_id)
            if election.operation == VALIDATOR_ELECTION:
                # TODO change to `new_height + 2` when upgrading to Tendermint 0.24.0.
                self.delete_validator_set(new_height + 1)
            if election.operation == CHAIN_MIGRATION_ELECTION:
                self.delete_abci_chain(new_height)

    def approve_election(self, election, new_height):
        """Override to update the database state according to the
        election rules. Consider the current database state to account for
        other concluded elections, if required.
        """
        if election.operation == CHAIN_MIGRATION_ELECTION:
            self.migrate_abci_chain()
        if election.operation == VALIDATOR_ELECTION:
            validator_updates = [election.assets[0]["data"]]
            curr_validator_set = self.get_validators(new_height)
            updated_validator_set = new_validator_set(curr_validator_set, validator_updates)

            updated_validator_set = [v for v in updated_validator_set if v["voting_power"] > 0]

            # TODO change to `new_height + 2` when upgrading to Tendermint 0.24.0.
            self.store_validator_set(new_height + 1, updated_validator_set)
            return encode_validator(election.assets[0]["data"])


Block = namedtuple("Block", ("app_hash", "height", "transactions"))
