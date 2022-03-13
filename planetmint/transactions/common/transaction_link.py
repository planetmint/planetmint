# Copyright © 2020 Interplanetary Database Association e.V.,
# Planetmint and IPDB software contributors.
# SPDX-License-Identifier: (Apache-2.0 AND CC-BY-4.0)
# Code is Apache-2.0 and docs are CC-BY-4.0

class TransactionLink(object):
    """An object for unidirectional linking to a Transaction's Output.

        Attributes:
            txid (str, optional): A Transaction to link to.
            output (int, optional): An output's index in a Transaction with id
            `txid`.
    """

    def __init__(self, txid=None, output=None):
        """Create an instance of a :class:`~.TransactionLink`.

            Note:
                In an IPLD implementation, this class is not necessary anymore,
                as an IPLD link can simply point to an object, as well as an
                objects properties. So instead of having a (de)serializable
                class, we can have a simple IPLD link of the form:
                `/<tx_id>/transaction/outputs/<output>/`.

            Args:
                txid (str, optional): A Transaction to link to.
                output (int, optional): An Outputs's index in a Transaction with
                    id `txid`.
        """
        self.txid = txid
        self.output = output

    def __bool__(self):
        return self.txid is not None and self.output is not None

    def __eq__(self, other):
        # TODO: If `other !== TransactionLink` return `False`
        return self.to_dict() == other.to_dict()

    def __hash__(self):
        return hash((self.txid, self.output))

    @classmethod
    def from_dict(cls, link):
        """Transforms a Python dictionary to a TransactionLink object.

            Args:
                link (dict): The link to be transformed.

            Returns:
                :class:`~planetmint.transactions.common.transaction.TransactionLink`
        """
        try:
            return cls(link['transaction_id'], link['output_index'])
        except TypeError:
            return cls()

    def to_dict(self):
        """Transforms the object to a Python dictionary.

            Returns:
                (dict|None): The link as an alternative serialization format.
        """
        if self.txid is None and self.output is None:
            return None
        else:
            return {
                'transaction_id': self.txid,
                'output_index': self.output,
            }

    def to_uri(self, path=''):
        if self.txid is None and self.output is None:
            return None
        return '{}/transactions/{}/outputs/{}'.format(path, self.txid,
                                                      self.output)
