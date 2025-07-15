# Experiment2

This repository contains a simple peer‑to‑peer social networking prototype. It is
implemented in Python using the [kademlia](https://github.com/bmuller/kademlia)
package for distributed hash table (DHT) storage.

## Setup

```bash
pip install -r requirements.txt
```

## Running

Each peer stores profile information and queued messages in the DHT. To start a
peer run:

```bash
python social_p2p.py --username alice --port 8468
```

To connect to an existing peer on another machine, specify the address of a
bootstrap node:

```bash
python social_p2p.py --username bob --port 8469 --bootstrap 192.0.2.10:8468
```

While running you can look up other users or send messages:

```bash
# On Alice's machine
python social_p2p.py --username alice --lookup bob --message "Hello!"

# On Bob's machine
python social_p2p.py --username bob --fetch
```

The script keeps running for an hour to maintain its connection to the network.
It only provides minimal functionality intended for experimentation.
