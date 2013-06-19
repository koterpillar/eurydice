#!/usr/bin/env python
from perl import Perl

p = Perl(4444)

p.use('Appender')

cls = p.klass('Appender')

obj = cls('one') # 'new' by default

result = obj.append('two')

assert result == 'twoone'

class Source(object):
    def string(self):
        return 'three'

obj.set_source(Source())

result = obj.append_with_source('four')

assert result == 'fouronethree'
