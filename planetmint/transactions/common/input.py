# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

from cryptoconditions import Fulfillment
from cryptoconditions.exceptions import ASN1DecodeError, ASN1EncodeError

from planetmint.transactions.common.exceptions import InvalidSignature
from .utils import _fulfillment_to_details, _fulfillment_from_details
from .output import Output
from .transaction_link import TransactionLink


class Input(object):
    """A Input is used to spend assets locked by an Output.

    Wraps around a Crypto-condition Fulfillment.

        Attributes:
            fulfillment (:class:`cryptoconditions.Fulfillment`): A Fulfillment
                to be signed with a private key.
            owners_before (:obj:`list` of :obj:`str`): A list of owners after a
                Transaction was confirmed.
            fulfills (:class:`~planetmint.transactions.common.transaction. TransactionLink`,
                optional): A link representing the input of a `TRANSFER`
                Transaction.
    """

    def __init__(self, fulfillment, owners_before, fulfills=None):
        """Create an instance of an :class:`~.Input`.

            Args:
                fulfillment (:class:`cryptoconditions.Fulfillment`): A
                    Fulfillment to be signed with a private key.
                owners_before (:obj:`list` of :obj:`str`): A list of owners
                    after a Transaction was confirmed.
                fulfills (:class:`~planetmint.transactions.common.transaction.
                    TransactionLink`, optional): A link representing the input
                    of a `TRANSFER` Transaction.
        """
        if fulfills is not None and not isinstance(fulfills, TransactionLink):
            raise TypeError('`fulfills` must be a TransactionLink instance')
        if not isinstance(owners_before, list):
            raise TypeError('`owners_before` must be a list instance')

        self.fulfillment = fulfillment
        self.fulfills = fulfills
        self.owners_before = owners_before

    def __eq__(self, other):
        # TODO: If `other !== Fulfillment` return `False`
        return self.to_dict() == other.to_dict()

    # NOTE: This function is used to provide a unique key for a given
    # Input to suppliment memoization
    def __hash__(self):
        return hash((self.fulfillment, self.fulfills))

    def to_dict(self):
        """Transforms the object to a Python dictionary.

            Note:
                If an Input hasn't been signed yet, this method returns a
                dictionary representation.

            Returns:
                dict: The Input as an alternative serialization format.
        """
        try:
            fulfillment = self.fulfillment.serialize_uri()
        except (TypeError, AttributeError, ASN1EncodeError, ASN1DecodeError):
            fulfillment = _fulfillment_to_details(self.fulfillment)

        try:
            # NOTE: `self.fulfills` can be `None` and that's fine
            fulfills = self.fulfills.to_dict()
        except AttributeError:
            fulfills = None

        input_ = {
            'owners_before': self.owners_before,
            'fulfills': fulfills,
            'fulfillment': fulfillment,
        }
        return input_

    @classmethod
    def generate(cls, public_keys):
        # TODO: write docstring
        # The amount here does not really matter. It is only use on the
        # output data model but here we only care about the fulfillment
        output = Output.generate(public_keys, 1)
        return cls(output.fulfillment, public_keys)

    @classmethod
    def from_dict(cls, data):
        """Transforms a Python dictionary to an Input object.

            Note:
                Optionally, this method can also serialize a Cryptoconditions-
                Fulfillment that is not yet signed.

            Args:
                data (dict): The Input to be transformed.

            Returns:
                :class:`~planetmint.transactions.common.transaction.Input`

            Raises:
                InvalidSignature: If an Input's URI couldn't be parsed.
        """
        fulfillment = data['fulfillment']
        if not isinstance(fulfillment, (Fulfillment, type(None))):
            try:
                fulfillment = Fulfillment.from_uri(data['fulfillment'])
            except ASN1DecodeError:
                # TODO Remove as it is legacy code, and simply fall back on
                # ASN1DecodeError
                raise InvalidSignature("Fulfillment URI couldn't been parsed")
            except TypeError:
                # NOTE: See comment about this special case in
                #       `Input.to_dict`
                fulfillment = _fulfillment_from_details(data['fulfillment'])
        fulfills = TransactionLink.from_dict(data['fulfills'])
        return cls(fulfillment, data['owners_before'], fulfills)
