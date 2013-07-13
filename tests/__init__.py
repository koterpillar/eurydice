"""
Common functionality for tests
"""

import gc
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
        pass

    @pytest.mark.xfail  # pylint:disable=no-member
    def test_delete(self):
        super(TestPythonPerl, self).test_delete()
