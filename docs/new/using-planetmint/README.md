

# Basic usage

## Transactions in Planetmint

In Planetmint, _transactions_ are used to register, issue, create or transfer
things (e.g. assets).

Transactions are the most basic kind of record stored by Planetmint. There are
two kinds: CREATE transactions and TRANSFER transactions.

You can view the transaction specifications in Github, which describe transaction components and the conditions they have to fulfill in order to be valid. 

[Planetmint Transactions Specs](https://github.com/bigchaindb/BEPs/tree/master/13/)

### CREATE Transactions

A CREATE transaction can be used to register, issue, create or otherwise
initiate the history of a single thing (or asset) in Planetmint. For example,
one might register an identity or a creative work. The things are often called
"assets" but they might not be literal assets.

Planetmint supports divisible assets as of Planetmint Server v0.8.0.
That means you can create/register an asset with an initial number of "shares."
For example, A CREATE transaction could register a truckload of 50 oak trees.
Each share of a divisible asset must be interchangeable with each other share;
the shares must be fungible.

A CREATE transaction can have one or more outputs.
Each output has an associated amount: the number of shares tied to that output.
For example, if the asset consists of 50 oak trees,
one output might have 35 oak trees for one set of owners,
and the other output might have 15 oak trees for another set of owners.

Each output also has an associated condition: the condition that must be met
(by a TRANSFER transaction) to transfer/spend the output.
Planetmint supports a variety of conditions.
For details, see
the section titled **Transaction Components: Conditions**
in the relevant
[Planetmint Transactions Spec](https://github.com/bigchaindb/BEPs/tree/master/13/).

![Example Planetmint CREATE transaction](./_static/CREATE_example.png)

Above we see a diagram of an example Planetmint CREATE transaction.
It has one output: Pam owns/controls three shares of the asset
and there are no other shares (because there are no other outputs).

Each output also has a list of all the public keys associated
with the conditions on that output.
Loosely speaking, that list might be interpreted as the list of "owners."
A more accurate word might be fulfillers, signers, controllers,
or transfer-enablers.
See the section titled **A Note about Owners**
in the relevant [Planetmint Transactions Spec](https://github.com/bigchaindb/BEPs/tree/master/13/).

A CREATE transaction must be signed by all the owners.
(If you're looking for that signature,
it's in the one "fulfillment" of the one input, albeit encoded.)

### TRANSFER Transactions

A TRANSFER transaction can transfer/spend one or more outputs
on other transactions (CREATE transactions or other TRANSFER transactions).
Those outputs must all be associated with the same asset;
a TRANSFER transaction can only transfer shares of one asset at a time.

Each input on a TRANSFER transaction connects to one output
on another transaction.
Each input must satisfy the condition on the output it's trying
to transfer/spend.

A TRANSFER transaction can have one or more outputs,
just like a CREATE transaction (described above).
The total number of shares coming in on the inputs must equal
the total number of shares going out on the outputs.

![Example Planetmint transactions](./_static/CREATE_and_TRANSFER_example.png)

Above we see a diagram of two example Planetmint transactions,
a CREATE transaction and a TRANSFER transaction.
The CREATE transaction is the same as in the earlier diagram.
The TRANSFER transaction spends Pam's output,
so the input on that TRANSFER transaction must contain a valid signature
from Pam (i.e. a valid fulfillment).
The TRANSFER transaction has two outputs:
Jim gets one share, and Pam gets the remaining two shares.

Terminology: The "Pam, 3" output is called a "spent transaction output"
and the "Jim, 1" and "Pam, 2" outputs are called "unspent transaction outputs"
(UTXOs).

**Example 1:** Suppose a red car is owned and controlled by Joe.
Suppose the current transfer condition on the car says
that any valid transfer must be signed by Joe.
Joe could build a TRANSFER transaction containing
an input with Joe's signature (to fulfill the current output condition)
plus a new output condition saying that any valid transfer
must be signed by Rae.

**Example 2:** Someone might construct a TRANSFER transaction
that fulfills the output conditions on four
previously-untransferred assets of the same asset type
e.g. paperclips. The amounts might be 20, 10, 45 and 25, say,
for a total of 100 paperclips.
The TRANSFER transaction would also set up new transfer conditions.
For example, maybe a set of 60 paperclips can only be transferred
if Gertrude signs, and a separate set of 40 paperclips can only be
transferred if both Jack and Kelly sign.
Note how the sum of the incoming paperclips must equal the sum
of the outgoing paperclips (100).

### Transaction Validity

When a node is asked to check if a transaction is valid, it checks several
things. This got documented by a BigchainDB post (previous version of Planetmint) at*The BigchainDB Blog*:
["What is a Valid Transaction in BigchainDB?"](https://blog.bigchaindb.com/what-is-a-valid-transaction-in-planetmint-9a1a075a9598)
(Note: That post was about Planetmint Server v1.0.0.)

## A Note on IPLD marshalling and CIDs

Planetmint utilizes IPLD (interplanetary linked data) marshalling and CIDs (content identifiers) to store and verify data.
Before submitting a transaction to the network the data is marshalled using [py-ipld](https://github.com/planetmint/py-ipld) and instead of the raw data a CID is stored on chain.

The CID is a self describing data structure. It contains information about the encoding, cryptographic algorithm, length and the actual hashvalue. For example the CID `bafybeigdyrzt5sfp7udm7hu76uh7y26nf3efuylqabf3oclgtqy55fbzdi` tells us the following:

```
Encoding: base32
Codec: dag-pb (MerkleDAG protobuf)
Hashing-Algorithm: sha2-256
Digest (Hex): C3C4733EC8AFFD06CF9E9FF50FFC6BCD2EC85A6170004BB709669C31DE94391A
```

With this information we can validate that information about an asset we've received is actually valid.


### Example Transactions

There are example Planetmint transactions in
[the HTTP API documentation](./connecting/http-client-server-api)
and
[the Python Driver documentation](./connecting/drivers).

## Contracts & Conditions

Planetmint has been developed with simple logical gateways in mind. The logic got introduced by [cryptoconditions](https://https://docs.planetmint.io/projects/cryptoconditions). The cryptocondition documentation contains all details about how conditoins are defined and how they can be verified and fulfilled. 

The integration of such into the transaction schema of Planetmint is shown below.

## Zenroom Smart Contracts and Policies

[Zenroom](https://zenroom.org/) was integrated into [cryptoconditions](https://https://docs.planetmint.io/projects/cryptoconditions) to allow for human-readable conditions and fulfillments.
At the moment these contracts can only be stateless, which implies that the conditions and fulfillments need to be transacted in the same transaction. However, [PRP-10](https://github.com/planetmint/PRPs/tree/main/10) aims to make stateful contracts possible, which enables asynchronous and party-independent processing of contracts.

As for network-wide or asset-based policies [PRP-11](https://github.com/planetmint/PRPs/tree/main/11) specifies how these can be implemented and how these can be used to verify a transaction state before it is commited to the network.
