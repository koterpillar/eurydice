package Eurydice::Server;

use strict;
use warnings;

use Data::Visitor::Callback;

use JSON;

use Module::Load;

use Scalar::Util qw(blessed refaddr weaken);

use Eurydice::Module;
use Eurydice::Object;

my $RECEIVE_AGAIN = bless \[], 'PerlServer::ReceiveAgain';

sub new {
	my ($class, $transport) = @_;

	my $this = bless {}, $class;

	$this->{identity} = 'server';

	$this->{transport} = $transport;

	# Serializer
	$this->{json} = JSON->new;
	$this->{json}->pretty(0);
	$this->{json}->filter_json_single_key_object(_remote_proxy => sub {
		my ($data) = @_;

		if ($data->{instance} eq $this->{identity}) {
			return $this->{objects}->{$data->{id}};
		} else {
			return Eurydice::Object->new($this, $data);
		}
	});

	# Object registry
	$this->{objects} = {};

	return $this;
}

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

	my $result = $RECEIVE_AGAIN;
	while (blessed $result && $result->isa('PerlServer::ReceiveAgain')) {
		my $line = $this->{transport}->getline();

		if (!defined $line) {
			die('End of stream.');
		}

		$line = $this->{json}->decode($line);
		my ($command, @args) = @{$line};
		#
		# Prevent memory leaks in case @args contains an object
		# which needs to be destroyed
		#
		$line = undef;

		my $command_func = "command_$command";
		if ($this->can($command_func)) {
			$result = $this->$command_func(@args);
		} else {
			die("Unknown command $command.");
		}
	}
	return $result;
}

sub encode {
	my ($this, $args) = @_;

	my $visitor = Data::Visitor::Callback->new(
		object => sub {
			my (undef, $object) = @_;

			if ($object->isa('Eurydice::Object')) {
				return { _remote_proxy => $object->{proxy_data} };
			} else {
				my $index = refaddr($object);
				if (!exists $this->{objects}->{$index}) {
					$this->{objects}->{$index} = $object;
				}

				return { _remote_proxy => {
					instance => $this->{identity},
					id => $index,
				} };
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

sub wrap_action {
	my ($this, $action) = @_;

	my $retval;
	my $success = eval {
		$retval = $action->();
		1;
	};

	if ($success) {
		$this->send('return', $retval);
	} else {
		$this->send('error', $@);
	}
}

sub command_call {
	my ($this, $object, $method, @args) = @_;

	$this->wrap_action(sub { $object->$method(@args) });
}

sub command_import {
	my ($this, $module, @args) = @_;

	$this->wrap_action(sub {
		load $module;
		return Eurydice::Module->new($this, $module);
	});
}

sub command_delete {
	my ($this, $object) = @_;

	#
	# Prevent memory leaks - $object, which is also
	# the first argument to the method, is being
	# destroyed
	#
	weaken($object);
	weaken($_[1]);
	return $this->wrap_action(sub {
		my $id = refaddr($object);
		delete $this->{objects}->{$id};
		return;
	});
}

sub command_return {
	my ($this, $value) = @_;

	return $value;
}

sub command_error {
	my ($this, $error) = @_;

	die($error);
}

sub call {
	my ($this, $object, $method, @args) = @_;

	$this->send('call', $object, $method, @args);
	return $this->process();
}

sub delete {
	my ($this, $object) = @_;

	$this->send('delete', $object);
	return $this->process();
}

1;
