package PyPl::Server;

use strict;
use warnings;

use Data::Visitor::Callback;

use JSON;

use Module::Load;

use Scalar::Util qw(blessed weaken);

use PyPl::Module;
use PyPl::Object;


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
			return $this->{objects}->[$data->{id}];
		} else {
			return PyPl::Object->new($this, $data);
		}
	});

	# Object registry
	$this->{objects} = [];

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

	my $line = $this->{transport}->getline();

	if (!defined $line) {
		die('End of stream.');
	}

	$line = $this->{json}->decode($line);
	my ($command, @args) = @{$line};

	my $command_func = "command_$command";
	if ($this->can($command_func)) {
		return $this->$command_func(@args);
	} else {
		die("Unknown command $command.");
	}
}

sub encode {
	my ($this, $args) = @_;

	my $visitor = Data::Visitor::Callback->new(
		object => sub {
			my (undef, $object) = @_;

			if ($object->isa('PyPl::Object')) {
				return { _remote_proxy => $object->{proxy_data} };
			} else {
				my $index = @{$this->{objects}};
				push @{$this->{objects}}, $object;

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
		return PyPl::Module->new($this, $module);
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

sub callback {
	my ($this, $object, $method, @args) = @_;

	$this->send('call', $object, $method, @args);
	return $this->process();
}

1;
