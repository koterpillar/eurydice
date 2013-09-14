"""
Tests for WebSocket endpoints
"""

from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler

import eurydice
import eurydice.websocket

from tests import JavaScriptInteractionTest, PythonInteractionTest
from tests.test_socket import ProcessServerClient, SocketServerClient


class WebSocketServerClient(SocketServerClient):
    """
    WebSocket client with a temporary server
    """
    def client(self):
        url = "ws://%s:%s" % self.address
        return eurydice.websocket.Client(url)


class PythonWebSocketClient(WebSocketServerClient):
    """
    WebSocket client with a Python server
    """
    def run_server(self):
        server = pywsgi.WSGIServer(
            self.address,
            eurydice.websocket.websocket_endpoint,
            handler_class=WebSocketHandler)
        server.serve_forever()


class JavaScriptWebSocketClient(WebSocketServerClient, ProcessServerClient):
    """
    WebSocket client with a JavaScript server
    """

    arguments = ['nodejs', 'javascript/server.js']


class TestPythonPython(PythonInteractionTest):
    """
    Test interaction with a Python server
    """
    def client(self):
        return PythonWebSocketClient()


class TestPythonJavaScript(JavaScriptInteractionTest):
    """
    Test interaction with a JavaScript server
    """
    def client(self):
        return JavaScriptWebSocketClient()
