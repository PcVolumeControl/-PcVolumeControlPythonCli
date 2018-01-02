#!/usr/bin/env python

"""This is a PC Volume Control Python client.
"""

__version__ = 6

import argparse
from pprint import pprint
import json
import readline
import socket
import sys
import time

class MyCompleter(object):
    """An autocomplete widget thingy because hey why not"""
    def __init__(self, options):
        self.options = sorted(options)

    def complete(self, text, state):
        if state == 0:  # on first trigger, build possible matches
            if text:  # cache matches (entries that start with entered text)
                self.matches = [s for s in self.options
                                if s and s.startswith(text)]
            else:  # no text entered, all matches possible
                self.matches = self.options[:]

        # return match indexed by state
        try:
            return self.matches[state]
        except IndexError:
            return None

class PcvgClient(object):
    """A TCP Client used to interact with PC Volume Control"""
    state = None
    def __init__(self, servername, port):
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.servername = servername
        self.port = port
        self.connected = False
        self.server_version = None

    def connect(self):
        """Open a socket with the target. This will get an immediate response
        with the full state. Populate this object with the initial state.
        """
        self.client.connect((self.servername, self.port))
        buff, bufsize = [], 1024
        while True:
            data = self.client.recv(bufsize).decode()
            buff.append(data)
            if data.endswith('\n'):
                break
        response = ''.join(buff)
        self.state = json.loads(response)
        self.server_version = self.state.get('version')
        if self.server_version != __version__:
            raise RuntimeError(f'Version mismatch: client({__version__}) and server{self.server_version}!')
        self.connected = True

    def push_update(self, data):
        """Push an update over to the server.
        Take in a regular dict and convert/encode to JSON for sending.
        Updates require the version and device id.
        """
        jstring = json.dumps(data)
        # data going out has to be bytes-encoded.
        print("JSON string being sent to the server:\n")
        pprint(jstring)
        self.client.send(jstring.encode())

    def disconnect(self):
        self.client.close()
        self.connected = False

    def toggle_master_mute(self):
        """For the master device, toggle its mute button."""
        master_device_id = self.state['defaultDevice']['deviceId']
        new_state = not self.state['defaultDevice']['masterMuted']
        update = {'version': __version__,
                  'defaultDevice': {'deviceId': master_device_id,
                                    'masterMuted': new_state}}

        self.push_update(data=update)

    def toggle_session_mute(self, session):
        master_device_id = self.state['defaultDevice']['deviceId']

        # 'session' can be a case-insensitive substring in the session name.
        # There can be one or many sessions with this name.
        targeted_sessions = [d for d in self.state['defaultDevice']['sessions'] if session.lower() in d.get('name').lower()]

        for tgt in targeted_sessions:
            tgt['muted'] = not tgt['muted']
        update = {'version': __version__,
                  'defaultDevice': {'deviceId': master_device_id,
                                    'sessions': targeted_sessions}}
        for x in targeted_sessions:
            print(f"Session ({x.get('name')}) changed muted value to ({x.get('muted')})")

        self.push_update(data=update)

    def __repr__(self):
        return f'Connected: {self.connected}, Host: {self.servername}:{self.port}, Server Version: {self.server_version}'

    def change_master_volume(self, newvolume):
        master_device_id = self.state['defaultDevice']['deviceId']
        update = {'version': __version__,
                  'defaultDevice': {'deviceId': master_device_id,
                                    'masterVolume': float(newvolume)}}

        self.push_update(data=update)

    def change_session_volume(self, session, newvolume):
        targeted_sessions = [d for d in self.state['defaultDevice']['sessions'] if session.lower() in d.get('name').lower()]

        for tgt in targeted_sessions:
            tgt['volume'] = float(newvolume)
        master_device_id = self.state['defaultDevice']['deviceId']

        update = {'version': __version__,
                  'defaultDevice': {'deviceId': master_device_id,
                                    'sessions': targeted_sessions}}
        for x in targeted_sessions:
            print(f"Session ({x.get('name')}) changed volume value to ({x.get('volume')})")

        self.push_update(data=update)


def main(arguments):
    """Run the volume control client."""

    if arguments.watch:
        try:
            while True:
                print(chr(27) + "[2J")  # clear screen
                my_client = PcvgClient(servername=arguments.server_name, port=arguments.server_port)
                my_client.connect()
                pprint(my_client.state)
                my_client.disconnect()
                time.sleep(0.5)
        except KeyboardInterrupt:
            print('Exiting...')

    if arguments.interactive:
        # play around
        commands = ['toggle', 'volume', 't', 'v', 'sessions', 'scary']
        completer = MyCompleter(commands)
        readline.set_completer(completer.complete)
        readline.parse_and_bind('tab: complete')
        while True:
            my_client = PcvgClient(servername=arguments.server_name, port=arguments.server_port)
            my_client.connect()
            # pprint(my_client.state)
            sessions = my_client.state['defaultDevice']['sessions']
            command = input('what do? > ')
            params = command.split()
            try:
                if params[0] not in commands:
                    print(f'The commands available are: {commands}')
                    continue

                if params[0] in ['toggle', 't']:
                    if params[1] == 'master':
                        # mute or unmute mster
                        my_client.toggle_master_mute()
                    else:
                        # It's a session to mute.
                        my_client.toggle_session_mute(params[1])
                if params[0] in ['volume', 'v']:
                    # Change the volume to a certain amount.
                    if params[1] == 'master':
                        my_client.change_master_volume(params[2])
                    else:
                        my_client.change_session_volume(session=params[1], newvolume=params[2])
                if params[0] == 'sessions':
                    # Just dump all the sessions.
                    pprint(my_client.state['defaultDevice']['sessions'])
                if params[0] == 'scary':
                    # Just allow them to send whatever they paste into the terminal.
                    unsanitized_frightening_input = input('Enter some JSONt to send:')
                    my_client.push_update(unsanitized_frightening_input)
                    pprint(my_client.state)

            except IndexError:
                print('There was a problem with your command. Maybe add arguments?')
                print(f'The commands available are: {commands}')
            except KeyboardInterrupt:
                sys.exit()
            finally:
                # disconnect and reconnect to get new state from the server
                my_client.disconnect()



if __name__ == '__main__':
    # parse arguments on the command line.
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('server_name', help='server FQDN or IP')
    parser.add_argument('-p', action='store', dest='server_port', help='server listening TCP port, defaults to 3000', default=3000)
    parser.add_argument('-w', action='store_true', dest='watch', help='Just watch the server state.')
    parser.add_argument('-i', action='store_true', dest='interactive', help='Run in interactive mode for server testing.')
    args = parser.parse_args()
    main(args)
