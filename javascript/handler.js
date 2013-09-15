var Q = require('q');

module.exports = function Handler(socket) {
  var self = this;

  var instance = Math.random();

  var objects = [];

  var commands = {};

  // The unfinished call stack
  var stack = [];

  function freezeObject(obj) {
    var type = typeof(obj);
    if (type === 'function' || type === 'object') {
      // TODO: Check if this is a proxy for a remote object and convert it back
      // to its representation
      if ('_remote_proxy' in obj) {
        throw "Remote proxies not implemented.";
      }
      // Actually object, store it in the array (checking if it's there
      // already first)
      var id = null;
      for (var i = 0; i < objects.length; i++) {
        if (objects[i] === obj) {
          id = i;
        }
      }
      if (id === null) {
        id = objects.push(obj) - 1;
      }
      return {
        _remote_proxy: {
          id: id,
          instance: instance
        }
      };
    } else if (typeof(obj) === 'array') {
      return obj.map(freezeObject);
    } else {
      return obj;
    }
  }

  function thawObject(obj) {
    if (typeof(obj) === 'object' && '_remote_proxy' in obj) {
      // Proxy for either a remote object or ours
      if (obj._remote_proxy.instance === instance) {
        // Proxy for our object, get it back
        return objects[obj._remote_proxy.id];
      } else {
        // TODO: Create a proxy for the remote object
        throw "Remote proxies not implemented.";
      }
    }
    return obj;
  }

  function receive(message) {
    // parse the message
    message = JSON.parse(message);
    // get the command
    var command = message.shift();
    // convert arguments
    var args = message.map(thawObject);
    // get the command
    if (command in commands) {
      Q.fapply(commands[command], args)
      .then(function (result) {
        send(['return', result]);
      })
      .catch(function (error) {
        send(['error', error.toString()]);
      });
    }
  }

  function send(message) {
    // Freeze just the arguments, not the command
    for (var i = 1; i < message.length; i++) {
      message[i] = freezeObject(message[i]);
    }
    message = JSON.stringify(message);
    socket.send(message);
  }

  commands.call = function (obj, method, args) {
    // unpack a variable number of arguments
    args = Array.prototype.slice.call(arguments);
    obj = args.shift();
    method = args.shift();

    return obj[method].apply(obj, args);
  };

  commands.global = function (obj) {
    return global[obj];
  };

  commands.import = function (module) {
    return require(module);
  };

  commands.delete = function (obj) {
    for (var i = 0; i < objects.length; i++) {
      if (obj === objects[i]) {
        delete objects[i];
        return;
      }
    }
    throw "Object not found.";
  };

  commands.error = function (err) {
    var deferred = stack.pop();
    deferred.reject(err);
  };

  commands.return = function (value) {
    var deferred = stack.pop();
    deferred.resolve(value);
  };

  socket.on('message', receive);
};
