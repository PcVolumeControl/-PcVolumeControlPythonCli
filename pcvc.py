#!/usr/bin/env python

"""PC Volume Control Python client
Everything is in one place right now. Running this file should open a window used
to control the volume on the target.
"""

__version__ = 2

from pprint import pprint
import json
import socket
import sys
import time

class PcvgClient(object):
    state = None
    def __init__(self, host, port=3000):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.host = host
        self.port = port
        self.connected = False
        self.server_version = None

    def connect(self):
        """Open a socket with the target. This will get an immediate response
        with the full state. Populate this object with the initial state.
        """
        self.client.connect((self.host, self.port))
        response = self.client.recv(4096)
        self.state = json.loads(response)
        self.server_version = self.state.get('version')
        if self.server_version != __version__:
            raise RuntimeError(f'Version mismatch: client({__version__}) and server{self.server_version}!')
        self.connected = True

    def push_update(self, data):
        """Push an update over to the server."""
        self.client.send(data)

        # perhaps check if we get a reply. It would be helpful.
        # response = self.client.recv(4096)
        # self.state = json.loads(response)


    def disconnect(self):
        self.client.close()
        self.connected = False

    def __repr__(self):
        return f'Connected: {self.connected}, Host: {self.host}:{self.port}, Server Version: {self.server_version}'

test = PcvgClient('192.168.2.78')
test.connect()
pprint(test.state)

send = {'defaultDevice': {'deviceId': '{0.0.0.00000000}.{116d952a-14fb-4ef3-95b1-78a8442f9c96}',
                          'masterMuted': False,
                          'masterVolume': 0.23}}
jstring = json.dumps(send)
# data going out has to be bytes-encoded.
test.push_update(jstring.encode())
test.disconnect()
