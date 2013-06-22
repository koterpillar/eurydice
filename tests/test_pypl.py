from multiprocessing import Process

# TODO: why does py.test not add . to sys.path?
import sys
sys.path.append('.')

import pypl

class Concat(object):
    """
    A test class concatenating strings passed in various ways
    """

    def __init__(own):
        self.own = own
        self.source = None

    def set_source(source):
        self.source = source

    def concat(other):
        if self.source:
            source_str = source.get_string()
        else:
            source_str = ""

        return self.own + source_str + other

PORT = 5555

def run_server():
    server = pypl.Server()
    server.listen(PORT)

def setup_module(module):
    module.pserver = Process(target=run_server)
    module.pserver.start()

def teardown_module(module):
    module.pserver.terminate()

def test_pypl():
    client = pypl.Client('localhost', PORT)

    cclass = client.klass('Concat')
    obj = cclass('one')
    res = obj.concat('two')

    assert res == 'onetwo'
