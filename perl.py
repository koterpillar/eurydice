import json
import socket

class PerlClass(object):
    def __init__(self, perl, name):
        self.perl = perl
        self.name = name

    def __getattr__(self, method):
        return lambda *args: self.perl.callvirt(self.name, method, *args)

    def __call__(self, *args):
        return self.new(*args)

class PerlObject(object):
    def __init__(self, perl, ref):
        self.perl = perl
        self.ref = ref

    def __getattr__(self, method):
        return lambda *args: self.perl.callvirt(self.ref, method, *args)

class PerlJSONEncoder(json.JSONEncoder):
    def __init__(self, perl):
        super(PerlJSONEncoder, self).__init__()
        self.perl = perl

    def default(self, obj):
        raise Exception("haha")

class PerlJSONDecoder(json.JSONDecoder):
    def __init__(self, perl):
        super(PerlJSONDecoder, self).__init__(object_hook=self.decode_object)
        self.perl = perl

    def decode_object(self, obj):
        if isinstance(obj, dict) and 'plproxy' in obj:
            return PerlObject(self.perl, obj)
        else:
            return obj

class Perl(object):
    def __init__(self, port):
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

    def call(self, method, *args):
        return self._call(method=method, args=args)

    def callvirt(self, this, method, *args):
        return self._call(method=method, args=[this] + list(args), virtual=True)

    def _call(self, method, args, virtual=False):
        self._send('call', virtual, method, *args)
        return self._run()

    COMMANDS = {
        'return': 'ret',
        'useok': 'useok',
    }

    def _send(self, command, *args):
        line = self.encoder.encode([command] + list(args))
        print >>self.transport, line
        self.transport.flush()

    def _run(self):
        # TODO: has to process more than one result!
        line = self.transport.readline()

        line = self.decoder.decode(line)
        command = line[0]
        args = line[1:]

        if command in self.COMMANDS:
            # TODO: only return actually returns!
            return getattr(self, self.COMMANDS[command])(*args)

    def ret(self, *args):
        return args[0]

    def useok(self, *args):
        return
