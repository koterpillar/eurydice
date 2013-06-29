"""
Tests for the pypl module
"""

import gc
import multiprocessing
import os
import random
import signal
import time
import weakref

import pytest

import pypl

from tests.objects import Source, BadSource


def random_address():
    """
    Generate a random port for a test server
    """
    port = random.randrange(5000, 6000)
    return ('localhost', port)


class InteractionTest(object):
    """
    Test all the client-server interactions
    """
    def client(self):
        """
        Prepare a client to run the tests with
        """
        raise NotImplementedError(
                "client() not implemented in base InteractionTest.")

    def concat_object(self, client):
        """
        Create a test remote object
        """
        raise NotImplementedError(
                "concat_object() not implemented in base InteractionTest.")

    def test_call(self):
        """
        Test basic Python-Python interaction
        """
        with self.client() as client:
            robj = self.concat_object(client)

            assert robj.concat('two') == 'onetwo'

    def test_callback(self):
        """
        Test a callback
        """
        with self.client() as client:
            robj = self.concat_object(client)

            robj.set_source(Source('three'))

            assert robj.concat('four') == 'onethreefour'

    def test_remote_exception(self):
        """
        Test an exception raised on the remote side
        """
        with self.client() as client:
            robj = self.concat_object(client)

            # pylint:disable=no-member
            with pytest.raises(pypl.RemoteError) as exc:
                robj.breakdown('five')
            assert exc.value.message == 'five'

    def test_local_exception(self):
        """
        Test an exception raised locally
        """
        with self.client() as client:
            robj = self.concat_object(client)

            robj.set_source(BadSource('six'))

            assert robj.concat('seven') == 'one[six]seven'

    def test_delete(self):
        """
        Test deleting objects
        """
        with self.client() as client:
            robj = self.concat_object(client)

            ref = Source('weak')
            robj.set_source(ref)
            ref = weakref.ref(ref)

            del robj
            gc.collect()

            rgc = client.use('gc')
            rgc.collect()

            assert ref() == None

            del rgc


class ServerClient(object):
    """
    Base class for test clients as context objects
    """
    def __init__(self):
        self.address = random_address()
        self.process = multiprocessing.Process(target=self.run_server)

    def run_server(self):
        """
        Run the actual server
        """
        raise NotImplementedError(
                "run_server() not implemented in base ServerClient.")

    def __enter__(self):
        self.process.start()
        time.sleep(0.3)
        return pypl.Client(self.address)

    def __exit__(self, type_, value, traceback):
        self.process.terminate()
        return False


class PythonServerClient(ServerClient):
    """
    Python server returning a client connected to it as a context object
    """
    def run_server(self):
        server = pypl.Server(self.address)
        server.serve_forever()


class TestPythonPython(InteractionTest):
    """
    Test interaction with a Python server
    """
    def client(self):
        return PythonServerClient()

    def concat_object(self, client):
        robjects = client.use('tests.objects')
        return robjects.Concat('one')


class PerlServerClient(ServerClient):
    """
    Perl server returning a client connected to it as a context object
    """
    def run_server(self):
        """
        Start the Perl server
        """
        port = self.address[1]
        os.execvp('perl', ['perl', '-Iperl', 'perl/server.pl', str(port)])

    def __enter__(self):
        client = super(PerlServerClient, self).__enter__()
        time.sleep(0.4)
        return client

    def __exit__(self, type_, value, traceback):
        os.kill(self.process.pid, signal.SIGKILL)


class TestPythonPerl(InteractionTest):
    """
    Test interaction with a Perl server
    """
    def client(self):
        return PerlServerClient()

    def concat_object(self, client):
        rclass = client.use('Tests::Concat')
        return rclass.new('one')
