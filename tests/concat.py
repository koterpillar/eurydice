class Concat(object):
    """
    A test class concatenating strings passed in various ways
    """

    def __init__(self, own):
        self.own = own
        self.source = None

    def set_source(self, source):
        self.source = source

    def concat(self, other):
        if self.source:
            source_str = source.get_string()
        else:
            source_str = ""

        return self.own + source_str + other
