# avahi-json
**@readwithai** - [X](https://x.com/readwithai) - [blog](https://readwithai.substack.com/) - [machine-aided reading](https://www.reddit.com/r/machineAidedReading/) - [📖](https://readwithai.substack.com/p/what-is-reading-broadly-defined
)[⚡️](https://readwithai.substack.com/s/technical-miscellany)[🖋️](https://readwithai.substack.com/p/note-taking-with-obsidian-much-of)

Query the local network for devices and services using MDNS bia avahi (like `avahi-browser -ar`) but output results in easy-to-use JSON.

## Motivation
I have an Android phone on my home network. I also KDE connect on the phone. I occassionally want to connect to it via ADB over a TCP connection. But the IP address is not reliable. However, I can use KDE connect to find the device since KDE connect advertises itself using an MDNS services (i.e. avahi). All well and good - but the avahi command-line does not allow the querying I need and does not (really) output machine readable data. I am surprised that no one has written this before.

Therefore I am writing something which queries for services on the network using avahi and outputs theresult in beautiful JSON.

## Installation
You must first install the `python3-avahi` bindings. These are handled by `apt` on ubuntu and can be installed with `sudo apt install python3-avahi`

You can install `avahi-json` itself using [pipx](https://github.com/pypa/pipx) with the following command (`--system-site-packages` is needed for avahi and dbus).

```
pipx install --system-site-packages avahi-json
```

You need to have avahi, Linux's mdns daemon, installed to use this. But this tends to be installed by default.

## Usage
Run `avahi-json` this will give you services on the network using JSON.

## About me
I am **@readwithai**. I create tools for reading, research and agency sometimes using the markdown editor [Obsidian](https://readwithai.substack.com/p/what-exactly-is-obsidian).

I also create a [stream of tools](https://readwithai.substack.com/p/my-productivity-tools) that are related to carrying out my work.

I write about lots of things - including tools like this - on [X](https://x.com/readwithai).
My [blog](https://readwithai.substack.com/) is more about reading and research and agency.
