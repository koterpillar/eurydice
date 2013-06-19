package PerlServer;

use strict;
use warnings;

use Data::Visitor::Callback;

use JSON;

use Module::Load;

use Scalar::Util qw(blessed weaken);


use PerlServer::PythonObject;


sub new {
	my ($class, $transport) = @_;

	my $this = bless {}, $class;

	$this->{identity} = 'server';

	$this->{transport} = $transport;

	# Serializer
	$this->{json} = JSON->new;
	$this->{json}->pretty(0);
	$this->{json}->filter_json_single_key_object(plproxy => sub {
		my ($index) = @_;

		return $this->{objects}->[$index];
	});
	$this->{json}->filter_json_single_key_object(pyproxy => sub {
		my ($index) = @_;

		return PerlServer::PythonObject->new($this, $index);
	});

	# Object registry
	$this->{objects} = [];

	# Continuation stack
	$this->{stack} = [];

	return $this;
}

my %commands = map { $_ => 1 } qw(call error return use);

sub run {
	my ($this) = @_;

	eval {
		while (1) {
			$this->process();
		}
	}
}

sub process {
	my ($this) = @_;

	my $line = $this->{transport}->getline();

	if (!defined $line) {
		die('End of stream.');
	}

	$line = $this->{json}->decode($line);
	my ($command, @args) = @{$line};

	if (exists $commands{$command}) {
		return $this->$command(@args);
	}
}

sub encode {
	my ($this, $args) = @_;

	my $visitor = Data::Visitor::Callback->new(
		object => sub {
			my (undef, $object) = @_;

			if ($object->isa('PerlServer::PythonObject')) {
				return { pyproxy => $object->{index} };
			} else {
				my $index = @{$this->{objects}};
				push @{$this->{objects}}, $object;

				return { plproxy => $index };
			}
		},
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
	my ($this, $object, $method, @args) = @_;

	my $retval;
	my $success = eval {
		$retval = $object->$method(@args);
		1;
	};

	if ($success) {
		$this->send('return', $retval);
	} else {
		$this->send('error', $@);
	}
}

sub return {
	my ($this, $value) = @_;

	return $value;
}

sub error {
	my ($this, $error) = @_;

	die($error);
}

sub use {
	my ($this, $module, @args) = @_;

	load $module;
	$this->send('useok');
}

sub callback {
	my ($this, $object, $method, @args) = @_;

	$this->send('call', $object, $method, @args);
	return $this->process();
}

1;
