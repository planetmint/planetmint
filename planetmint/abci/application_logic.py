# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

"""This module contains all the goodness to integrate Planetmint
with Tendermint.
"""
import logging
import sys

from abci.application import BaseApplication
from abci.application import OkCode

from tendermint.abci import types_pb2
from tendermint.abci.types_pb2 import (
    ResponseInfo,
    ResponseInitChain,
    ResponseCheckTx,
    ResponseDeliverTx,
    ResponseBeginBlock,
    ResponseEndBlock,
    ResponseCommit,
)

from planetmint.application.validator import Validator
from planetmint.abci.utils import decode_validator, decode_transaction, calculate_hash
from planetmint.abci.block import Block
from planetmint.ipc.events import EventTypes, Event
from planetmint.backend.exceptions import DBConcurrencyError

CodeTypeError = 1
logger = logging.getLogger(__name__)


class ApplicationLogic(BaseApplication):
    """Bridge between Planetmint and Tendermint.

    The role of this class is to expose the Planetmint
    transaction logic to Tendermint Core.
    """

    def __init__(
        self,
        validator: Validator = None,
        events_queue=None,
    ):
        # super().__init__(abci)
        logger.debug("Checking values of types")
        logger.debug(dir(types_pb2))
        self.events_queue = events_queue
        self.validator = validator if validator else Validator()
        self.block_txn_ids = []
        self.block_txn_hash = ""
        self.block_transactions = []
        self.validators = None
        self.new_height = None
        self.chain = self.validator.models.get_latest_abci_chain()

    def log_abci_migration_error(self, chain_id, validators):
        logger.error(
            "An ABCI chain migration is in process. "
            "Download the self.planetmint_node.get_latest_abci_chain new ABCI client and configure it with "
            f"chain_id={chain_id} and validators={validators}."
        )

    def abort_if_abci_chain_is_not_synced(self):
        if self.chain is None or self.chain["is_synced"]:
            return
        validators = self.validator.models.get_validators()
        self.log_abci_migration_error(self.chain["chain_id"], validators)
        sys.exit(1)

    def init_chain(self, genesis):
        """Initialize chain upon genesis or a migration"""
        app_hash = ""
        height = 0
        try:
            known_chain = self.validator.models.get_latest_abci_chain()
            if known_chain is not None:
                chain_id = known_chain["chain_id"]

                if known_chain["is_synced"]:
                    msg = (
                        f"Got invalid InitChain ABCI request ({genesis}) - " f"the chain {chain_id} is already synced."
                    )
                    logger.error(msg)
                    sys.exit(1)
                if chain_id != genesis.chain_id:
                    validators = self.validator.models.get_validators()
                    self.log_abci_migration_error(chain_id, validators)
                    sys.exit(1)
                # set migration values for app hash and height
                block = self.validator.models.get_latest_block()
                app_hash = "" if block is None else block["app_hash"]
                height = 0 if block is None else block["height"] + 1
            known_validators = self.validator.models.get_validators()
            validator_set = [decode_validator(v) for v in genesis.validators]
            if known_validators and known_validators != validator_set:
                self.log_abci_migration_error(known_chain["chain_id"], known_validators)
                sys.exit(1)
            block = Block(app_hash=app_hash, height=height, transactions=[])
            self.validator.models.store_block(block._asdict())
            self.validator.models.store_validator_set(height + 1, validator_set)
            abci_chain_height = 0 if known_chain is None else known_chain["height"]
            self.validator.models.store_abci_chain(abci_chain_height, genesis.chain_id, True)
            self.chain = {
                "height": abci_chain_height,
                "is_synced": True,
                "chain_id": genesis.chain_id,
            }
        except DBConcurrencyError:
            sys.exit(1)
        except ValueError:
            sys.exit(1)
        return ResponseInitChain()

    def info(self, request):
        """Return height of the latest committed block."""

        self.abort_if_abci_chain_is_not_synced()

        # Check if Planetmint supports the Tendermint version
        # if not (hasattr(request, 'version') and tendermint_version_is_compatible(request.version)):
        #    logger.error(f'Unsupported Tendermint version: {getattr(request, "version", "no version")}.'
        #                 f' Currently, Planetmint only supports {__tm_supported_versions__}. Exiting!')
        #    sys.exit(1)

        # logger.info(f"Tendermint version: {request.version}")

        r = ResponseInfo()
        block = None
        try:
            block = self.validator.models.get_latest_block()
        except DBConcurrencyError:
            block = None
        except ValueError:
            block = None
        if block:
            chain_shift = 0 if self.chain is None else self.chain["height"]
            r.last_block_height = block["height"] - chain_shift
            r.last_block_app_hash = block["app_hash"].encode("utf-8")
        else:
            r.last_block_height = 0
            r.last_block_app_hash = b""
        return r

    def check_tx(self, raw_transaction):
        """Validate the transaction before entry into
        the mempool.

        Args:
            raw_tx: a raw string (in bytes) transaction.
        """

        self.abort_if_abci_chain_is_not_synced()

        logger.debug("check_tx: %s", raw_transaction)
        transaction = decode_transaction(raw_transaction)
        try:
            if self.validator.is_valid_transaction(transaction):
                logger.debug("check_tx: VALID")
                return ResponseCheckTx(code=OkCode)
            else:
                logger.debug("check_tx: INVALID")
                return ResponseCheckTx(code=CodeTypeError)
        except DBConcurrencyError:
            sys.exit(1)
        except ValueError:
            sys.exit(1)

    def begin_block(self, req_begin_block):
        """Initialize list of transaction.
        Args:
            req_begin_block: block object which contains block header
            and block hash.
        """
        self.abort_if_abci_chain_is_not_synced()

        chain_shift = 0 if self.chain is None else self.chain["height"]
        # req_begin_block.header.num_txs not found, so removing it.
        logger.debug("BEGIN BLOCK, height:%s", req_begin_block.header.height + chain_shift)

        self.block_txn_ids = []
        self.block_transactions = []
        return ResponseBeginBlock()

    def deliver_tx(self, raw_transaction):
        """Validate the transaction before mutating the state.

        Args:
            raw_tx: a raw string (in bytes) transaction.
        """

        self.abort_if_abci_chain_is_not_synced()

        logger.debug("deliver_tx: %s", raw_transaction)
        transaction = None
        try:
            transaction = self.validator.is_valid_transaction(
                decode_transaction(raw_transaction), self.block_transactions
            )
        except DBConcurrencyError:
            sys.exit(1)
        except ValueError:
            sys.exit(1)

        if not transaction:
            logger.debug("deliver_tx: INVALID")
            return ResponseDeliverTx(code=CodeTypeError)
        else:
            logger.debug("storing tx")
            self.block_txn_ids.append(transaction.id)
            self.block_transactions.append(transaction)
            return ResponseDeliverTx(code=OkCode)

    def end_block(self, request_end_block):
        """Calculate block hash using transaction ids and previous block
        hash to be stored in the next block.

        Args:
            height (int): new height of the chain.
        """

        self.abort_if_abci_chain_is_not_synced()

        chain_shift = 0 if self.chain is None else self.chain["height"]
        height = request_end_block.height + chain_shift
        self.new_height = height

        # store pre-commit state to recover in case there is a crash during
        # `end_block` or `commit`
        logger.debug(f"Updating pre-commit state: {self.new_height}")
        pre_commit_state = dict(height=self.new_height, transactions=self.block_txn_ids)
        try:
            self.validator.models.store_pre_commit_state(pre_commit_state)

            block_txn_hash = calculate_hash(self.block_txn_ids)
            block = self.validator.models.get_latest_block()

            logger.debug("BLOCK: ", block)

            if self.block_txn_ids:
                self.block_txn_hash = calculate_hash([block["app_hash"], block_txn_hash])
            else:
                self.block_txn_hash = block["app_hash"]

            validator_update = self.validator.process_block(self.new_height, self.block_transactions)
        except DBConcurrencyError:
            sys.exit(1)
        except ValueError:
            sys.exit(1)

        return ResponseEndBlock(validator_updates=validator_update)

    def commit(self):
        """Store the new height and along with block hash."""

        self.abort_if_abci_chain_is_not_synced()

        data = self.block_txn_hash.encode("utf-8")
        try:
            # register a new block only when new transactions are received
            if self.block_txn_ids:
                self.validator.models.store_bulk_transactions(self.block_transactions)

            block = Block(
                app_hash=self.block_txn_hash,
                height=self.new_height,
                transactions=self.block_txn_ids,
            )
            # NOTE: storing the block should be the last operation during commit
            # this effects crash recovery. Refer BEP#8 for details
            self.validator.models.store_block(block._asdict())
        except DBConcurrencyError:
            sys.exit(1)
        except ValueError:
            sys.exit(1)

        logger.debug(
            "Commit-ing new block with hash: apphash=%s ," "height=%s, txn ids=%s",
            data,
            self.new_height,
            self.block_txn_ids,
        )

        if self.events_queue:
            event = Event(
                EventTypes.BLOCK_VALID,
                {
                    "height": self.new_height,
                    "hash": self.block_txn_hash,
                    "transactions": self.block_transactions,
                },
            )
            self.events_queue.put(event)

        return ResponseCommit(data=data)
