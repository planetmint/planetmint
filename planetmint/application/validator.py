import logging
import json

from collections import OrderedDict
from transactions import Transaction, Vote
from transactions.common.exceptions import (
    DoubleSpend,
    AssetIdMismatch,
    InvalidSignature,
    AmountError,
    SchemaValidationError,
    ValidationError,
    MultipleInputsError,
    DuplicateTransaction,
    InvalidProposer,
    UnequalValidatorSet,
    InvalidPowerChange,
)
from transactions.common.crypto import public_key_from_ed25519_key
from transactions.common.output import Output as TransactionOutput
from transactions.common.transaction import VALIDATOR_ELECTION, CHAIN_MIGRATION_ELECTION
from transactions.types.elections.election import Election
from transactions.types.elections.validator_utils import election_id_to_public_key

from planetmint.abci.utils import encode_validator, new_validator_set, key_from_base64, public_key_to_base64
from planetmint.application.basevalidationrules import BaseValidationRules
from planetmint.backend.models.output import Output
from planetmint.model.dataaccessor import DataAccessor
from planetmint.config import Config
from planetmint.config_utils import load_validation_plugin

logger = logging.getLogger(__name__)


class Validator:
    def __init__(self, async_io: bool = False):
        self.async_io = async_io
        self.models = DataAccessor(async_io=async_io)
        self.validation = Validator._get_validation_method()

    @staticmethod
    def _get_validation_method():
        validationPlugin = Config().get().get("validation_plugin")

        if validationPlugin:
            validation_method = load_validation_plugin(validationPlugin)
        else:
            validation_method = BaseValidationRules
        return validation_method

    @staticmethod
    def validate_inputs_distinct(tx: Transaction):
        # Validate that all inputs are distinct
        links = [i.fulfills.to_uri() for i in tx.inputs]
        if len(links) != len(set(links)):
            raise DoubleSpend('tx "{}" spends inputs twice'.format(tx.id))

    @staticmethod
    def validate_asset_id(tx: Transaction, input_txs: list):
        # validate asset
        if tx.operation != Transaction.COMPOSE:
            asset_id = tx.get_asset_id(input_txs)
            if asset_id != Transaction.read_out_asset_id(tx):
                raise AssetIdMismatch(
                    ("The asset id of the input does not" " match the asset id of the" " transaction")
                )
        else:
            asset_ids = Transaction.get_asset_ids(input_txs)
            if Transaction.read_out_asset_id(tx) in asset_ids:
                raise AssetIdMismatch(("The asset ID of the compose must be different to all of its input asset IDs"))

    @staticmethod
    def validate_input_conditions(tx: Transaction, input_conditions: list[Output]):
        # convert planetmint.Output objects to transactions.common.Output objects
        input_conditions_dict = Output.list_to_dict(input_conditions)
        input_conditions_converted = []
        for input_cond in input_conditions_dict:
            input_conditions_converted.append(TransactionOutput.from_dict(input_cond))

        if not tx.inputs_valid(input_conditions_converted):
            raise InvalidSignature("Transaction signature is invalid.")

    def validate_compose_inputs(self, tx, current_transactions=[]) -> bool:
        input_txs, input_conditions = self.models.get_input_txs_and_conditions(tx.inputs, current_transactions)

        Validator.validate_input_conditions(tx, input_conditions)

        Validator.validate_asset_id(tx, input_txs)

        Validator.validate_inputs_distinct(tx)

        return True

    def validate_transfer_inputs(self, tx, current_transactions=[]) -> bool:
        input_txs, input_conditions = self.models.get_input_txs_and_conditions(tx.inputs, current_transactions)

        Validator.validate_input_conditions(tx, input_conditions)

        Validator.validate_asset_id(tx, input_txs)

        Validator.validate_inputs_distinct(tx)

        input_amount = sum([input_condition.amount for input_condition in input_conditions])
        output_amount = sum([output_condition.amount for output_condition in tx.outputs])

        if output_amount != input_amount:
            raise AmountError(
                (
                    "The amount used in the inputs `{}`" " needs to be same as the amount used" " in the outputs `{}`"
                ).format(input_amount, output_amount)
            )

        return True

    def validate_create_inputs(self, tx, current_transactions=[]) -> bool:
        duplicates = any(txn for txn in current_transactions if txn.id == tx.id)
        if self.models.is_committed(tx.id) or duplicates:
            raise DuplicateTransaction("transaction `{}` already exists".format(tx.id))

        fulfilling_inputs = [i for i in tx.inputs if i.fulfills is not None and i.fulfills.txid is not None]

        if len(fulfilling_inputs) > 0:
            input_txs, input_conditions = self.models.get_input_txs_and_conditions(
                fulfilling_inputs, current_transactions
            )
            create_asset = tx.assets[0]
            input_asset = input_txs[0].assets[tx.inputs[0].fulfills.output]["data"]
            if create_asset != input_asset:
                raise ValidationError("CREATE must have matching asset description with input transaction")
            if input_txs[0].operation != Transaction.DECOMPOSE:
                raise SchemaValidationError("CREATE can only consume DECOMPOSE outputs")

        return True

    def validate_transaction(self, transaction, current_transactions=[]):
        """Validate a transaction against the current status of the database."""

        # CLEANUP: The conditional below checks for transaction in dict format.
        # It would be better to only have a single format for the transaction
        # throught the code base.
        if isinstance(transaction, dict):
            try:
                transaction = Transaction.from_dict(transaction, False)
            except SchemaValidationError as e:
                logger.warning("Invalid transaction schema: %s", e.__cause__.message)
                return False
            except ValidationError as e:
                logger.warning("Invalid transaction (%s): %s", type(e).__name__, e)
                return False

        if transaction.operation == Transaction.CREATE:
            self.validate_create_inputs(transaction, current_transactions)
        elif transaction.operation in [Transaction.TRANSFER, Transaction.VOTE]:
            self.validate_transfer_inputs(transaction, current_transactions)
        elif transaction.operation in [Transaction.COMPOSE]:
            self.validate_compose_inputs(transaction, current_transactions)

        return transaction

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
        if self.models.is_committed(transaction.id) or duplicates:
            raise DuplicateTransaction("transaction `{}` already exists".format(transaction.id))

        current_validators = self.models.get_validators_dict()

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

    def validate_validator_election(self, transaction):  # TODO: move somewhere else
        """For more details refer BEP-21: https://github.com/planetmint/BEPs/tree/master/21"""

        current_validators = self.models.get_validators_dict()

        # NOTE: change more than 1/3 of the current power is not allowed
        if transaction.get_assets()[0]["data"]["power"] >= (1 / 3) * sum(current_validators.values()):
            raise InvalidPowerChange("`power` change must be less than 1/3 of total power")

    def get_election_status(self, transaction):
        election = self.models.get_election(transaction.id)
        if election and election["is_concluded"]:
            return Election.CONCLUDED

        return Election.INCONCLUSIVE if self.has_validator_set_changed(transaction) else Election.ONGOING

    def has_validator_set_changed(self, transaction):
        latest_change = self.get_validator_change()
        if latest_change is None:
            return False

        latest_change_height = latest_change["height"]

        election = self.models.get_election(transaction.id)

        return latest_change_height > election["height"]

    def get_validator_change(self):
        """Return the validator set from the most recent approved block

        :return: {
            'height': <block_height>,
            'validators': <validator_set>
        }
        """
        latest_block = self.models.get_latest_block()
        if latest_block is None:
            return None
        return self.models.get_validator_set(latest_block["height"])

    def get_validator_dict(self, height=None):
        """Return a dictionary of validators with key as `public_key` and
        value as the `voting_power`
        """
        validators = {}
        for validator in self.models.get_validators(height):
            # NOTE: we assume that Tendermint encodes public key in base64
            public_key = public_key_from_ed25519_key(key_from_base64(validator["public_key"]["value"]))
            validators[public_key] = validator["voting_power"]

        return validators

    # TODO to be moved to planetmint.commands.planetmint
    def show_election_status(self, transaction):
        data = transaction.assets[0]
        data = data.to_dict()["data"]
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

    # TODO to be moved to planetmint.commands.planetmint
    def append_chain_migration_status(self, status):
        chain = self.models.get_latest_abci_chain()
        if chain is None or chain["is_synced"]:
            return status

        status += f'\nchain_id={chain["chain_id"]}'
        block = self.models.get_latest_block()
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

    def get_recipients_list(self):
        """Convert validator dictionary to a recipient list for `Transaction`"""

        recipients = []
        for public_key, voting_power in self.get_validator_dict().items():
            recipients.append(([public_key], voting_power))

        return recipients

    def count_votes(self, election_pk, transactions):
        votes = 0
        for txn in transactions:
            if txn.operation == Vote.OPERATION:
                for output in txn.outputs:
                    # NOTE: We enforce that a valid vote to election id will have only
                    # election_pk in the output public keys, including any other public key
                    # along with election_pk will lead to vote being not considered valid.
                    if len(output.public_keys) == 1 and [election_pk] == output.public_keys:
                        votes = votes + output.amount
        return votes

    def get_commited_votes(self, transaction, election_pk=None):  # TODO: move somewhere else
        if election_pk is None:
            election_pk = election_id_to_public_key(transaction.id)
        txns = self.models.get_asset_tokens_for_public_key(transaction.id, election_pk)
        return self.count_votes(election_pk, txns)

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
            election_id = Transaction.read_out_asset_id(tx)
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
            self.models.store_elections(initiated_elections)

        # elections voted for in this block and their votes
        elections = self._get_votes(txns)

        validator_update = None
        for election_id, votes in elections.items():
            election = self.models.get_transaction(election_id)
            if election is None:
                continue

            if not self.has_election_concluded(election, votes):
                continue

            validator_update = self.approve_election(election, new_height)
            self.models.store_election(election.id, new_height, is_concluded=True)

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

        total_votes = sum(int(output.amount) for output in transaction.outputs)
        if (votes_committed < (2 / 3) * total_votes) and (votes_committed + votes_current >= (2 / 3) * total_votes):
            return True

        return False

    def has_validator_election_concluded(self):  # TODO: move somewhere else
        latest_block = self.models.get_latest_block()
        if latest_block is not None:
            latest_block_height = latest_block["height"]
            latest_validator_change = self.models.get_validator_set()["height"]

            # TODO change to `latest_block_height + 3` when upgrading to Tendermint 0.24.0.
            if latest_validator_change == latest_block_height + 2:
                # do not conclude the election if there is a change assigned already
                return False

        return True

    def has_chain_migration_concluded(self):  # TODO: move somewhere else
        chain = self.models.get_latest_abci_chain()
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
        self.models.delete_elections(new_height)

        txns = [self.models.get_transaction(tx_id) for tx_id in txn_ids]

        txns = [Transaction.from_dict(tx.to_dict()) for tx in txns if tx]

        elections = self._get_votes(txns)
        for election_id in elections:
            election = self.models.get_transaction(election_id)
            if election.operation == VALIDATOR_ELECTION:
                # TODO change to `new_height + 2` when upgrading to Tendermint 0.24.0.
                self.models.delete_validator_set(new_height + 1)
            if election.operation == CHAIN_MIGRATION_ELECTION:
                self.models.delete_abci_chain(new_height)

    def approve_election(self, election, new_height):
        """Override to update the database state according to the
        election rules. Consider the current database state to account for
        other concluded elections, if required.
        """
        if election.operation == CHAIN_MIGRATION_ELECTION:
            self.migrate_abci_chain()
        if election.operation == VALIDATOR_ELECTION:
            validator_updates = [election.assets[0].data]
            curr_validator_set = self.models.get_validators(new_height)
            updated_validator_set = new_validator_set(curr_validator_set, validator_updates)

            updated_validator_set = [v for v in updated_validator_set if v["voting_power"] > 0]

            # TODO change to `new_height + 2` when upgrading to Tendermint 0.24.0.
            self.models.store_validator_set(new_height + 1, updated_validator_set)
            return encode_validator(election.assets[0].data)

    def is_valid_transaction(self, tx, current_transactions=[]):
        # NOTE: the function returns the Transaction object in case
        # the transaction is valid
        try:
            return self.validate_transaction(tx, current_transactions)
        except ValidationError as e:
            logger.warning("Invalid transaction (%s): %s", type(e).__name__, e)
            return False

    def migrate_abci_chain(self):
        """Generate and record a new ABCI chain ID. New blocks are not
        accepted until we receive an InitChain ABCI request with
        the matching chain ID and validator set.

        Chain ID is generated based on the current chain and height.
        `chain-X` => `chain-X-migrated-at-height-5`.
        `chain-X-migrated-at-height-5` => `chain-X-migrated-at-height-21`.

        If there is no known chain (we are at genesis), the function returns.
        """
        latest_chain = self.models.get_latest_abci_chain()
        if latest_chain is None:
            return

        block = self.models.get_latest_block()

        suffix = "-migrated-at-height-"
        chain_id = latest_chain["chain_id"]
        block_height_str = str(block["height"])
        new_chain_id = chain_id.split(suffix)[0] + suffix + block_height_str

        self.models.store_abci_chain(block["height"] + 1, new_chain_id, False)

    def rollback(self):
        pre_commit = None

        try:
            pre_commit = self.models.get_pre_commit_state()
        except Exception as e:
            logger.exception("Unexpected error occurred while executing get_pre_commit_state()", e)

        if pre_commit is None or len(pre_commit) == 0:
            # the pre_commit record is first stored in the first `end_block`
            return

        latest_block = self.models.get_latest_block()
        if latest_block is None:
            logger.error("Found precommit state but no blocks!")
            sys.exit(1)

        # NOTE: the pre-commit state is always at most 1 block ahead of the commited state
        if latest_block["height"] < pre_commit["height"]:
            self.rollback_election(pre_commit["height"], pre_commit["transactions"])
            self.models.delete_transactions(pre_commit["transactions"])
