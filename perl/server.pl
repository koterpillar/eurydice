#!/usr/bin/env perl

use strict;
use warnings;

use IO::Socket;

use PerlServer;

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

print "Listening on $port.\n";
while (my $client = $server->accept()) {
	my $responder = PerlServer->new($client);
	my $success = eval { $responder->run() };
	if (!$success) {
		print STDERR $@;
	}
	$client->shutdown(2);
}
