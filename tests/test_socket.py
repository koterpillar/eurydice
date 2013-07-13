"""
Tests for socket endpoints
"""

import os
import random
import signal
import socket

import eurydice
import eurydice.socket

from tests import ServerClient, PythonInteractionTest, PerlInteractionTest


def random_address():
    """
    Generate a random port for a test server
    """
    port = random.randrange(5000, 6000)
    return ('127.0.0.1', port)


class SocketServerClient(ServerClient):
    """
    Socket client with a temporary server as a context object
    """

    def __init__(self):
        super(SocketServerClient, self).__init__()
        self.address = random_address()

    def run_server(self):
        """
        Run the actual server
        """
        raise NotImplementedError(
            "run_server() not implemented in base SocketServerClient.")

    def client(self):
        return eurydice.socket.Client(self.address)

    def server_ready(self):
        try:
            socket.create_connection(self.address)
            return True
        except socket.error:
            return False


class PythonServerClient(SocketServerClient):
    """
    Python server returning a client connected to it as a context object
    """
    def run_server(self):
        server = eurydice.socket.Server(self.address)
        server.serve_forever()


class PerlServerClient(SocketServerClient):
    """
    Perl server returning a client connected to it as a context object
    """
    def run_server(self):
        """
        Start the Perl server
        """
        port = self.address[1]
        os.execvp('perl', ['perl', '-Iperl', 'perl/server.pl', str(port)])

    def __exit__(self, type_, value, traceback):
        os.kill(self.process.pid, signal.SIGKILL)
        return False


class TestPythonPython(PythonInteractionTest):
    """
    Test interaction with a Python server
    """
    def client(self):
        return PythonServerClient()


class TestPythonPerl(PerlInteractionTest):
    """
    Test interaction with a Perl server
    """
    def client(self):
        return PerlServerClient()
