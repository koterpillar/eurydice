"""
Endpoints working over WebSockets
"""

from websocket import create_connection
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler

from eurydice.endpoint import Endpoint
from eurydice.transport import WebSocketTransport


class WebSocketEndpoint(Endpoint):
    """
    An endpoint running over a websocket
    """
    def __init__(self, websocket):
        transport = WebSocketTransport(websocket)
        super(WebSocketEndpoint, self).__init__(transport)


class WebSocketClient(WebSocketEndpoint):
    """
    An endpoint connecting to a WebSocket server
    """
    def __init__(self, url):
        websocket = create_connection(url)
        super(WebSocketClient, self).__init__(websocket)


def websocket_endpoint(environ, start_response):
    """
    A WSGI handler serving an endpoint
    """
    websocket = environ['wsgi.websocket']
    endpoint = WebSocketEndpoint(websocket)
    endpoint.serve_forever()
