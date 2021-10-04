#!/bin/bash

set -x

cp -R /spads_etc/* /opt/spads/etc
cp -R /spads_var/* /opt/spads/var

mkdir -p /opt/spads/var/log
mkdir -p /opt/spads/var/plugins
mkdir -p /opt/spads/var/spring

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
  $SPADS_ARGS
