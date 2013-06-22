from multiprocessing import Process
import random

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

def test_pypl():
    client = pypl.Client('localhost', PORT)

    cmodule = client.use('concat')
    cclass = cmodule.__getattr__('Concat')()
    obj = cclass('one')
    res = obj.concat('two')

    assert res == 'onetwo'

    client.close()
