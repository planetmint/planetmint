

# About Planetmint

## Basic Facts

1. One can store arbitrary data (including encrypted data) in a Planetmint network, within limits: there’s a maximum transaction size. Every transaction has a `metadata` section which can store almost any Unicode string (up to some maximum length). Similarly, every CREATE transaction has an `asset.data` section which can store almost any Unicode string.
2. The data stored in certain Planetmint transaction fields must not be encrypted, e.g. public keys and amounts. Planetmint doesn’t offer private transactions akin to Zcoin.
3. Once data has been stored in a Planetmint network, it’s best to assume it can’t be change or deleted.
4. Every node in a Planetmint network has a full copy of all the stored data.
5. Every node in a Planetmint network can read all the stored data.
6. Everyone with full access to a Planetmint node (e.g. the sysadmin of a node) can read all the data stored on that node.
7. Everyone given access to a node via the Planetmint HTTP API can find and read all the data stored by Planetmint. The list of people with access might be quite short.
8. If the connection between an external user and a Planetmint node isn’t encrypted (using HTTPS, for example), then a wiretapper can read all HTTP requests and responses in transit.
9. If someone gets access to plaintext (regardless of where they got it), then they can (in principle) share it with the whole world. One can make it difficult for them to do that, e.g. if it is a lot of data and they only get access inside a secure room where they are searched as they leave the room.

## Planetmint for Asset Registrations & Transfers

Planetmint can store data of any kind, but it’s designed to be particularly good for storing asset registrations and transfers:

* The fundamental thing that one sends to a Planetmint network, to be checked and stored (if valid), is a _transaction_, and there are two kinds: CREATE transactions and TRANSFER transactions.
* A CREATE transaction can be use to register any kind of asset (divisible or indivisible), along with arbitrary metadata.
* An asset can have zero, one, or several owners.
* The owners of an asset can specify (crypto-)conditions which must be satisfied by anyone wishing transfer the asset to new owners. For example, a condition might be that at least 3 of the 5 current owners must cryptographically sign a TRANSFER transaction.
* Planetmint verifies that the conditions have been satisfied as part of checking the validity of TRANSFER transactions. (Moreover, anyone can check that they were satisfied.)
* Planetmint prevents double-spending of an asset.
* Validated transactions are immutable.

**Note**

We used the word “owners” somewhat loosely above. A more accurate word might be fulfillers, signers, controllers, or transfer-enablers. See the section titled **A Note about Owners** in the relevant [Planetmint Transactions Spec](https://github.com/Planetmint/PRPs/tree/master/tx-specs/).


## Production-Ready?

Depending on your use case, Planetmint may or may not be production-ready. You should ask your service provider. If you want to go live (into production) with Planetmint, please consult with your service provider.

Note: Planetmint has an open source license with a “no warranty” section that is typical of open source licenses. This is standard in the software industry. For example, the Linux kernel is used in production by billions of machines even though its license includes a “no warranty” section. Warranties are usually provided above the level of the software license, by service providers.

## Storing Private Data Off-Chain

A system could store data off-chain, e.g. in a third-party database, document store, or content management system (CMS) and it could use Planetmint to:

* Keep track of who has read permissions (or other permissions) in a third-party system. An example of how this could be done is described below.
* Keep a permanent record of all requests made to the third-party system.
* Store hashes of documents-stored-elsewhere, so that a change in any document can be detected.
* Record all handshake-establishing requests and responses between two off-chain parties (e.g. a Diffie-Hellman key exchange), so as to prove that they established an encrypted tunnel (without giving readers access to that tunnel). There are more details about this idea in [the Privacy Protocols repository](https://github.com/Planetmint/privacy-protocols).

A simple way to record who has read permission on a particular document would be for the third-party system (“DocPile”) to store a CREATE transaction in a Planetmint network for every document+user pair, to indicate that that user has read permissions for that document. The transaction could be signed by DocPile (or maybe by a document owner, as a variation). The asset data field would contain 1) the unique ID of the user and 2) the unique ID of the document. The one output on the CREATE transaction would only be transferable/spendable by DocPile (or, again, a document owner).

To revoke the read permission, DocPile could create a TRANSFER transaction, to spend the one output on the original CREATE transaction, with a metadata field to say that the user in question no longer has read permission on that document.

This can be carried on indefinitely, i.e. another TRANSFER transaction could be created by DocPile to indicate that the user now has read permissions again.

