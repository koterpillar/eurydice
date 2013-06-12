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
        # TODO write this
        pass

    def use(self, module):
        pass

    def klass(self, cls):
        return PerlClass(self, cls)

    def call(self, method, *args):
        pass

    def callvirt(self, this, method, *args):
        pass
