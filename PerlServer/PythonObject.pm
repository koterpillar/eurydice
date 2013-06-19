package PerlServer::PythonObject;

use strict;
use warnings;

sub new {
	my ($class, $perl, $index) = @_;

	my $this = bless {}, $class;

	$this->{perl} = $perl;
	$this->{index} = $index;

	return $this;
}

sub AUTOLOAD {
	our $AUTOLOAD;

	(my $method = $AUTOLOAD) =~ s/.*:://s;

	my ($this, @args) = @_;

	return $this->{perl}->callback($this, $method, @args);
}

sub DESTROY {
	# TODO: send a 'weaken' request
}

1;
