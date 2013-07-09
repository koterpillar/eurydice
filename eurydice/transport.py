"""
Transport
"""

from __future__ import print_function

import json

import random

from eurydice.common import RemoteObject, TransportException


class Transport(object):
    """
    Base class for transports
    """

    def __init__(self, endpoint):
        """
        Initialize a transport
        """
        self.endpoint = endpoint
        self.objects = endpoint.objects

    def send(self, command, *args):
        """
        Send a command to the remote side
        """
        raise NotImplementedError("Please override send().")

    def receive(self):
        """
        Receive a command from the remote side
        """
        raise NotImplementedError("Please override receive().")


class StreamLineTransport(Transport):
    # pylint:disable=abstract-class-little-used
    """
    Transport sending messages through a file-like object
    """
    def __init__(self, transport, objects):
        super(StreamLineTransport, self).__init__(objects)
        self.transport = transport

    def decode(self, line):
        """
        Decode a line of data received
        """
        raise NotImplementedError("Please override decode().")

    def encode(self, *args):
        """
        Encode a command to a chunk
        """
        raise NotImplementedError("Please override decode().")

    def send(self, command, *args):
        line = self.encode(command, *args)
        try:
            print(line, file=self.transport)
            self.transport.flush()
        except IOError as exc:
            raise TransportException("Transport error: '%s'" % exc)

    def receive(self):
        try:
            line = self.transport.readline()
        except IOError as exc:
            raise TransportException("Transport error: '%s'" % exc)
        try:
            args = self.decode(line)
        except ValueError:
            raise TransportException("Invalid data received: '%s'" % line)
        command = args.pop(0)
        return (command, args)


class RemoteJSONEncoder(json.JSONEncoder):
    """
    An encoder recognizing remote object proxies
    """
    def __init__(self, transport):
        super(RemoteJSONEncoder, self).__init__()
        self.transport = transport

    def default(self, obj):  # pylint:disable=method-hidden
        if isinstance(obj, RemoteObject):
            return obj.ref

        index = id(obj)
        if index not in self.transport.objects:
            self.transport.objects[index] = obj

        return {
            '_remote_proxy': {
                'id': index,
                'instance': self.transport.identity,
            },
        }


class RemoteJSONDecoder(json.JSONDecoder):
    """
    A decoder recognizing remote object proxies
    """
    def __init__(self, transport):
        super(RemoteJSONDecoder, self).__init__(object_hook=self.decode_object)
        self.transport = transport

    def decode_object(self, obj):
        """
        Decode remote object proxies
        """
        if isinstance(obj, dict):
            if '_remote_proxy' in obj:
                proxy = obj['_remote_proxy']
                if proxy['instance'] == self.transport.identity:
                    return self.transport.objects[proxy['id']]
                else:
                    return RemoteObject(self.transport, obj)
        return obj


class StreamJSONTransport(StreamLineTransport):
    """
    Transport for encoding messages as JSON
    """
    def __init__(self, transport, objects):
        super(StreamJSONTransport, self).__init__(transport, objects)
        self.identity = str(random.random())
        self.encoder = RemoteJSONEncoder(self)
        self.decoder = RemoteJSONDecoder(self)

    def decode(self, line):
        return self.decoder.decode(line)

    def encode(self, *args):
        return self.encoder.encode(list(args))
