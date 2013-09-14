"""
Common functionality for tests
"""

import gc
import multiprocessing
import time
import weakref

import pytest

import eurydice

from tests.objects import Source, BadSource


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
            with pytest.raises(eurydice.RemoteError) as exc:
                robj.breakdown('five\n')
            assert str(exc.value) == 'five\n'

    def test_local_exception(self):
        """
        Test an exception raised locally
        """
        with self.client() as client:
            robj = self.concat_object(client)

            robj.set_source(BadSource('six\n'))

            assert robj.concat('seven') == 'one[six\n]seven'

    def remote_gc(self, client):
        """
        Initiate the garbage collection on the remote side
        """
        raise NotImplementedError(
            "remote_gc() not implemented in base InteractionTest.")

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

            self.remote_gc(client)

            assert ref() is None


class PythonInteractionTest(InteractionTest):
    """
    Interaction test with Python on the remote side
    """
    def concat_object(self, client):
        robjects = client.use('tests.objects')
        return robjects.Concat('one')

    def remote_gc(self, client):
        rgc = client.use('gc')
        rgc.collect()


class PerlInteractionTest(InteractionTest):
    """
    Interaction test with Perl on the remote side
    """

    def concat_object(self, client):
        rclass = client.use('Tests::Concat')
        return rclass.new('one')

    def remote_gc(self, client):
        # No GC API for Perl
        pass


class ServerClient(object):
    """
    Base class for test clients as context objects
    """
    CONNECT_RETRIES = 10
    CONNECT_DELAY = 0.1

    def __init__(self):
        self.process = multiprocessing.Process(target=self.run_server)

    def run_server(self):
        """
        Run the actual server
        """
        raise NotImplementedError(
            "run_server() not implemented in base ServerClient.")

    def client(self):
        """
        Create a client connected to the server
        """
        raise NotImplementedError(
            "client() not implemented in base ServerClient.")

    def server_ready(self):  # pylint:disable=no-self-use
        """
        Check if the server is ready
        """
        return True

    def __enter__(self):
        self.process.start()
        for retry in range(1, self.CONNECT_RETRIES):
            if self.server_ready():
                return self.client()
            time.sleep(self.CONNECT_DELAY * (2 ** retry))
        pytest.fail("Server failed to start.")  # pylint:disable=no-member

    def __exit__(self, type_, value, traceback):
        self.process.terminate()
        return False
