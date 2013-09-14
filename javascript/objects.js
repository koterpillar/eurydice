/**
 * A test class concatentating strings passed in various ways
 */
function Concat(own) {
  this.own = own;
  this.source = none;

  /**
   * Add an object to ask for a string to concatenate from
   */
  function set_source(source) {
    this.source = source;
  }

  /**
   * Concatenate all the strings
   */
  function concat(other) {
    var source_str;
    if(this.source) {
      try {
        source_str = this.source.get_string();
      } catch (e) {
        source_str = '[' + e.toString() + ']';
      }
    } else {
      source_str = '';
    }

    return this.own + source_str + other;
  }

  /**
   * Raise an exception on purpose
   */
  function breakdown(how) {
    throw Error(how);
  }
}

exports.create = function (arg) { return new Concat(arg); };
