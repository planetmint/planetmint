

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
