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
            try:
                source_str = self.source.get_string()
            except Exception, e:
                source_str = "[" + e.message + "]"
        else:
            source_str = ""

        return self.own + source_str + other

    def breakdown(self, how):
        raise Exception(how)
