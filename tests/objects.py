"""
Simple objects for the tests
"""

class Concat(object):
    """
    A test class concatenating strings passed in various ways
    """

    def __init__(self, own):
        self.own = own
        self.source = None

    def set_source(self, source):
        """
        Add an object to ask for a string to concatenate from
        """
        self.source = source

    def concat(self, other):
        """
        Concatenate all the strings
        """
        if self.source:
            try:
                source_str = self.source.get_string()
            except Exception as exc: # pylint:disable=broad-except
                source_str = '[' + exc.message + ']'
        else:
            source_str = ''

        return self.own + source_str + other

    def breakdown(self, how): # pylint:disable=no-self-use
        """
        Raise an exception on purpose
        """
        raise Exception(how)


class Source(object):
    """
    An object providing a string to concatenate
    """
    def __init__(self, string):
        self.string = string

    def get_string(self):
        """
        Return a string
        """
        return self.string


class BadSource(object):
    """
    An object raising an error when asked for a string
    """
    def __init__(self, string):
        self.string = string

    def get_string(self):
        """
        Raise an error instead of returning a string
        """
        raise Exception(self.string)
