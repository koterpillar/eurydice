from multiprocessing import Process
import random

import pytest

# TODO: why does py.test not add . to sys.path?
import sys
sys.path.append('.')

import pypl

PORT = random.randrange(5000, 6000)

def run_server():
    server = pypl.Server(PORT)
    server.serve_forever()

def setup_module(module):
    module.pserver = Process(target=run_server)
    module.pserver.start()

def teardown_module(module):
    module.pserver.terminate()

def test_python_python():
    client = pypl.Client('localhost', PORT)

    cmodule = client.use('concat')
    obj = cmodule.Concat('one')

    assert obj.concat('two') == 'onetwo'

    class Source(object):
        def get_string(self):
            return 'three'

    source = Source()

    obj.set_source(source)

    assert obj.concat('four') == 'onethreefour'

    with pytest.raises(pypl.RemoteError) as e:
        obj.breakdown('five')
    assert e.value.message == 'five'

    client.close()
