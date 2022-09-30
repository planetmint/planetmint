

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
