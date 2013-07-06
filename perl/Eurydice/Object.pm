package Eurydice::Object;

use strict;
use warnings;

sub new {
	my ($class, $perl, $data) = @_;

	my $this = bless {}, $class;

	$this->{perl} = $perl;
	$this->{proxy_data} = $data;

	return $this;
}

sub AUTOLOAD {
	our $AUTOLOAD;

	(my $method = $AUTOLOAD) =~ s/.*:://s;

	my ($this, @args) = @_;

	return $this->{perl}->call($this, $method, @args);
}

sub DESTROY {
	my ($this) = @_;

	$this->{perl}->delete($this);
}

1;
