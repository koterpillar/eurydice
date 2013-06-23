package PerlServer::Module;

use strict;
use warnings;


sub new {
	my ($class, @args) = @_;

	if (ref $class) {
		my $this = $class;
		return $this->{module}->new(@args);
	} else {
		my ($perl, $module) = @args;
		my $this = bless {}, $class;

		$this->{perl} = $perl;
		$this->{module} = $module;

		return $this;
	}
}

sub AUTOLOAD {
	our $AUTOLOAD;

	(my $method = $AUTOLOAD) =~ s/.*:://s;

	my ($this, @args) = @_;

	return $this->{module}->$method(@args);
}

sub DESTROY {
}

1;
