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

### Status posts

You can publish short status updates that are stored in the DHT. Use:

```bash
python social_p2p.py --username alice --post "Hello world"
```

Fetch posts from another user with `--get-posts bob`.

<<<< codex/build-client-side-social-media-platform

## GUI

A small Tkinter based interface is provided in `social_gui.py`. It works on
Windows, Linux and macOS using the built in `ttk` widgets. The program will try
to use the Windows *vista* theme when running on Windows and falls back to a
portable theme on other platforms.

Start the GUI with:

```bash
python social_gui.py
```

The first time you launch the application it will ask for a folder to store
profile backups and whether the program should continue running in the
background when the window is closed. Once a profile has been created the
application will automatically sign in using the saved data.

### Web interface

For a more modern look you can run the optional Flask web GUI:

```bash
python web_gui.py
```

Open `http://localhost:5000` in your browser to log in and post updates.

### Command line usage (for debugging)

The command line script can still be used for experimenting with the network:

```bash
python social_p2p.py --username alice --port 8468
```

## FAQ

**Where is my profile stored?**  By default a folder named `.p2psocial` is
created in your home directory. This folder holds your configuration file and a
backup of your profile data which can be copied for safekeeping.

**How do I restore my account?**  Place your saved profile JSON back into the
data folder and ensure the configuration file points to the same username. The
program will automatically load it on start.

**Is there a browser based UI?**  Yes, run `python web_gui.py` and open
`http://localhost:5000` to use the web interface.

## Technical Notes

The network layer relies on the `kademlia` package to publish profile details
and exchange messages using a DHT. The desktop GUI is built with Tkinter and
can optionally minimize to the system tray using `pystray`. A lightweight Flask
server serves the web interface using HTML templates.
