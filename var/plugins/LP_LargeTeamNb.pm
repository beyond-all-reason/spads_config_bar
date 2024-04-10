# LP_LargeTeamNb Plugin
# This plugin reuses some unused/reserved bits in MYBATTLESTATUS command from spring protocol
#
# Original spring protocol can communicate about up to 16 players and teams over the command MYBATTLESTATUS (https://springrts.com/dl/LobbyProtocol/ProtocolDescription.html#MYBATTLESTATUS:client)
# Since spring/recoil supports up to 256 players, this plugin uses those unused/reserved bits b18..b21 and b28..b31 to communicate teamIDS and allyTeamIDs between autohost and clients.
#
# So team nr. will be b2..b5(original) + b18..b21(extension)
# and ally team no. gets b6..b9 + b28..b31
# (This info was added by Fireball)

# Author of code: Yaribz

package LP_LargeTeamNb;

use strict;

use SpadsPluginApi;

my $pluginVersion='0.1';
my $requiredSpadsVersion='0.12.57';
my $requiredSliVersion='0.39';

sub getVersion { return $pluginVersion; }
sub getRequiredSpadsVersion { return $requiredSpadsVersion; }

my @SLI_FUNCTIONS_REPLACED = (qw'marshallBattleStatus unmarshallBattleStatus');
my @SLI_HOOKS_REMOVED = (qw'UPDATEBOT FORCEALLYNO FORCETEAMNO');

sub new {
  my $class=shift;
  
  my $lobbyInterface=getLobbyInterface();
  if(::compareVersions($lobbyInterface->getVersion(),$requiredSliVersion) < 0) {
    slog("SpringLobbyInterface v$requiredSliVersion or greater is required",1);
    return undef;
  }

  my %sliBackups;
  map {$sliBackups{$_} = delete ${SpringLobbyInterface::}{$_}} @SLI_FUNCTIONS_REPLACED;
  map {$sliBackups{$_} = delete $SpringLobbyInterface::commandHooks{$_}} @SLI_HOOKS_REMOVED;

  ${SpringLobbyInterface::}{marshallBattleStatus} = sub {
    my ($self,$p_battleStatus)=@_;
    my %bs=%{$p_battleStatus};
    my $teamLow = $bs{team} % 16;
    my $teamHigh=int($bs{team}/16);
    my $idLow = $bs{id} % 16;
    my $idHigh=int($bs{id}/16);
    return oct('0b'
               .sprintf('%04b',$teamHigh)
               .sprintf('%04b',$bs{side})
               .sprintf('%02b',$bs{sync})
               .sprintf('%04b',$idHigh)
               .sprintf('%07b',$bs{bonus})
               .$bs{mode}
               .sprintf('%04b',$teamLow)
               .sprintf('%04b',$idLow)
               .$bs{ready}
               .'0');
  };
  
  ${SpringLobbyInterface::}{unmarshallBattleStatus} = sub {
    my ($self,$battleStatus)=@_;
    $battleStatus+=2147483648 if($battleStatus < 0);
    my $bs=sprintf('%032b',$battleStatus);
    return { side => oct('0b'.substr($bs,4,4)),
             sync => oct('0b'.substr($bs,8,2)),
             bonus => oct('0b'.substr($bs,14,7)),
             mode => substr($bs,21,1)+0,
             team => oct('0b'.substr($bs,0,4).substr($bs,22,4)),
             id => oct('0b'.substr($bs,10,4).substr($bs,26,4)),
             ready => substr($bs,30,1)+0 };
  };
  
  my $self = { sliBackups => \%sliBackups };
  bless($self,$class);
  
  slog("Plugin loaded (version $pluginVersion)",3);
  return $self;
}

sub onUnload {
  my ($self,$reason)=@_;

  map {delete ${SpringLobbyInterface::}{$_}; ${SpringLobbyInterface::}{$_}=$self->{sliBackups}{$_}} @SLI_FUNCTIONS_REPLACED;
  map {$SpringLobbyInterface::commandHooks{$_}=$self->{sliBackups}{$_}} @SLI_HOOKS_REMOVED;
  
  slog("Plugin unloaded [$reason]",3);
}

1;
