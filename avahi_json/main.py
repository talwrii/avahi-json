#!/usr/bin/env python3
import argparse
import json
import logging
import sys

# Check for dbus before other imports
try:
    import dbus
    import dbus.mainloop.glib
except ImportError:
    print("ERROR: dbus module not found.", file=sys.stderr)
    print("", file=sys.stderr)
    print("You need to install python3-avahi system package:", file=sys.stderr)
    print("  sudo apt install python3-avahi", file=sys.stderr)
    print("", file=sys.stderr)
    print("Then reinstall avahi-json with --system-site-packages:", file=sys.stderr)
    print("  pipx uninstall avahi-json", file=sys.stderr)
    print("  pipx install --system-site-packages avahi-json", file=sys.stderr)
    sys.exit(1)

from frozendict import frozendict
from gi.repository import GLib

# Avahi constants
AVAHI_PROTO_UNSPEC = -1
AVAHI_IF_UNSPEC = -1

dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
bus = dbus.SystemBus()
avahi_server = bus.get_object('org.freedesktop.Avahi', '/')
server = dbus.Interface(avahi_server, 'org.freedesktop.Avahi.Server')
main_loop = GLib.MainLoop()

service_types = set()
service_browsers = {}

def resolve_service(service_data):
    logging.debug(f"Resolving service: {service_data['name']}.{service_data['stype']}.{service_data['domain']}...")
    server.ResolveService(
        service_data["interface"],
        service_data["protocol"],
        service_data["name"],
        service_data["stype"],
        service_data["domain"],
        AVAHI_PROTO_UNSPEC,
        dbus.UInt32(0),
        reply_handler=print_resolved_service,
        error_handler=print_error
    )

def print_resolved_service(*args):
    keys = ("interface", "protocol", "name", "stype", "domain", "host", "aprotocol", "address", "port", "txt", "flags")
    resolved = dict(zip(keys, args))
    try:
        txt_strings = [bytes(entry).decode('utf-8', errors='replace') if hasattr(entry, '__iter__') else str(entry) for entry in resolved["txt"]]
    except Exception:
        txt_strings = [str(entry) for entry in resolved["txt"]]
    
    output = {
        "name": resolved["name"],
        "service_type": resolved["stype"],
        "domain": resolved["domain"],
        "host": resolved["host"],
        "address": resolved["address"],
        "port": resolved["port"],
        "txt": txt_strings,
        "flags": resolved["flags"]
    }
    print(json.dumps(output))

def print_error(e):
    logging.error("Service resolution error: %s", e)

def service_instance_found(interface, protocol, name, stype, domain, flags):
    service_data = {
        "interface": interface,
        "protocol": protocol,
        "name": name,
        "stype": stype,
        "domain": domain,
        "flags": flags
    }
    logging.debug(f"Discovered service instance: {name}.{stype} in domain {domain}")
    resolve_service(service_data)

def browse_service_type(interface, protocol, service_type, domain):
    logging.debug(f"Browsing for instances of service type: {service_type}")
    sb_path = server.ServiceBrowserNew(
        interface,
        protocol,
        service_type,
        domain,
        dbus.UInt32(0)
    )
    sb = dbus.Interface(
        bus.get_object('org.freedesktop.Avahi', sb_path),
        'org.freedesktop.Avahi.ServiceBrowser'
    )
    sb.connect_to_signal("ItemNew", service_instance_found)
    service_browsers[service_type] = sb

def service_type_found(interface, protocol, name, transport, domain, flags):
    del flags
    service_type = f"{name}.{transport}"
    if service_type not in service_types:
        service_types.add(service_type)
        browse_service_type(interface, protocol, service_type, domain)

def found_all_service_types():
    logging.debug("Finished browsing for service types.")
    if not service_types:
        logging.debug("No service types found, quitting.")
        main_loop.quit()

PARSER = argparse.ArgumentParser(description='Find services using MDNS (avahi) in machine readable JSON.', epilog="@readwithai 📖 https://readwithai.substack.com/ ⚡️ machine-aided reading ✒️")
PARSER.add_argument('--debug', action='store_true')
PARSER.add_argument('--timeout', type=int, default=5)

def main():
    args = PARSER.parse_args()
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)
    else:
        logging.basicConfig(level=logging.INFO)
    
    type_browser_path = server.ServiceBrowserNew(
        AVAHI_IF_UNSPEC,
        AVAHI_PROTO_UNSPEC,
        "_services._dns-sd._udp",
        "local",
        dbus.UInt32(0)
    )
    type_browser = dbus.Interface(
        bus.get_object('org.freedesktop.Avahi', type_browser_path),
        'org.freedesktop.Avahi.ServiceBrowser'
    )

    type_browser.connect_to_signal("ItemNew", service_type_found)
    type_browser.connect_to_signal("AllForNow", found_all_service_types)

    # Timeout after 10 seconds to quit even if not all resolved (adjust as needed)
    GLib.timeout_add_seconds(5, lambda: main_loop.quit())

    try:
        main_loop.run()
    except KeyboardInterrupt:
        logging.info("Interrupted by user, exiting.")