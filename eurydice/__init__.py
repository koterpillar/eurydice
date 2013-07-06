"""
PyPl - a protocol for interacting between Python and Perl
"""

from __future__ import print_function

from functools import wraps

import importlib

import socket
try:
    import socketserver # pylint:disable=import-error
except ImportError:
    import SocketServer as socketserver

from eurydice.common import TransportException
from eurydice.transport import StreamJSONTransport


class RemoteError(Exception):
    """
    An exception occurred on the remote side
    """
    pass


def callback(func):
    """
    Within Endpoint, execute a function, send its result (or an error)
    back and continue listening for the next command
    """
    @wraps(func)
    def decorated(self, *args):
        """
        Wrapped function
        """
        try:
            val = func(self, *args)
            returned = True
        except Exception as exc: # pylint:disable=broad-except
            val = exc
            returned = False

        # pylint:disable=protected-access
        # This will be a part of the Endpoint class
        if returned:
            self._send('return', val)
        else:
            self._send('error', str(val))
        return RECEIVE_AGAIN
    return decorated


def unpack_args(func):
    """
    Unpack the argument array passed as a parameter
    """
    @wraps(func)
    def decorated(self, args):
        """
        Wrapped function
        """
        return func(self, *args)
    return decorated


RECEIVE_AGAIN = object()


class Endpoint(object):
    """
    Base class for clients and servers
    """
    def __init__(self, transport):
        self.objects = {}

        self.transport = StreamJSONTransport(transport, self)

    def _send(self, command, *args):
        """
        Send a command to the remote side
        """
        self.transport.send(command, *args)

    def _receive(self):
        """
        Receive a command from the remote side and act on it
        """
        result = RECEIVE_AGAIN
        while result is RECEIVE_AGAIN:
            (command, args) = self.transport.receive()

            command_function = 'command_%s' % command
            if hasattr(self, command_function):
                result = getattr(self, command_function)(args)
            else:
                raise TransportException("Invalid command: '%s'" % command)
        return result

    def _send_receive(self, command, *args):
        """
        Send a command to the remote side and return the result received
        """
        self._send(command, *args)
        return self._receive()

    def use(self, module):
        """
        Import a module
        """
        return self._send_receive('import', module)

    def get_global(self, obj):
        """
        Return the value of a global object
        """
        return self._send_receive('global', obj)

    def call(self, obj, method, *args):
        """
        Call a method on an object
        """
        return self._send_receive('call', obj, method, *args)

    def delete(self, obj):
        """
        Delete the reference to the object on the remote side
        """
        return self._send_receive('delete', obj)

    # Command handlers only use 'self' via the decorator
    # pylint:disable=no-self-use

    @callback
    @unpack_args
    def command_call(self, obj, method, *args):
        """
        Process the call command
        """
        return getattr(obj, method)(*args)

    @callback
    @unpack_args
    def command_global(self, obj):
        """
        Process a 'get global object value' command
        """
        return globals()[obj]

    @callback
    @unpack_args
    def command_import(self, module):
        """
        Process an 'import module' command
        """
        return importlib.import_module(module)

    @callback
    def command_delete(self, args):
        """
        Release the reference to the object
        """
        obj_id = id(args[0])
        del args[0]
        del self.objects[obj_id]

    @unpack_args
    def command_error(self, err):
        """
        Process a 'raise error' command
        """
        raise RemoteError(err)

    @unpack_args
    def command_return(self, value):
        """
        Process 'return a value' command
        """
        return value


class ServerEndpoint(Endpoint):
    """
    An endpoint passively executing commands from the remote side
    """

    def run(self):
        """
        Start executing commands from the remote side
        """
        try:
            while True:
                self._receive()
        except TransportException:
            pass


class ServerHandler(socketserver.BaseRequestHandler):
    """
    Request handler for the Server
    """
    def handle(self):
        transport = self.request.makefile('rw')
        endpoint = ServerEndpoint(transport)
        endpoint.run()


class Server(socketserver.TCPServer, object):
    """
    A server listening for commands from the remote side
    """
    def __init__(self, address):
        super(Server, self).__init__(address, ServerHandler)


class Client(Endpoint):
    """
    A client sending commands to the remote side
    """
    def __init__(self, address):
        sock = socket.create_connection(address)
        transport = sock.makefile('rw')
        super(Client, self).__init__(transport)
