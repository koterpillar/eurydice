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
  this.concat = function(other) {
    var source_str;
    if(_source) {
      try {
        source_str = _source.get_string();
      } catch (e) {
        source_str = '[' + e.toString() + ']';
      }
    } else {
      source_str = '';
    }

    return _own + source_str + other;
  }

  /**
   * Raise an exception on purpose
   */
  function breakdown(how) {
    throw Error(how);
  }
}

exports.create = function (arg) { return new Concat(arg); };
