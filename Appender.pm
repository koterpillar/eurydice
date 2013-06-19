package Appender;

use strict;
use warnings;

sub new {
	my ($class, $append) = @_;

	my $this = bless {}, $class;

	$this->{append} = $append;

	return $this;
}

sub set_source {
	my ($this, $source) = @_;

	$this->{source} = $source;

	return $this;
}

sub append {
	my ($this, $string) = @_;

	return $string . $this->{append};
}

sub append_with_source {
	my ($this, $string) = @_;

	my $source_string = $this->{source}->string();
	return $string . $this->{append} . $source_string;
}

1;
