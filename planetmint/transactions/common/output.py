# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

from functools import reduce

import base58
from cryptoconditions import ThresholdSha256, Ed25519Sha256, ZenroomSha256
from cryptoconditions import Fulfillment

from planetmint.transactions.common.exceptions import AmountError
from .utils import _fulfillment_to_details, _fulfillment_from_details


class Output(object):
    """An Output is used to lock an asset.

    Wraps around a Crypto-condition Condition.

        Attributes:
            fulfillment (:class:`cryptoconditions.Fulfillment`): A Fulfillment
                to extract a Condition from.
            public_keys (:obj:`list` of :obj:`str`, optional): A list of
                owners before a Transaction was confirmed.
    """

    MAX_AMOUNT = 9 * 10**18

    def __init__(self, fulfillment, public_keys=None, amount=1):
        """Create an instance of a :class:`~.Output`.

        Args:
            fulfillment (:class:`cryptoconditions.Fulfillment`): A
                Fulfillment to extract a Condition from.
            public_keys (:obj:`list` of :obj:`str`, optional): A list of
                owners before a Transaction was confirmed.
            amount (int): The amount of Assets to be locked with this
                Output.

        Raises:
            TypeError: if `public_keys` is not instance of `list`.
        """
        if not isinstance(public_keys, list) and public_keys is not None:
            raise TypeError("`public_keys` must be a list instance or None")
        if not isinstance(amount, int):
            raise TypeError("`amount` must be an int")
        if amount < 1:
            raise AmountError("`amount` must be greater than 0")
        if amount > self.MAX_AMOUNT:
            raise AmountError("`amount` must be <= %s" % self.MAX_AMOUNT)

        self.fulfillment = fulfillment
        self.amount = amount
        self.public_keys = public_keys

    def __eq__(self, other):
        # TODO: If `other !== Condition` return `False`
        return self.to_dict() == other.to_dict()

    def to_dict(self):
        """Transforms the object to a Python dictionary.

        Note:
            A dictionary serialization of the Input the Output was
            derived from is always provided.

        Returns:
            dict: The Output as an alternative serialization format.
        """
        # TODO FOR CC: It must be able to recognize a hashlock condition
        #              and fulfillment!
        condition = {}
        try:
            # TODO verify if a script is returned in case of zenroom fulfillments
            condition["details"] = _fulfillment_to_details(self.fulfillment)
        except AttributeError:
            pass

        try:
            condition["uri"] = self.fulfillment.condition_uri
        except AttributeError:
            condition["uri"] = self.fulfillment

        output = {
            "public_keys": self.public_keys,
            "condition": condition,
            "amount": str(self.amount),
        }
        return output

    @classmethod
    def generate(cls, public_keys, amount):
        """Generates a Output from a specifically formed tuple or list.

        Note:
            If a ThresholdCondition has to be generated where the threshold
            is always the number of subconditions it is split between, a
            list of the following structure is sufficient:

            [(address|condition)*, [(address|condition)*, ...], ...]

        Args:
            public_keys (:obj:`list` of :obj:`str`): The public key of
                the users that should be able to fulfill the Condition
                that is being created.
            amount (:obj:`int`): The amount locked by the Output.

        Returns:
            An Output that can be used in a Transaction.

        Raises:
            TypeError: If `public_keys` is not an instance of `list`.
            ValueError: If `public_keys` is an empty list.
        """
        threshold = len(public_keys)
        if not isinstance(amount, int):
            raise TypeError("`amount` must be a int")
        if amount < 1:
            raise AmountError("`amount` needs to be greater than zero")
        if not isinstance(public_keys, list):
            raise TypeError("`public_keys` must be an instance of list")
        if len(public_keys) == 0:
            raise ValueError("`public_keys` needs to contain at least one" "owner")
        elif len(public_keys) == 1 and not isinstance(public_keys[0], list):
            if isinstance(public_keys[0], Fulfillment):
                ffill = public_keys[0]
            elif isinstance(public_keys[0], ZenroomSha256):
                ffill = ZenroomSha256(public_key=base58.b58decode(public_keys[0]))
            else:
                ffill = Ed25519Sha256(public_key=base58.b58decode(public_keys[0]))
            return cls(ffill, public_keys, amount=amount)
        else:
            initial_cond = ThresholdSha256(threshold=threshold)
            threshold_cond = reduce(cls._gen_condition, public_keys, initial_cond)
            return cls(threshold_cond, public_keys, amount=amount)

    @classmethod
    def _gen_condition(cls, initial, new_public_keys):
        """Generates ThresholdSha256 conditions from a list of new owners.

        Note:
            This method is intended only to be used with a reduce function.
            For a description on how to use this method, see
            :meth:`~.Output.generate`.

        Args:
            initial (:class:`cryptoconditions.ThresholdSha256`):
                A Condition representing the overall root.
            new_public_keys (:obj:`list` of :obj:`str`|str): A list of new
                owners or a single new owner.

        Returns:
            :class:`cryptoconditions.ThresholdSha256`:
        """
        try:
            threshold = len(new_public_keys)
        except TypeError:
            threshold = None

        if isinstance(new_public_keys, list) and len(new_public_keys) > 1:
            ffill = ThresholdSha256(threshold=threshold)
            reduce(cls._gen_condition, new_public_keys, ffill)
        elif isinstance(new_public_keys, list) and len(new_public_keys) <= 1:
            raise ValueError("Sublist cannot contain single owner")
        else:
            try:
                new_public_keys = new_public_keys.pop()
            except AttributeError:
                pass
            # NOTE: Instead of submitting base58 encoded addresses, a user
            #       of this class can also submit fully instantiated
            #       Cryptoconditions. In the case of casting
            #       `new_public_keys` to a Ed25519Fulfillment with the
            #       result of a `TypeError`, we're assuming that
            #       `new_public_keys` is a Cryptocondition then.
            if isinstance(new_public_keys, Fulfillment):
                ffill = new_public_keys
            else:
                ffill = Ed25519Sha256(public_key=base58.b58decode(new_public_keys))
        initial.add_subfulfillment(ffill)
        return initial

    @classmethod
    def from_dict(cls, data):
        """Transforms a Python dictionary to an Output object.

        Note:
            To pass a serialization cycle multiple times, a
            Cryptoconditions Fulfillment needs to be present in the
            passed-in dictionary, as Condition URIs are not serializable
            anymore.

        Args:
            data (dict): The dict to be transformed.

        Returns:
            :class:`~planetmint.transactions.common.transaction.Output`
        """
        try:
            fulfillment = _fulfillment_from_details(data["condition"]["details"])
        except KeyError:
            # NOTE: Hashlock condition case
            fulfillment = data["condition"]["uri"]
        try:
            amount = int(data["amount"])
        except ValueError:
            raise AmountError("Invalid amount: %s" % data["amount"])
        return cls(fulfillment, data["public_keys"], amount)
