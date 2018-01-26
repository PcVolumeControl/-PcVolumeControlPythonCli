#!/usr/bin/env python

"""Loop indefinitely, announcing the service via zeroconf.
Use this to test clients.

call it like so:
python ./zero-server.py 192.168.1.99 3000
Just use the IP and port your server is advertising.

Even more data can be embedded in the properties of the ServiceInfo object.
"""

import logging
import socket
import sys
from time import sleep

from zeroconf import ServiceInfo, Zeroconf

THE_SERVER_IP = sys.argv[1]
THE_SERVER_PORT = int(sys.argv[2])

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    if len(sys.argv) > 3:
        assert sys.argv[3:] == ['--debug']
        logging.getLogger('zeroconf').setLevel(logging.DEBUG)

    # docs:
    # https://github.com/jstasiak/python-zeroconf/blob/master/zeroconf.py#L1363


    desc = {'missiles': 'armed'}

    info = ServiceInfo(type_="_http._tcp.local.",
                       name="pcvolumecontrol._http._tcp.local.",
                       address=socket.inet_aton(THE_SERVER_IP),
                       port=THE_SERVER_PORT,
                       weight=0,
                       priority=0,
					   properties=desc,
					   server="myservername.local.")


    zeroconf = Zeroconf()
    print("Registration of a service, press Ctrl-C to exit...")
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
