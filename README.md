Eurydice - the Python-Perl bridge
=============================

Introduction
------------

This is a bridge allowing to call from Python code into Perl, and vice versa.
The intention is to seamlessly mix parts written in both without worrying
about exactly which language is a part written in, and possibly replacing a
Perl library with an equivalent Python one without modifying the rest of the
code.

While similar goal can be achieved using Protocol Buffers or Thrift, they only
allow for calls returning a pre-defined type and do not provide a mechanism
for using callbacks. Java RMI allows for callbacks using proxy objects but is
neither multilingual nor friendly to dynamic languages.

The intended use is to have a "server" only used for executing "foreign" code
while the "client" contains the main execution flow.

Features
--------

* Passing arbitrary objects to either side which can then call methods on them
* Exception propagation from either side

Limitations
-----------

* The transport is TCP sockets without any authentication
* The serialization is using JSON
* Exceptions are not typed (thank you, Perl)

TODO
----

* Pluggable transports and serializations
* Embedding the "foreign" interpreter in the host process
* Performance optimizations
