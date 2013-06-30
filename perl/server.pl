#!/usr/bin/env perl

use strict;
use warnings;

use IO::Socket;

use PyPl::Server;

my $port = $ARGV[0];

my $server;

my $shutdown = sub {
	if ($server) {
		$server->shutdown(2);
	}
};

END { $shutdown->(); }
$SIG{'TERM'} = $shutdown;

$server = IO::Socket::INET->new(
	Proto => 'tcp',
	LocalPort => $port,
	Listen => SOMAXCONN,
) or die("Cannot set up server.");

while (my $client = $server->accept()) {
	my $responder = PyPl::Server->new($client);
	my $success = eval { $responder->run() };
	if (!$success) {
		print STDERR $@;
	}
	$client->shutdown(2);
}
