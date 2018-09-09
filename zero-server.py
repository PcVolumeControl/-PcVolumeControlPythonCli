#!/usr/bin/env python

"""Loop indefinitely, announcing the service via zeroconf.
Use this to test clients.

call it like so:
python ./zero-server.py 192.168.1.99 3000
Just use the IP and port your server is advertising.

Even more data can be embedded in the properties of the ServiceInfo object.
"""

import argparse
import logging
import socket
from time import sleep
from zeroconf import ServiceInfo, Zeroconf


def main(parsed_args):
    """Advertise a service on the local subnet using mDNS."""

    # set the log level based on the verbosity they need.
    logging.basicConfig(level=logging.INFO)
    if parsed_args.verbose:
        logging.getLogger('zeroconf').setLevel(logging.DEBUG)

    portnum = int(parsed_args.port)

    info = ServiceInfo(type_="_http._tcp.local.",
                       name="pcvolumecontrol._http._tcp.local.",
                       address=socket.inet_aton(parsed_args.ip),
                       port=portnum,
                       weight=0,
                       priority=0,
                       properties={'missiles': 'armed'},
                       server="myservername.local.")

    zeroconf = Zeroconf()
    print("Service is now registered at: {}:{}, press Ctrl-C to exit...".format(parsed_args.ip, portnum))
    zeroconf.register_service(info)
    try:
        while True:
            sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        print("Unregistering...")
        zeroconf.unregister_service(info)
        zeroconf.close()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Advertise a service on the LAN using mDNS.')
    parser.add_argument('ip', action='store', help='IP address of the service')
    parser.add_argument('port', action='store', help='Port of the service')
    parser.add_argument('--verbose', '-v', action='store_true')

    args = parser.parse_args()

    main(args)
