var Server = require('./handler.js');

var WebSocketServer = require('ws').Server;

var wss = new WebSocketServer({port: process.argv[2]});

wss.on('connection', function (ws) {
  new Server(ws);
});
