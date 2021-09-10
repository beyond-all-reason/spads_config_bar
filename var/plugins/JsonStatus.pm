package JsonStatus;

use warnings;
use strict;

use IO::Socket::INET;
use JSON::PP;
use Tie::RefHash;

use SpadsPluginApi;

my $pluginVersion='0.4';
my $requiredSpadsVersion='0.12.30';

sub getVersion { return $pluginVersion; }
sub getRequiredSpadsVersion { return $requiredSpadsVersion; }

sub new {
  my $class=shift;
  my $self = {};

  $self->{serverSocket}=IO::Socket::INET->new(Listen => 5,
                                              LocalPort => getSpadsConfFull()->{hSettings}{port},
                                              Proto => 'tcp',
                                              ReuseAddr => 1);
  if(! defined $self->{serverSocket}) {
    slog("Unable to open server socket: $@",1);
    return undef;
  }

  my %clientSockets;
  tie %clientSockets, 'Tie::RefHash';
  $self->{clientSockets}=\%clientSockets;

  addSocket($self->{serverSocket},\&acceptClient);
  addTimer('socketTimeouts',1,1,\&socketTimeouts);

  bless($self,$class);
  slog("Plugin loaded (version $pluginVersion)",3);
  return $self;
}

sub acceptClient {
  my $serverSock=shift;
  my $clientSock=$serverSock->accept();
  if(defined $clientSock) {
    slog('New connection from '.$clientSock->peerhost(),5);
    getPlugin()->{clientSockets}{$clientSock}=time;
    addSocket($clientSock,\&processRequest);
  }else{
    slog('Unable to create client socket!',1);
  }
}

sub processRequest {
  my $sock=shift;
  my $self=getPlugin();
  my $readLength=$sock->sysread(my $cmd,4096);
  if(! defined $readLength) {
    slog('Error while reading request from '.$sock->peerhost().": $!",2);
  }elsif($readLength == 0) {
    slog('Connection reset by peer ('.$sock->peerhost().')',2);
  }
  if($readLength) {
    $cmd=~s/[\r\n]*$//g;
    if($cmd eq 'getBattleLobbyStatus') {
      my ($r_clientsStatus,undef,$r_globalStatus)=::getBattleLobbyStatus({accessLevel => 10});
      my $lobby=getLobbyInterface();
      foreach my $r_client (@{$r_clientsStatus}) {
        next if($r_client->{Name} =~ / \(bot\)$/);
        $r_client->{Country}=$lobby->{users}{$r_client->{Name}}{country};
      }
      print $sock encode_json({clients => $r_clientsStatus, status => $r_globalStatus});
    }elsif($cmd eq 'getGameStatus') {
      my ($r_clientsStatus,undef,$r_globalStatus)=::getGameStatus({accessLevel => 10});
      if(defined $r_clientsStatus) {
        my $r_runningBattle=getRunningBattle();
        foreach my $r_client (@{$r_clientsStatus}) {
          next if($r_client->{Name} =~ / \(bot\)$/);
          $r_client->{ID}=$r_runningBattle->{users}{$r_client->{Name}}{accountId};
          $r_client->{Rank}=$r_runningBattle->{users}{$r_client->{Name}}{status}{rank};
          $r_client->{Skill}=$r_runningBattle->{scriptTags}{'game/players/'.lc($r_client->{Name}).'/skill'};
          $r_client->{Country}=$r_runningBattle->{users}{$r_client->{Name}}{country};
        }
      }
      print $sock encode_json({clients => $r_clientsStatus, status => $r_globalStatus});
    }elsif($cmd eq 'getFullStatus') {
      my ($r_clientsStatusBattle,undef,$r_globalStatusBattle)=::getBattleLobbyStatus({accessLevel => 10});
      my ($r_clientsStatusGame,undef,$r_globalStatusGame)=::getGameStatus({accessLevel => 10});
      print $sock encode_json({battleLobby => {clients => $r_clientsStatusBattle, status => $r_globalStatusBattle},
                               game => {clients => $r_clientsStatusGame, status => $r_globalStatusGame}});
    }else{
      slog('Invalid request from '.$sock->peerhost(),2); # remove the .": $cmd" part as printing binary to terminal breaks char encoding
    }
  }
  removeSocket($sock);
  close($sock);
  delete $self->{clientSockets}{$sock};
  return;
}

sub onUnload {
  my $self=shift;
  removeTimer('socketTimeouts');
  foreach my $clientSock (keys %{$self->{clientSockets}}) {
    removeSocket($clientSock);
    close($clientSock);
    delete $self->{clientSockets}{$clientSock};
  }
  removeSocket($self->{serverSocket});
  close($self->{serverSocket});
  $self->{serverSocket}=undef;
  slog('Plugin unloaded',3);
}

sub socketTimeouts {
  my $self=getPlugin();
  foreach my $clientSock (keys %{$self->{clientSockets}}) {
    if(time-$self->{clientSockets}{$clientSock}>2) {
      slog('Timeout on client socket for '.$clientSock->peerhost(),2);
      removeSocket($clientSock);
      close($clientSock);
      delete $self->{clientSockets}{$clientSock};
    }
  }
}

1;
