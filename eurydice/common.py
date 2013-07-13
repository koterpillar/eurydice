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
    def __init__(self, endpoint, ref):
        self.endpoint = endpoint
        self.ref = ref

    def __getattr__(self, method):
        return lambda *args: self.endpoint.call(self, method, *args)

    def __del__(self):
        try:
            self.endpoint.delete(self)
        except TransportException:
            pass
