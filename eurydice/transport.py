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


class RemoteJSONEncoder(json.JSONEncoder):
    """
    An encoder recognizing remote object proxies
    """
    def __init__(self, endpoint, identity):
        super(RemoteJSONEncoder, self).__init__()
        self.endpoint = endpoint
        self.identity = identity

    def default(self, obj):  # pylint:disable=method-hidden
        if isinstance(obj, RemoteObject):
            return obj.ref

        index = id(obj)
        if index not in self.endpoint.objects:
            self.endpoint.objects[index] = obj

        return {
            '_remote_proxy': {
                'id': index,
                'instance': self.identity,
            },
        }


class RemoteJSONDecoder(json.JSONDecoder):
    """
    A decoder recognizing remote object proxies
    """
    def __init__(self, endpoint, identity):
        super(RemoteJSONDecoder, self).__init__(object_hook=self.decode_object)
        self.endpoint = endpoint
        self.identity = identity

    def decode_object(self, obj):
        """
        Decode remote object proxies
        """
        if isinstance(obj, dict):
            if '_remote_proxy' in obj:
                proxy = obj['_remote_proxy']
                if proxy['instance'] == self.identity:
                    return self.endpoint.objects[proxy['id']]
                else:
                    return RemoteObject(self.endpoint, obj)
        return obj


class JSONTransport(Transport):
    """
    Transport encoding messages by JSON
    """
    def __init__(self, endpoint):
        super(JSONTransport, self).__init__(endpoint)
        self.identity = 'PY' + str(random.random())
        self.encoder = RemoteJSONEncoder(endpoint, self.identity)
        self.decoder = RemoteJSONDecoder(endpoint, self.identity)

    def decode(self, message):
        """
        Decode a message using JSON
        """
        return self.decoder.decode(message)

    def encode(self, *args):
        """
        Encode a message using JSON
        """
        return self.encoder.encode(list(args))

    def send(self, command, *args):
        chunk = self.encode(command, *args)
        try:
            self.send_chunk(chunk)
        except IOError as exc:
            raise TransportException("Transport error: '%s'" % exc)

    def receive(self):
        try:
            chunk = self.receive_chunk()
        except IOError as exc:
            raise TransportException("Transport error: '%s'" % exc)
        try:
            args = self.decode(chunk)
        except ValueError:
            raise TransportException("Invalid data received: '%s'" % chunk)
        command = args.pop(0)
        return (command, args)

    def send_chunk(self, chunk):
        """
        Send a chunk of data across
        """
        raise NotImplementedError("Please override send_chunk().")

    def receive_chunk(self):
        """
        Receive a chunk of data
        """
        raise NotImplementedError("Please override receive_chunk().")


class StreamLineTransport(JSONTransport):
    """
    Transport sending messages through a file-like object
    """
    def __init__(self, stream, endpoint):
        super(StreamLineTransport, self).__init__(endpoint)
        self.stream = stream

    def send_chunk(self, chunk):
        print(chunk, file=self.stream)
        self.stream.flush()

    def receive_chunk(self):
        return self.stream.readline()
