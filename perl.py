import json
import socket

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

class Perl(object):
    def __init__(self, port):
        self.identity = 'client'

        self.socket = socket.create_connection(('localhost', port))
        self.transport = self.socket.makefile()

        # Serializer
        self.encoder = PerlJSONEncoder(self)
        self.decoder = PerlJSONDecoder(self)

        # Objects registry
        self.objects = []

        # Continuation stack
        self.stack = []

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
