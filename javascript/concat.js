var Q = require('q');

/**
 * A test class concatentating strings passed in various ways
 */
function Concat(own) {
  var _own = own;
  var _source;

  /**
   * Add an object to ask for a string to concatenate from
   */
  this.set_source = function (source) {
    _source = source;
  };

  /**
   * Concatenate all the strings
   */
  this.concat = function (other) {
    var source_str;
    if(_source) {
      source_str = _source.get_string()
      .fail(function (e) {
        return '[' + e.toString() + ']';
      });
    } else {
      source_str = Q('');
    }

    return source_str.then(function (str) {
      return _own + str + other;
    });
  };

  /**
   * Raise an exception on purpose
   */
  this.breakdown = function (how) {
    throw how;
  };
}

exports.create = function (arg) { return new Concat(arg); };
