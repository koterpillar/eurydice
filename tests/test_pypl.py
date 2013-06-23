"""
Tests for the pypl module
"""

from multiprocessing import Process
import os
import random
import signal
import time

import pytest

import pypl

from tests.objects import Source, BadSource


def random_address():
    """
    Generate a random port for a test server
    """
    port = random.randrange(5000, 6000)
    return ('localhost', port)


def test_python_python():
    """
    Test interaction between Python client and server
    """
    address = random_address()

    server = pypl.Server(address)
    pserver = Process(target=server.serve_forever)
    pserver.start()

    try:
        client = pypl.Client(address)

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

    finally:
        pserver.terminate()


def test_python_perl():
    """
    Test interaction between Python client and server
    """
    (_, port) = address = random_address()

    def start_perl_server():
        """
        Start the Perl server
        """
        os.execvp('perl', ['perl', '-Iperl', 'perl/server.pl', str(port)])

    pserver = Process(target=start_perl_server)
    pserver.start()
    time.sleep(0.3)

    try:
        client = pypl.Client(address)

        rclass = client.use('Tests::Concat')
        robj = rclass.new('one')

        assert robj.concat('two') == 'onetwo'

        robj.set_source(Source('three'))

        assert robj.concat('four') == 'onethreefour'

        with pytest.raises(pypl.RemoteError) as exc: # pylint:disable=no-member
            robj.breakdown('five\n')
        assert exc.value.message == 'five\n'

        robj.set_source(BadSource('six\n'))

        assert robj.concat('seven') == 'one[six\n]seven'

    finally:
        os.kill(pserver.pid, signal.SIGKILL)
