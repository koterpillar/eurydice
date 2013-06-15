#!/usr/bin/env perl

package PerlServer;

use strict;
use warnings;

use Data::Dumper;
use Data::Visitor::Callback;

use JSON;

use Module::Load;

use Scalar::Util qw(blessed weaken);

sub new {
	my ($class, $transport) = @_;

	my $this = bless {}, $class;

	$this->{transport} = $transport;

	# Serializer
	$this->{json} = JSON->new;
	$this->{json}->pretty(0);
	$this->{json}->filter_json_single_key_object(plproxy => sub {
		my ($index) = @_;
		print Dumper({
			args => \@_,
			objects => $this->{objects},
		});
		return $this->{objects}->[$index];
	});
	$this->{json}->filter_json_single_key_object(pyproxy => sub {
		# TODO: create a PerlServer::Proxy object
		die("'Their' proxies aren't implemented.");
	});

	# Object registry
	$this->{objects} = [];

	# Continuation stack
	$this->{stack} = [];

	return $this;
}

my %commands = map { $_ => 1 } qw(call return use);

sub run {
	my ($this) = @_;

	while (1) {
		my $line = $this->{transport}->getline();

		if (!defined $line) {
			last;
		}

		$line = $this->{json}->decode($line);
		print Dumper($line);
		my ($command, @args) = @{$line};

		if (exists $commands{$command}) {
			$this->$command(@args);
		}
	}
}

sub encode {
	my ($this, $args) = @_;

	my $visitor = Data::Visitor::Callback->new(
		object => sub {
			my (undef, $object) = @_;

			my $index = @{$this->{objects}};
			push @{$this->{objects}}, $object;
			#weaken $this->{objects}->[$index];

			return { plproxy => $index };
		}
	);
	$args = $visitor->visit($args);

	return $this->{json}->encode($args);
}

sub send {
	my ($this, $command, @args) = @_;

	my $line = $this->encode([$command, @args]);

	$this->{transport}->print("$line\n");
}

sub call {
	my ($this, $virtual, $method, @args) = @_;

	my $retval;
	if ($virtual) {
		my $ref = shift @args;
		$retval = $ref->$method(@args);
	} else {
		$retval = &{\&{$method}}(@args);
	}

	$this->send('return', $retval);
}

sub return {
	my ($this, $value) = @_;
	# There's a code reference on the stack
	# Pop it off there and execute with the return value
}

sub use {
	my ($this, $module, @args) = @_;

	load $module;
	$this->send('useok');
}

# Main

use IO::Socket;

my $PORT = 4444;

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
	LocalPort => $PORT,
	Listen => SOMAXCONN,
) or die("Cannot set up server.");

while (my $client = $server->accept()) {
	my $responder = PerlServer->new($client);
	my $success = eval { $responder->run() };
	if (!$success) {
		print STDERR $@;
	}
	$client->shutdown(2);
}