DocPile can figure out if a given user has read permissions on a given document by reading the last transaction in the CREATE → TRANSFER → TRANSFER → etc. chain for that user+document pair.

There are other ways to accomplish the same thing. The above is just one example.

You might have noticed that the above example didn’t treat the “read permission” as an asset owned (controlled) by a user because if the permission asset is given to (transferred to or created by) the user then it cannot be controlled any further (by DocPile) until the user transfers it back to DocPile. Moreover, the user could transfer the asset to someone else, which might be problematic.

## Storing Private Data On-Chain, Encrypted

There are many ways to store private data on-chain, encrypted. Every use case has its own objectives and constraints, and the best solution depends on the use case. [The IPDB consulting team](mailto:contact%40ipdb.global) can help you design the best solution for your use case.

Below we describe some example system setups, using various crypto primitives, to give a sense of what’s possible.

Please note:

* Ed25519 keypairs are designed for signing and verifying cryptographic signatures, [not for encrypting and decrypting messages](https://crypto.stackexchange.com/questions/27866/why-curve25519-for-encryption-but-ed25519-for-signatures). For encryption, you should use keypairs designed for encryption, such as X25519.
* If someone (or some group) publishes how to decrypt some encrypted data on-chain, then anyone with access to that encrypted data will be able to get the plaintext. The data can’t be deleted.
* Encrypted data can’t be indexed or searched by MongoDB. (It can index and search the ciphertext, but that’s not very useful.) One might use homomorphic encryption to index and search encrypted data, but MongoDB doesn’t have any plans to support that any time soon. If there is indexing or keyword search needed, then some fields of the `asset.data` or `metadata` objects can be left as plain text and the sensitive information can be stored in an encrypted child-object.

## Examples 

### System Example 1

Encrypt the data with a symmetric key and store the ciphertext on-chain (in `metadata` or `asset.data`). To communicate the key to a third party, use their public key to encrypt the symmetric key and send them that. They can decrypt the symmetric key with their private key, and then use that symmetric key to decrypt the on-chain ciphertext.

The reason for using a symmetric key along with public/private keypairs is so the ciphertext only has to be stored once.

### System Example 2

This example uses [proxy re-encryption](https://en.wikipedia.org/wiki/Proxy\_re-encryption):

1. MegaCorp encrypts some data using its own public key, then stores that encrypted data (ciphertext 1) in a Planetmint network.
2. MegaCorp wants to let others read that encrypted data, but without ever sharing their private key and without having to re-encrypt themselves for every new recipient. Instead, they find a “proxy” named Moxie, to provide proxy re-encryption services.
3. Zorban contacts MegaCorp and asks for permission to read the data.
4. MegaCorp asks Zorban for his public key.
5. MegaCorp generates a “re-encryption key” and sends it to their proxy, Moxie.
6. Moxie (the proxy) uses the re-encryption key to encrypt ciphertext 1, creating ciphertext 2.
7. Moxie sends ciphertext 2 to Zorban (or to MegaCorp who forwards it to Zorban).
8. Zorban uses his private key to decrypt ciphertext 2, getting the original un-encrypted data.

{% hint style="info" %}
**Note**

* The proxy only ever sees ciphertext. They never see any un-encrypted data.
* Zorban never got the ability to decrypt ciphertext 1, i.e. the on-chain data.
* There are variations on the above flow.
{% endhint %}

### System Example 3

This example uses [erasure coding](https://en.wikipedia.org/wiki/Erasure\_code):

1. Erasure-code the data into n pieces.
2. Encrypt each of the n pieces with a different encryption key.
3. Store the n encrypted pieces on-chain, e.g. in n separate transactions.
4. Share each of the the n decryption keys with a different party.

If k < N of the key-holders gets and decrypts k of the pieces, they can reconstruct the original plaintext. Less than k would not be enough.

### System Example 4

This setup could be used in an enterprise blockchain scenario where a special node should be able to see parts of the data, but the others should not.

* The special node generates an X25519 keypair (or similar asymmetric _encryption_ keypair).
* A Planetmint end user finds out the X25519 public key (encryption key) of the special node.
* The end user creates a valid Planetmint transaction, with either the asset.data or the metadata (or both) encrypted using the above-mentioned public key.
* This is only done for transactions where the contents of asset.data or metadata don’t matter for validation, so all node operators can validate the transaction.
* The special node is able to decrypt the encrypted data, but the other node operators can’t, and nor can any other end user.