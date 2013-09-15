var Q = require('q');

function noop() {}

function constant(value) {
  return function () { return value; };
}

var remoteDescriptor = function (endpoint, obj) {
  return function (method) {
    if (method === 'inspect') {
      return constant('[Remote proxy]');
    }
    return {
      get: function () {
        return function () {
          var args = Array.prototype.slice.call(arguments);
          args.unshift(method);
          args.unshift(obj);
          return endpoint.do_call.apply(endpoint, args);
        };
      }
    };
  };
};

var remoteProxy = function (endpoint, obj) {
  return {
    getOwnPropertyDescriptor: remoteDescriptor(endpoint, obj),
    getPropertyDescriptor: remoteDescriptor(endpoint, obj),
    getOwnPropertyNames: constant([]),
    getPropertyNames: constant([]),
    defineProperty: noop,
    delete: noop,
    fix: noop
  };
};

module.exports = function Handler(socket) {
  var self = this;

  var instance = 'JS' + Math.random();

  var objects = [];

  var commands = {};

  // The unfinished call stack
  var stack = [];

  function freezeObject(obj) {
    var type = typeof(obj);
    if (type === 'function' || type === 'object') {
      // Check if this is a proxy for a remote object and convert it back to
      // its representation
      if ('_remote_proxy' in obj) {
        return {
          _remote_proxy: obj._remote_proxy
        };
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
    if (typeof(obj) === 'object' && obj !== null && '_remote_proxy' in obj) {
      // Proxy for either a remote object or ours
      if (obj._remote_proxy.instance === instance) {
        // Proxy for our object, get it back
        return objects[obj._remote_proxy.id];
      } else {
        // Create a proxy for the remote object
        return Proxy.create(remoteProxy(self, obj));
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
      commands[command].apply(void 0, args);
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

  function sendResult(func) {
    return function () {
      Q.fapply(func, arguments)
      .then(function (result) {
        send(['return', result]);
      }).catch(function (error) {
        send(['error', error.toString()]);
      });
    };
  }

  commands.call = sendResult(function (obj, method, args) {
    // unpack a variable number of arguments
    args = Array.prototype.slice.call(arguments);
    obj = args.shift();
    method = args.shift();

    return obj[method].apply(obj, args);
  });

  commands.global = sendResult(function (obj) {
    return global[obj];
  });

  commands.import = sendResult(function (module) {
    return require(module);
  });

  commands.delete = sendResult(function (obj) {
    for (var i = 0; i < objects.length; i++) {
      if (obj === objects[i]) {
        delete objects[i];
        return;
      }
    }
    throw "Object not found.";
  });

  commands.error = function (err) {
    var deferred = stack.pop();
    deferred.reject(err);
  };

  commands.return = function (value) {
    var deferred = stack.pop();
    deferred.resolve(value);
  };

  this.do_call = function (obj, method, args) {
    // unpack a variable number of arguments
    args = Array.prototype.slice.call(arguments);
    obj = args.shift();
    method = args.shift();

    // create a deferred to be resolved by the remote side
    var result = Q.defer();
    stack.push(result);

    send(['call', obj, method].concat(args));
    return result.promise;
  };

  socket.on('message', receive);
};
