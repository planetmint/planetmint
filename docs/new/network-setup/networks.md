

# Planetmint Networks

A **Planetmint network** is a set of connected **Planetmint nodes**, managed by a **Planetmint consortium** (i.e. an organization). Those terms are defined in the [Planetmint Terminology page](https://docs.planetmint.io/en/latest/terminology.html).

## Consortium Structure & Governance

The consortium might be a company, a foundation, a cooperative, or [some other form of organization](https://en.wikipedia.org/wiki/Organizational_structure).
It must make many decisions, e.g. How will new members be added? Who can read the stored data? What kind of data will be stored?
A governance process is required to make those decisions, and therefore one of the first steps for any new consortium is to specify its governance process (if one doesn't already exist).
This documentation doesn't explain how to create a consortium, nor does it outline the possible governance processes.

It's worth noting that the decentralization of a Planetmint network depends,
to some extent, on the decentralization of the associated consortium. See the pages about [decentralization](https://docs.planetmint.io/en/latest/decentralized.html) and [node diversity](https://docs.planetmint.io/en/latest/diversity.html).

## DNS Records and SSL Certificates

We now describe how *we* set up the external (public-facing) DNS records for a Planetmint network. Your consortium may opt to do it differently.
There were several goals:

* Allow external users/clients to connect directly to any Planetmint node in the network (over the internet), if they want.
* Each Planetmint node operator should get an SSL certificate for their Planetmint node, so that their Planetmint node can serve the [Planetmint HTTP API](../connecting/http-client-server-api) via HTTPS. (The same certificate might also be used to serve the [WebSocket API](../connecting/websocket-event-stream-api).)
* There should be no sharing of SSL certificates among Planetmint node operators.
* Optional: Allow clients to connect to a "random" Planetmint node in the network at one particular domain (or subdomain).

### Node Operator Responsibilities

1. Register a domain (or use one that you already have) for your Planetmint node. You can use a subdomain if you like. For example, you might opt to use `abc-org73.net`, `api.dynabob8.io` or `figmentdb3.ninja`.
2. Get an SSL certificate for your domain or subdomain, and properly install it in your node (e.g. in your NGINX instance).
3. Create a DNS A Record mapping your domain or subdomain to the public IP address of your node (i.e. the one that serves the Planetmint HTTP API).

### Consortium Responsibilities

Optional: The consortium managing the Planetmint network could register a domain name and set up CNAME records mapping that domain name (or one of its subdomains) to each of the nodes in the network. For example, if the consortium registered `bdbnetwork.io`, they could set up CNAME records like the following:

* CNAME record mapping `api.bdbnetwork.io` to `abc-org73.net`
* CNAME record mapping `api.bdbnetwork.io` to `api.dynabob8.io`
* CNAME record mapping `api.bdbnetwork.io` to `figmentdb3.ninja`
