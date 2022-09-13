# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

from planetmint.transactions.common.transaction import Transaction
from planetmint.transactions.common.output import Output
from copy import deepcopy


class Transfer(Transaction):

    OPERATION = "TRANSFER"
    ALLOWED_OPERATIONS = (OPERATION,)

    @classmethod
    def validate_transfer(cls, inputs, recipients, asset_id, metadata):
        if not isinstance(inputs, list):
            raise TypeError("`inputs` must be a list instance")
        if len(inputs) == 0:
            raise ValueError("`inputs` must contain at least one item")
        if not isinstance(recipients, list):
            raise TypeError("`recipients` must be a list instance")
        if len(recipients) == 0:
            raise ValueError("`recipients` list cannot be empty")

        outputs = []
        for recipient in recipients:
            if not isinstance(recipient, tuple) or len(recipient) != 2:
                raise ValueError(
                    ("Each `recipient` in the list must be a" " tuple of `([<list of public keys>]," " <amount>)`")
                )
            pub_keys, amount = recipient
            outputs.append(Output.generate(pub_keys, amount))

        if not isinstance(asset_id, str):
            raise TypeError("`asset_id` must be a string")

        return (deepcopy(inputs), outputs)

    @classmethod
    def generate(cls, inputs, recipients, asset_id, metadata=None):
        """A simple way to generate a `TRANSFER` transaction.

        Note:
            Different cases for threshold conditions:

            Combining multiple `inputs` with an arbitrary number of
            `recipients` can yield interesting cases for the creation of
            threshold conditions we'd like to support. The following
            notation is proposed:

            1. The index of a `recipient` corresponds to the index of
               an input:
               e.g. `transfer([input1], [a])`, means `input1` would now be
                    owned by user `a`.

            2. `recipients` can (almost) get arbitrary deeply nested,
               creating various complex threshold conditions:
               e.g. `transfer([inp1, inp2], [[a, [b, c]], d])`, means
                    `a`'s signature would have a 50% weight on `inp1`
                    compared to `b` and `c` that share 25% of the leftover
                    weight respectively. `inp2` is owned completely by `d`.

        Args:
            inputs (:obj:`list` of :class:`~planetmint.common.transaction.
                Input`): Converted `Output`s, intended to
                be used as inputs in the transfer to generate.
            recipients (:obj:`list` of :obj:`tuple`): A list of
                ([keys],amount) that represent the recipients of this
                Transaction.
            asset_id (str): The asset ID of the asset to be transferred in
                this Transaction.
            metadata (dict): Python dictionary to be stored along with the
                Transaction.

        Returns:
            :class:`~planetmint.common.transaction.Transaction`
        """
        (inputs, outputs) = cls.validate_transfer(inputs, recipients, asset_id, metadata)
        return cls(cls.OPERATION, {"id": asset_id}, inputs, outputs, metadata)
