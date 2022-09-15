# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

from planetmint.transactions.common.transaction import Transaction
from planetmint.transactions.common.input import Input
from planetmint.transactions.common.output import Output


class Create(Transaction):

    OPERATION = "CREATE"
    ALLOWED_OPERATIONS = (OPERATION,)

    @classmethod
    def validate_create(self, tx_signers, recipients, asset, metadata):
        if not isinstance(tx_signers, list):
            raise TypeError("`tx_signers` must be a list instance")
        if not isinstance(recipients, list):
            raise TypeError("`recipients` must be a list instance")
        if len(tx_signers) == 0:
            raise ValueError("`tx_signers` list cannot be empty")
        if len(recipients) == 0:
            raise ValueError("`recipients` list cannot be empty")
        if not asset is None:
            if not isinstance(asset, dict):
                raise TypeError("`asset` must be a CID string or None")
            if "data" in asset and not isinstance(asset["data"], str):
                raise TypeError("`asset` must be a CID string or None")
            import cid

            cid.make_cid(asset["data"])
        if not (metadata is None or isinstance(metadata, str)):
            # add check if metadata is ipld marshalled CID string
            raise TypeError("`metadata` must be a CID string or None")

        return True

    @classmethod
    def generate(cls, tx_signers, recipients, metadata=None, asset=None):
        """A simple way to generate a `CREATE` transaction.

        Note:
            This method currently supports the following Cryptoconditions
            use cases:
                - Ed25519
                - ThresholdSha256

            Additionally, it provides support for the following Planetmint
            use cases:
                - Multiple inputs and outputs.

        Args:
            tx_signers (:obj:`list` of :obj:`str`): A list of keys that
                represent the signers of the CREATE Transaction.
            recipients (:obj:`list` of :obj:`tuple`): A list of
                ([keys],amount) that represent the recipients of this
                Transaction.
            metadata (dict): The metadata to be stored along with the
                Transaction.
            asset (dict): The metadata associated with the asset that will
                be created in this Transaction.

        Returns:
            :class:`~planetmint.common.transaction.Transaction`
        """

        Create.validate_create(tx_signers, recipients, asset, metadata)
        (inputs, outputs) = Transaction.complete_tx_i_o(tx_signers, recipients)
        return cls(cls.OPERATION, asset, inputs, outputs, metadata)
