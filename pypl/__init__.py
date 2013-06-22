import json

import socket
import SocketServer


class PerlClass(object):
    def __init__(self, perl, name):
        self.perl = perl
        self.name = name

    def __getattr__(self, method):
        return lambda *args: self.perl.call(self.name, method, *args)

    def __call__(self, *args):
        return self.new(*args)

class PerlObject(object):
    def __init__(self, perl, ref):
        self.perl = perl
        self.ref = ref

    def __getattr__(self, method):
        return lambda *args: self.perl.call(self.ref, method, *args)

class PerlError(Exception):
    pass

class PerlJSONEncoder(json.JSONEncoder):
    def __init__(self, perl):
        super(PerlJSONEncoder, self).__init__()
        self.perl = perl

    def default(self, obj):
        if isinstance(obj, PerlObject):
            return obj.ref
        elif isinstance(obj, PerlClass):
            return obj.name

        index = len(self.perl.objects)
        self.perl.objects.append(obj)

        return { 'pyproxy': index }

class PerlJSONDecoder(json.JSONDecoder):
    def __init__(self, perl):
        super(PerlJSONDecoder, self).__init__(object_hook=self.decode_object)
        self.perl = perl

    def decode_object(self, obj):
        if isinstance(obj, dict):
            if 'plproxy' in obj:
                return PerlObject(self.perl, obj)
            elif 'pyproxy' in obj:
                return self.perl.objects[obj['pyproxy']]
        return obj


class Endpoint(object):
    def __init__(self, transport, identity):
        # Serializer
        self.encoder = PerlJSONEncoder(self)
        self.decoder = PerlJSONDecoder(self)

        # Objects registry
        self.objects = []

        self.transport = transport

        self.identity = identity

    def use(self, module):
        self._send('use', module)
        return self._run()

    def klass(self, cls):
        return PerlClass(self, cls)

    def call(self, obj, method, *args):
        self._send('call', obj, method, *args)
        return self._run()

    COMMANDS = {
        'call': 'callback',
        'error': 'error',
        'return': 'ret',
        'useok': 'useok',
    }

    def _send(self, command, *args):
        line = self.encoder.encode([command] + list(args))
        print >>self.transport, line
        self.transport.flush()

    def _run(self):
        # TODO: rename this
        line = self.transport.readline()

        line = self.decoder.decode(line)
        command = line[0]
        args = line[1:]

        if command in self.COMMANDS:
            return getattr(self, self.COMMANDS[command])(*args)
        else:
            # TODO: custom exception
            raise Exception("Transport exception")

    def callback(self, obj, method, *args):
        try:
            val = getattr(obj, method)(*args)
            returned = True
        except Exception, e:
            returned = False

        if returned:
            self._send('return', val)
        else:
            self._send('error', str(e))
        return self._run()

    def error(self, err):
        raise PerlError(err)

    def ret(self, value):
        return value

    def useok(self, *args):
        return


class ServerEndpoint(Endpoint):
    def __init__(self, sock):
        super(ServerEndpoint, self).__init__(sock, 'server')

    def run(self):
        while True:
            self._run()


class ServerHandler(SocketServer.StreamRequestHandler):
    def handle(self):
        endpoint = ServerEndpoint(self.rfile)
        endpoint.run()


class Server(SocketServer.TCPServer, object):
    def __init__(self, port):
        super(Server, self).__init__(('localhost', port), ServerHandler)


class Client(Endpoint):
    def __init__(self, host, port):
        sock = socket.create_connection((host, port))
        transport = sock.makefile()

        super(Client, self).__init__(transport, 'client')
