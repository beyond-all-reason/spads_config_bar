#!/bin/bash

_term() {
  echo "Caught termination signal, passing to child process"
  kill -TERM "$child" 2>/dev/null

  pids=`find /opt/spads/var/ClusterManager -type f -name *.pid -print | xargs -I{} sh -c "cat {}; echo ''"`
  for pid in $pids
  do
    echo "> Waiting for instance with pid $pid to exit"
    tail --pid=$pid -f /dev/null
  done
  echo "Done, exiting"
}

trap _term SIGTERM
trap _term SIGINT

cp -R /spads_etc/* /opt/spads/etc
cp -R /spads_var/* /opt/spads/var

mkdir -p /opt/spads/var/log
mkdir -p /opt/spads/var/plugins
mkdir -p /opt/spads/var/spring

pidfiles=`find /opt/spads/var/ClusterManager -type f -name *.pid -print`
if [[ ! -z "$pidfiles" ]]
then
  echo "Found stale pids:"
  printf "$pidfiles\n"
  echo "Cleaning up"
  printf "$pidfiles" | xargs -I{} rm {}
fi

perl /opt/spads/spads.pl /opt/spads/etc/spads_cluster.conf \
  CMD_lobbyHost=$SPADS_LOBBY_HOST \
  CMD_lobbyLogin=$SPADS_LOBBY_LOGIN \
  CMD_lobbyPassword=$SPADS_LOBBY_PASSWORD \
  CMD_registrationEmail=$SPADS_REGISTRATION_EMAIL \
  CMD_baseGamePort=$SPADS_BASEGAME_PORT \
  CMD_baseAutoHostPort=$SPADS_BASEAUTOHOST_PORT \
  CMD_hostRegion="$SPADS_BATTLENAME_PREFIX" \
  CMD_enginesBaseDir=/spring-engines/ \
  CMD_engineDir=latest/ \
  CMD_springDataDir=$SPRING_DATADIR \
  CMD_localLanIp=$SPADS_LAN_IP \
  CMD_maxInstances=$SPADS_MAX_INSTANCES \
  CMD_targetSpares=$SPADS_TARGET_SPARES \
  CMD_clusters=$SPADS_CLUSTER_PRESETS \
  CMD_endGameCommandPath=/opt/upload_replay.sh \
  CMD_autoLoadPlugins="$SPADS_CLUSTER_PLUGINS" \
  $SPADS_ARGS &

child=$!

echo "Captured pid: $child"

wait "$child"
