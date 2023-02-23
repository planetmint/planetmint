import json

from packaging import version
from transactions.common.crypto import key_pair_from_ed25519_key

from planetmint.abci.tendermint_utils import key_from_base64
from planetmint.version import __tm_supported_versions__


def load_node_key(path):
    with open(path) as json_data:
        priv_validator = json.load(json_data)
        priv_key = priv_validator["priv_key"]["value"]
        hex_private_key = key_from_base64(priv_key)
        return key_pair_from_ed25519_key(hex_private_key)


def tendermint_version_is_compatible(running_tm_ver):
    """
    Check Tendermint compatability with Planetmint server

    :param running_tm_ver: Version number of the connected Tendermint instance
    :type running_tm_ver: str
    :return: True/False depending on the compatability with Planetmint server
    :rtype: bool
    """

    # Splitting because version can look like this e.g. 0.22.8-40d6dc2e
    tm_ver = running_tm_ver.split("-")
    if not tm_ver:
        return False
    for ver in __tm_supported_versions__:
        if version.parse(ver) == version.parse(tm_ver[0]):
            return True
    return False
