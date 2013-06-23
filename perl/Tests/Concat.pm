package Tests::Concat;

use strict;
use warnings;

sub new {
	my ($class, $own) = @_;

	my $this = bless {}, $class;

	$this->{own} = $own;

	return $this;
}

sub set_source {
	my ($this, $source) = @_;

	$this->{source} = $source;

	return;
}

sub concat {
	my ($this, $other) = @_;

	my $source_str;
	if ($this->{source}) {
		my $success = eval {
			$source_str = $this->{source}->get_string();
			1;
		};
		if (!$success) {
			$source_str = "[" . $@ . "]";
		}
	} else {
		$source_str = '';
	}

	return $this->{own} . $source_str . $other;
}

sub breakdown {
	my ($this, $how) = @_;

	die($how);
}

1;
