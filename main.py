#!/usr/bin/env python
from perl import Perl

p = Perl(4444)

p.use('Foo')

cls = p.klass('Appender')

obj = cls('plus') # 'new' by default

result = obj.append('minus')

assert result == 'minusplus'
