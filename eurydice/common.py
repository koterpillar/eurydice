"""
Generic routines
"""


class TransportException(Exception):
    """
    An error due to incomprehensible data received from the transport side
    """
    pass


class RemoteObject(object):
    """
    A representation of a transport object
    """
    def __init__(self, transport, ref):
        self.transport = transport
        self.ref = ref

    def __getattr__(self, method):
        return lambda *args: self.transport.endpoint.call(self, method, *args)

    def __del__(self):
        try:
            self.transport.endpoint.delete(self)
        except TransportException:
            pass
