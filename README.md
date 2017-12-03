Use this to mess around with the PC Volume Control server running on a Windows box.

```
env $ ./pcvc.py -h
usage: pcvc.py [-h] [-p SERVER_PORT] [-w] [-i] server_name

This is a PC Volume Control Python client.

positional arguments:
  server_name     server FQDN or IP

optional arguments:
  -h, --help      show this help message and exit
  -p SERVER_PORT  server listening TCP port, defaults to 3000
  -w              Just watch the server state.
  -i              Run in interactive mode for server testing.
env $
```

Some examples...

**watch mode**

Just just connects to the server and updates whatever the server's state is at a given moment in time.

```
$ ./pcvc.py -w
<loads of JSON>
```

**interactive mode**

Just connect to the server IP or name and use the -i argument.

```
env $ ./pcvc.py 192.168.2.78 -i
what do? >
scary     sessions  t         toggle    v         volume
what do? > toggle master
JSON string being sent to the server:

('{"version": 5, "defaultDevice": {"deviceId": '
 '"0d33830e-d6f8-4883-8d41-a02d989d1621", "masterMuted": false}}')
what do? > volume master 50
JSON string being sent to the server:

('{"version": 5, "defaultDevice": {"deviceId": '
 '"0d33830e-d6f8-4883-8d41-a02d989d1621", "masterVolume": 50.0}}')
what do? > volume fire 20
Session (Firefox) changed volume value to (20.0)
JSON string being sent to the server:

('{"version": 5, "defaultDevice": {"deviceId": '
 '"0d33830e-d6f8-4883-8d41-a02d989d1621", "sessions": [{"name": "Firefox", '
 '"id": '
 '"{0.0.0.00000000}.{0d33830e-d6f8-4883-8d41-a02d989d1621}|\\\\Device\\\\HarddiskVolume6\\\\Program '
 'Files\\\\Mozilla '
 'Firefox\\\\firefox.exe%b{00000000-0000-0000-0000-000000000000}", "volume": '
 '20.0, "muted": false}]}}')
what do? >
```

Note there is tab-completion for the commands you can enter.