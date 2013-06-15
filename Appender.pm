package Appender;

use strict;
use warnings;

sub new {
	my ($class, $append) = @_;

	my $this = bless {}, $class;

	$this->{append} = $append;

	return $this;
}

sub append {
	my ($this, $string) = @_;

	return $string . $this->{append};
}

1;
