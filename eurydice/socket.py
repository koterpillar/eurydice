"""
Socket endpoints
"""

from __future__ import absolute_import

import socket
try:
    import socketserver  # pylint:disable=import-error
except ImportError:
    import SocketServer as socketserver

from eurydice.endpoint import Endpoint
from eurydice.transport import StreamLineTransport


class SocketEndpoint(Endpoint):
    """
    An endpoint using a socket for communication
    """
    def __init__(self, stream):
        transport = StreamLineTransport(stream, self)
        super(SocketEndpoint, self).__init__(transport)


class ServerHandler(socketserver.BaseRequestHandler):
    """
    Request handler for the Server
    """
    def handle(self):
        transport = self.request.makefile('rw')
        endpoint = SocketEndpoint(transport)
        endpoint.serve_forever()


class Server(socketserver.TCPServer, object):
    """
    A server listening for commands from the remote side
    """
    def __init__(self, address):
        super(Server, self).__init__(address, ServerHandler)


class Client(SocketEndpoint):
    """
    A client sending commands to the remote side
    """
    def __init__(self, address):
        sock = socket.create_connection(address)
        stream = sock.makefile('rw')
        super(Client, self).__init__(stream)
