#!/usr/bin/env python

"""Don't have a Windows box to test with? This is a mock server for pcvc.
This can be used to test clients. This will attempt to mimic the TCP stack
of the actual server.
"""


import json
import sys
import socket
import socketserver
from threading import Thread

SERVER_PROTO_VERSION = 6

startstate = {
                "version": 6,
                "deviceIds": {
                    "0f4090a9-dee2-4563-ba29-0ad6b93d9e22": "Speakers (Realtek High Definition Audio)",
                    "c5a32106-264d-40b2-a2e0-74eda397454c": "Headphones (Rift Audio)",
                    "c98e4030-926b-4e62-8c83-1c529574cc51": "Headset (5- USB Audio Device)"
                },
                "defaultDevice": {
                    "deviceId": "0f4090a9-dee2-4563-ba29-0ad6b93d9e22",
                    "name": "Speakers (Realtek High Definition Audio)",
                    "masterVolume": 80.0,
                    "masterMuted": False,
                    "sessions": [
                        {
                            "name": "OVRServer_x64",
                            "id": "{0.0.0.00000000}.{0f4090a9-dee2-4563-ba29-0ad6b93d9e22}|\\Device\\HarddiskVolume2\\Program Files\\Oculus\\Support\\oculus-runtime\\OVRServer_x64.exe%b{00000000-0000-0000-0000-000000000000}",
                            "volume": 77.0,
                            "muted": False
                        },
                        {
                            "name": "Steam Client Bootstrapper",
                            "id": "{0.0.0.00000000}.{0f4090a9-dee2-4563-ba29-0ad6b93d9e22}|\\Device\\HarddiskVolume2\\Program Files (x86)\\Steam\\Steam.exe%b{00000000-0000-0000-0000-000000000000}",
                            "volume": 83.0,
                            "muted": False
                        },
                        {
                            "name": "qemu-system-i386",
                            "id": "{0.0.0.00000000}.{0f4090a9-dee2-4563-ba29-0ad6b93d9e22}|\\Device\\HarddiskVolume2\\Users\\adamw\\AppData\\Local\\Android\\sdk\\emulator\\qemu\\windows-x86_64\\qemu-system-i386.exe%b{00000000-0000-0000-0000-000000000000}",
                            "volume": 100.0,
                            "muted": False
                        },
                        {
                            "name": "Google Chrome",
                            "id": "{0.0.0.00000000}.{0f4090a9-dee2-4563-ba29-0ad6b93d9e22}|\\Device\\HarddiskVolume2\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe%b{00000000-0000-0000-0000-000000000000}",
                            "volume": 35.0,
                            "muted": False
                        }
                    ]
                }
            }

class ParseError(Exception):
    pass

class FullState(object):
    """This represents a full state of sound components some Windows system as
    far as pcvg is concerned.
    """
    def __init__(self, seed):
        # starting state always starts with a seed to populate the class.
        self.seed = json.loads(json.dumps(seed))
        self.lastupdate = None

    def identify_update(self, update):
        """figure out what kind of update this is."""

        # default output device switched from one to another
        ddevice = update.get('defaultDevice')
        if len(ddevice) == 1:
            return "DEFAULT_NEW"

        # Mute or volume changed on the master output device
        if all([x for x in ddevice if x in ['masterMuted', 'masterVolume', 'deviceId']]):
            return "DEFAULT_MODIFIED"

        # Mute or volume changed on a session
        pass

    def parse_update(self, update):
        loaded = json.loads(update)
        self.validate_update(loaded)
        utype = self.identify_update(loaded)
        print(f"update was a :{utype}")


    def default_new(self):
        pass

    def default_modified(self):
        pass

    def session_modified(self):
        pass

    def validate_update(self, update):
        # version mismatch, newlines...
        if update['version'] != SERVER_PROTO_VERSION:
            raise RuntimeError("version mismatch!")
        if not update.get('defaultDevice'):
            raise RuntimeError('default device not in update!')
        return True

class ClientThread(Thread):
    """For a given client, give them a thread and attempt to encode/decode
    the JSON they send toward the server.

    Server behaviors:
    - On initial client connection:
        + Server sends the entire full state to client

    - On any incoming data from clients:
        + successfully-parsed client updates get a full state server reply.

    - Client is disconnected if:
        + client and server versions mismatch
        + client sends json which does not parse
        + client sends decodable message, but does not conform to pcvc protocol
        + [pcvc protocol] client sends message not ending in a newline (\n)
    """

    def __init__(self, conn, ip, port):
        Thread.__init__(self)
        self.ip = ip
        self.port = port
        self.conn = conn
        print(f"New client connected: {ip}:{port}")
        self.fullstate = startstate
        print("pushing initial state to client...")
        self.conn.send(f"{json.dumps(self.fullstate)}\n".encode())
        self.state = FullState(seed=startstate)

    def run(self):
        while True:
            try:
                data = self.conn.recv(1024)
                print("Server received data:", data)
                self.parse_payload(payload=data)
            except ParseError:
                # Tear down this client's connection.
                self.conn.close()
                break


    def parse_payload(self, payload):
        """This is where the server decodes the string to first see if it's
        valid JSON. Then we check for pcvc protocol-specific violations."""

        try:
            parsed = json.loads(payload)
        except json.decoder.JSONDecodeError:
            print("JSON payload sent from the client could not be parsed. Closing connection.")
            raise ParseError('JSON payload not decoded')
        else:
            # Do all server-side processing.
            # payload is bytes
            self.state.parse_update(update=payload)

            # we parsed it just fine. Now send back the new full state.
            self.conn.send(json.dumps(self.fullstate).encode())


class PCVCServer(object):
    """A TCP server which listens on a single IP:port and handles clients
    one per thread. This has no notion of pcvc state, only connection state.

    Note socket.SO_REUSEADDR is set to close out TCP sessions in FIN-WAIT which
    have not timed out yet. This allows the server to be stopped/started
    rapidly.
    """

    def __init__(self, host, port):
       self.host = host
       self.port = port

    def start(self):
        """Start the server socket. Every client gets their own thread."""
        print('Server starting up...')
        threads = []

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.host, self.port))
            s.listen(1)

            while True:
                c, (ip, port) = s.accept()
                newthread = ClientThread(c, ip, port)
                newthread.start()
                threads.append(newthread)

            for t in threads:
                t.join()

    def stop(self):
        s.close()


if __name__ == "__main__":
    HOST, PORT = "localhost", 3000

    server = PCVCServer(HOST, PORT)
    try:
        server.start()
    except KeyboardInterrupt:
        sys.exit(1)
