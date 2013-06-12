#!/usr/bin/env perl

package PerlServer;

use strict;
use warnings;

use Data::Dumper;

use JSON;

use Module::Load;

sub new {
	my ($class, $transport) = @_;

	my $this = bless {}, $class;

	$this->{transport} = $transport;

	# Serializer
	$this->{json} = JSON->new;
	$this->{json}->pretty(0);
	$this->{json}->filter_json_single_key_object(proxy => sub {
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

sub send {
	my ($this, $command, @args) = @_;

	my $line = $this->{json}->encode([$command, @args]);

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

sub serialize {
	my ($this, $value) = @_;

	if (ref $value) {
		die "Cannot serialize anything useful.\n";
	}

	return JSON::to_json($value, { allow_nonref => 1 });
}

sub deserialize {
	my ($this, $value) = @_;

	return JSON::from_json($value, { allow_nonref => 1 });
}

use IO::Socket;

# Main

my $PORT = 4444;

my $server = IO::Socket::INET->new(
	Proto => 'tcp',
	LocalPort => $PORT,
	Listen => SOMAXCONN,
) or die("Cannot set up server.");

while (my $client = $server->accept()) {
	my $server = PerlServer->new($client);
	$server->run();
}
