#!/usr/bin/env perl

# actually, an even simpler solution would be to warp the pr-downloader call in a script which would acquire the lock on the SPADS unitsync lock file
# it should prevent conflicting Spring archives accesses that were hampering performance
# but it only works if sequential unitsync mode is enabled in SPADS
# Usage: perl sequentialSpadsUnitsyncProcess.pl /home/eru/spads/var /home/eru/spads/pr-downloader --filesystem-writepath /home/eru/spads/var/spring/data byar:test

use warnings;
use strict;

use Fcntl qw':DEFAULT :flock';
use File::Spec::Functions qw'catfile';

invalidUsage('at least 2 parameters are required') unless(@ARGV > 1);

my $spadsVarDir=shift(@ARGV);
invalidUsage("\"$spadsVarDir\" is not a valid directory") unless(-d $spadsVarDir);

my $spadsUnitsyncLockFile=catfile($spadsVarDir,'unitsync.lock');

printTimestamped('Acquiring SPADS unitsync exclusive lock...');
open(my $lockFh,'>',$spadsUnitsyncLockFile)
    or die "Failed to open SPADS unitsync lock file \"$spadsUnitsyncLockFile\": $!\n";
flock($lockFh,LOCK_EX)
    or die "Failed to acquire SPADS unitsync exclusive lock: $!\n";

printTimestamped('Calling synchronized process...');
system {$ARGV[0]} @ARGV;
close($lockFh);

printTimestamped('End of synchronized process.');

sub invalidUsage { die "Invalid usage: $_[0]\n  Usage:  $0 <spadsVarDir> <command>\n" }

sub printTimestamped { print getFormattedTimestamp().' - '.$_[0]."\n" }

sub getFormattedTimestamp {
  my $timestamp=$_[0]//time();
  my @localtime=localtime($timestamp);
  $localtime[4]++;
  @localtime = map {sprintf('%02d',$_)} @localtime;
  return ($localtime[5]+1900)
      .'-'.$localtime[4]
      .'-'.$localtime[3]
      .' '.$localtime[2]
      .':'.$localtime[1]
      .':'.$localtime[0]
      .' '.getTzOffset($timestamp);
}

sub getTzOffset {
  my $t=shift;
  my ($lMin,$lHour,$lYear,$lYday)=(localtime($t))[1,2,5,7];
  my ($gMin,$gHour,$gYear,$gYday)=(gmtime($t))[1,2,5,7];
  my $deltaMin=($lMin-$gMin)+($lHour-$gHour)*60+( $lYear-$gYear || $lYday - $gYday)*24*60;
  my $sign=$deltaMin>=0?'+':'-';
  $deltaMin=abs($deltaMin);
  my ($deltaHour,$deltaHourMin)=(int($deltaMin/60),$deltaMin%60);
  return $sign.sprintf('%.2u%.2u',$deltaHour,$deltaHourMin);
}
