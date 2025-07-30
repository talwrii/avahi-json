#!/usr/bin/env python3
import sys
import json
import dbus
import dbus.mainloop.glib
import logging
from gi.repository import GLib

logging.basicConfig(level=logging.INFO)

# Avahi constants
AVAHI_PROTO_UNSPEC = -1
AVAHI_IF_UNSPEC = -1

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 test-resolve.py '{\"interface\": 3, \"protocol\": 1, \"transport\": \"_tcp\", \"domain\": \"local\", \"name\": \"_smb\"}'")
        sys.exit(1)

    # Parse JSON input
    try:
        data = json.loads(sys.argv[1])
        interface = data.get("interface", AVAHI_IF_UNSPEC)
        protocol = data.get("protocol", AVAHI_PROTO_UNSPEC)
        transport = data.get("transport", "_tcp")
        domain = data.get("domain", "local")
        name = data.get("name")
        if not name:
            raise ValueError("Missing 'name' in input JSON")
    except Exception as e:
        print(f"Error parsing input JSON: {e}")
        sys.exit(1)

    service_type = f"{name}.{transport}"

    # Setup main loop
    dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
    loop = GLib.MainLoop()

    bus = dbus.SystemBus()
    avahi_server = bus.get_object('org.freedesktop.Avahi', '/')
    server = dbus.Interface(avahi_server, 'org.freedesktop.Avahi.Server')

    sb_path = server.ServiceBrowserNew(
        interface,
        protocol,
        service_type,
        domain,
        dbus.UInt32(0)
    )

    service_browser = dbus.Interface(
        bus.get_object('org.freedesktop.Avahi', sb_path),
        'org.freedesktop.Avahi.ServiceBrowser'
    )

    def resolve_service(interface, protocol, name, stype, domain):
        logging.info(f"Resolving service: {name}.{stype}.{domain}...")
        server.ResolveService(
            interface,
            protocol,
            name,
            stype,
            domain,
            AVAHI_PROTO_UNSPEC,
            dbus.UInt32(0),
            reply_handler=print_resolved_service,
            error_handler=print_error
        )

    def print_resolved_service(*args):
        (
            interface,
            protocol,
            name,
            stype,
            domain,
            host,
            aprotocol,
            address,
            port,
            txt,
            flags,
        ) = args
        print(f"\nResolved service '{name}':")
        print(f"  Hostname: {host}")
        print(f"  Address:  {address}")
        print(f"  Port:     {port}")
        print("  TXT:")
        for entry in txt:
            print(f"    {entry}")

    def print_error(e):
        print("\n--- Service Resolution Error! ---")
        print("Error:", e)

    def item_new(interface, protocol, name, stype, domain, flags):
        logging.info(f"Discovered service: {name}.{stype} in domain {domain}")
        resolve_service(interface, protocol, name, stype, domain)

    service_browser.connect_to_signal('ItemNew', item_new)

    print(f"Browsing for '{service_type}' services...")

    def quit_loop_after_timeout():
        print("\nTimeout reached: stopping service browsing.")
        loop.quit()
        return False

    GLib.timeout_add_seconds(5, quit_loop_after_timeout)

    try:
        loop.run()
    except KeyboardInterrupt:
        print("Exiting...")

if __name__ == "__main__":
    main()
