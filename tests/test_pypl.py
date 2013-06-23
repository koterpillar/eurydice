"""
Tests for the pypl module
"""

from multiprocessing import Process
import random

import pytest

import pypl

from tests.objects import Source, BadSource

PORT = random.randrange(5000, 6000)
ADDRESS = ('localhost', PORT)


def test_python_python():
    """
    Test interaction between Python client and server
    """
    server = pypl.Server(ADDRESS)
    pserver = Process(target=server.serve_forever)
    pserver.start()

    client = pypl.Client(ADDRESS)

    robjects = client.use('tests.objects')
    robj = robjects.Concat('one')

    assert robj.concat('two') == 'onetwo'

    robj.set_source(Source('three'))

    assert robj.concat('four') == 'onethreefour'

    with pytest.raises(pypl.RemoteError) as exc: # pylint:disable=no-member
        robj.breakdown('five')
    assert exc.value.message == 'five'

    robj.set_source(BadSource('six'))

    assert robj.concat('seven') == 'one[six]seven'

    pserver.terminate()
