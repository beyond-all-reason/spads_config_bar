package KickBanDuration;

use strict;

use SpadsPluginApi;
use constant {
  MAXBANDURATION => 60, #max duration of a kickban in minutes
};

my $pluginVersion='0.1';
my $requiredSpadsVersion='0.11.5'; # SPADS itself refuses to load this plugin below this version
my $maxTestedSpadsVersion='0.13.50'; # highest SPADS version this plugin has actually been verified against

# Set by new(), read by hKickBanDuration() (and onUnload()) as the safe thing to
# fall back to whenever this logic fails
my $previousKickBanHandler;

# Access control for kickban is intentionally left untouched, defer to existing kickban handler and permissions

sub getVersion { return $pluginVersion; }
sub getRequiredSpadsVersion { return $requiredSpadsVersion; }

# On success returns: (1,$playerFilter,$durationMinutes)
#if not specified then durationMinutes is -1
# On Failure returns: (0,$errorMessage)
sub parseKickBanDurationArgs {
  my $p_params=shift;
  my $nbParams=scalar(@{$p_params});
  return (0,'missing player name') if($nbParams < 1); #if no player name was specified, return error
  return (0,'too many parameters') if($nbParams > 2); #if more than 2 parameters were specified, return error
  return (1,$p_params->[0],-1) if($nbParams == 1);  #if only one parameter was specified, return success with durationMinutes=-1 to indicate that no duration was specified

  #parse duration parameter, assumes param is in minutes
  my $duration=$p_params->[1];
  return (0,"invalid duration \"$duration\", must be a positive integer number of minutes")

      #check that duration is a non-negative int (\d+ already rules out negatives) and at most maxbanduration
      unless($duration =~ /^\d+$/ && $duration <= MAXBANDURATION);
  return (1,$p_params->[0],$duration+0);
}

#when this plugin is loaded, replace the original kickban handler with our own
sub new {
  my $class=shift;
  $previousKickBanHandler=$::spadsCmdHandlers{kickban};
  my $self={};
  bless($self,$class);
  addSpadsCommandHandler({kickban => \&hKickBanDuration},1);
  slog("Plugin loaded (version $pluginVersion)",3);
  return $self;
}

#if this plugin is unloaded, restore the original kickban handler
sub onUnload {
  addSpadsCommandHandler({kickban => $previousKickBanHandler},1);
  slog("Plugin unloaded",3);
}

#command takes params $source,$user,\@cmd,$checkOnly:
# source is where the command was sent from (battle/chan/pv/game);
# user is the name of the player who sent the command;
# \@cmd is the list of parameters after the command name;
# $checkOnly is true if we only want to check if the command is valid, without actually executing it

sub hKickBanDuration {
  my ($source,$user,$p_params,$checkOnly)=@_;

  #compare versions to ensure that we are running on a version of SPADS that is known to be compatible with this plugin. If not, fall back to the original handler.
  if(::compareVersions($spadsVersion,$maxTestedSpadsVersion) > 0) {
    slog("KickBanDuration: SPADS $spadsVersion is newer than the last version this plugin was tested against ($maxTestedSpadsVersion); falling back to the original kickban handler",2);
    return &$previousKickBanHandler($source,$user,$p_params,$checkOnly); #call original function
  }

  #catch any error raised inside doKickBanDuration and fall back to the original handler instead of propagating it.
  #note: this only covers unexpected runtime errors - a syntax/parsing error still returns 0 directly, without falling back.
  #this is intended to catch cases where the original kickban handler changes in a future version of SPADS and is no longer compatible with this plugin
  my $result=eval { doKickBanDuration($source,$user,$p_params,$checkOnly) };
  if($@) {
    slog("KickBanDuration: unexpected error ($@), falling back to the original kickban handler",1);
    return &$previousKickBanHandler($source,$user,$p_params,$checkOnly);
  }
  return $result;
}

#perform actual kickban with duration, returns the result of the original kickban handler after changing config duration
sub doKickBanDuration {
  my ($source,$user,$p_params,$checkOnly)=@_;

  #parse args
  my ($ok,$playerOrError,$durationMinutes)=parseKickBanDurationArgs($p_params);
  if(! $ok) { #if there was an error parsing params, surface error code then return 0
    ::invalidSyntax($user,'kickban',$playerOrError);
    return 0;
  }

  #if duration minutes was specified, set the kickBanDuration config value to that duration in
  #seconds for the duration of this call only, then delegate to the real handler
  if($durationMinutes != -1) {
    my $p_conf=getSpadsConf();
    local $p_conf->{kickBanDuration}=$durationMinutes*60;

    # If the player already has a ban in place which could have been added by a
    # previous kickban, replace it below so the new duration actually takes
    # effect instead of being shadowed by the older entry (see getUserBan's
    # banType tie-break, which keeps the first matching ban of a given type,
    # not the newest).

    #resolve the target player by checking that kickban wouldn't error and would resolve to a player's name
    my $resolveRes = ::hKickBan($source,$user,[$playerOrError],1);
    return $resolveRes unless(ref($resolveRes) eq 'ARRAY'); #if it doesn't resolve to a name, return the error/failure result unchanged
    #this early return also prevents unbanning a player over an invalid/ambiguous/not-found kickban call
    my $bannedUser = $resolveRes->[1];

    #only actually clear anything when this is a real execution, not a checkOnly
    #syntax/vote pre-check - a pre-check must never have side effects
    if(! $checkOnly) {
      #before applying a new ban, remove existing battle type bans for the player if they exist, this is done to override existing bans with the new duration,
      # Only clear an existing kickban entry if its remaining time is already under the max allowed time for a kickban, otherwise leave it alone.
      #this is done as an extra check to avoid clearing bans that were set by other means (e.g. a manual ban) that may have a longer duration than the max allowed for a kickban.
      my $maxClearableRemainingSeconds = MAXBANDURATION*60;
      my $p_existingBans = getSpadsConfFull()->getDynamicBans(); #get existing ban entries
      for my $p_banEntry (@{$p_existingBans}) {
        my ($p_existingUser,$p_existingBanData) = @{$p_banEntry};
        next unless(defined $p_existingBanData->{banType} && $p_existingBanData->{banType} == 1);

        # search for the player by name or accountId, since the ban entry may have been created by a different name than the one used to issue the kickban command
        my $isSamePlayer = (defined $p_existingUser->{name} && $p_existingUser->{name} eq $bannedUser)
                        || (defined $p_existingUser->{accountId} && $p_existingUser->{accountId} =~ /\Q($bannedUser)\E$/);
        next unless($isSamePlayer);

        #check ban data and make sure it exists and is defined, and that the remaining time is less than the max allowed for a kickban, otherwise leave it alone
        next unless(exists $p_existingBanData->{endDate} && defined $p_existingBanData->{endDate} && $p_existingBanData->{endDate} ne '');
        next if($p_existingBanData->{endDate} - time > $maxClearableRemainingSeconds);

        #if all checks pass, remove the existing ban entry to allow the new kickban to be applied with the new duration
        getSpadsConfFull()->removeBanByHash(getSpadsConfFull()->getBanHash($p_banEntry));
      }
    }

    # Now perform the real (re-)ban with the overridden duration already in scope.
    return ::hKickBan($source,$user,[$playerOrError],$checkOnly);

  }

  #if duration minutes was not specified, just call the original kickban handler unchanged
  return ::hKickBan($source,$user,[$playerOrError],$checkOnly);
}

1;
