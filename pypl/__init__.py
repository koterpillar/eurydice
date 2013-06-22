from functools import wraps

import json

import socket
import SocketServer


class RemoteObject(object):
    def __init__(self, remote, ref):
        self.remote = remote
        self.ref = ref

    def __getattr__(self, method):
        return lambda *args: self.remote.call(self.ref, method, *args)


class RemoteError(Exception):
    pass


class RemoteJSONEncoder(json.JSONEncoder):
    def __init__(self, endpoint):
        super(RemoteJSONEncoder, self).__init__()
        self.endpoint = endpoint

    def default(self, obj):
        if isinstance(obj, RemoteObject):
            return obj.ref

        index = len(self.endpoint.objects)
        self.endpoint.objects.append(obj)

        return {
            '_remote_proxy': index,
            'instance': self.endpoint.identity,
        }

class RemoteJSONDecoder(json.JSONDecoder):
    def __init__(self, endpoint):
        super(RemoteJSONDecoder, self).__init__(object_hook=self.decode_object)
        self.endpoint = endpoint

    def decode_object(self, obj):
        if isinstance(obj, dict):
            if '_remote_proxy' in obj:
                if obj['instance'] == self.endpoint.identity:
                    return self.endpoint.objects[obj['_remote_proxy']]
                else:
                    return RemoteObject(self.endpoint, obj)
        return obj


def callback(func):
    @wraps(func)
    def decorated(self, *args):
        try:
            val = func(self, *args)
            returned = True
        except Exception, e:
            returned = False

        if returned:
            self._send('return', val)
        else:
            self._send('error', str(e))
        return self._receive()
    return decorated


class Endpoint(object):
    def __init__(self, transport, identity):
        # Serializer
        self.encoder = RemoteJSONEncoder(self)
        self.decoder = RemoteJSONDecoder(self)

        # Objects registry
        self.objects = []

        self.transport = transport

        self.identity = identity

    def _send(self, command, *args):
        line = self.encoder.encode([command] + list(args))
        print >>self.transport, line
        self.transport.flush()

    def _receive(self):
        line = self.transport.readline()

        line = self.decoder.decode(line)
        command = line[0]
        args = line[1:]

        command_function = 'command_%s' % command
        if hasattr(self, command_function):
            return getattr(self, command_function)(*args)
        raise InvalidCommand(command)

    def _send_receive(self, command, *args):
        self._send(command, *args)
        return self._receive()

    def use(self, module):
        return self._send_receive('import', module)

    def get_global(self, obj):
        return self._send_receive('global', obj)

    def call(self, obj, method, *args):
        return self._send_receive('call', obj, method, *args)

    @callback
    def command_call(self, obj, method, *args):
        return getattr(obj, method)(*args)

    @callback
    def command_global(self, obj):
        return globals()[obj]

    @callback
    def command_import(self, module):
        return __import__(module)

    def command_error(self, err):
        raise RemoteError(err)

    def command_return(self, value):
        return value


class ServerEndpoint(Endpoint):
    def __init__(self, sock):
        super(ServerEndpoint, self).__init__(sock, 'server')

    def run(self):
        while True:
            self._receive()


class ServerHandler(SocketServer.StreamRequestHandler):
    def handle(self):
        endpoint = ServerEndpoint(self.rfile)
        endpoint.run()


class Server(SocketServer.TCPServer, object):
    def __init__(self, port):
        super(Server, self).__init__(('localhost', port), ServerHandler)


class Client(Endpoint):
    def __init__(self, host, port):
        self.socket = socket.create_connection((host, port))
        super(Client, self).__init__(self.socket.makefile(), 'client')

    def close(self):
        self.socket.shutdown()
