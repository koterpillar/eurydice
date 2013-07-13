"""
Endpoints working over WebSockets
"""

from __future__ import absolute_import

from websocket import create_connection, WebSocketException

from eurydice.endpoint import Endpoint
from eurydice.transport import JSONTransport, TransportException


class WebSocketTransport(JSONTransport):
    """
    Transport communicating through a websocket
    """
    def __init__(self, stream, endpoint):
        super(WebSocketTransport, self).__init__(endpoint)
        self.stream = stream
        if hasattr(self.stream, 'recv'):
            self.stream_receive = self.stream.recv
        else:
            self.stream_receive = self.stream.receive

    def send_chunk(self, chunk):
        self.stream.send(chunk)

    def receive_chunk(self):
        try:
            return self.stream_receive()
        except WebSocketException as exc:
            raise TransportException("Transport error: '%s'" % exc)


class WebSocketEndpoint(Endpoint):
    """
    An endpoint running over a websocket
    """
    def __init__(self, websocket):
        transport = WebSocketTransport(websocket, self)
        super(WebSocketEndpoint, self).__init__(transport)


class Client(WebSocketEndpoint):
    """
    An endpoint connecting to a WebSocket server
    """
    def __init__(self, url):
        websocket = create_connection(url)
        super(Client, self).__init__(websocket)


def websocket_endpoint(environ, start_response):
    # pylint:disable=unused-argument
    """
    A WSGI handler serving an endpoint
    """
    websocket = environ['wsgi.websocket']
    endpoint = WebSocketEndpoint(websocket)
    endpoint.serve_forever()
