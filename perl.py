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

class Perl(object):
    def __init__(self, port):
        # objects registry
        self.objects = []
        self.transport = socket.create_connection(('localhost', port))

    def use(self, module):
        raise NotImplementedError("Making callvirt work first.")

    def klass(self, cls):
        return PerlClass(self, cls)

    def call(self, method, *args):
        return self._call(method=method, args=args)

    def callvirt(self, this, method, *args):
        return self._call(method=method, args=[this] + args, virtual=True)

    def _call(self, method, args, virtual=False):
        # TODO write this
        raise NotImplementedError("TODO")
