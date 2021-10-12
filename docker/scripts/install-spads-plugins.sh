#!/bin/bash

spads_root=/opt/spads
plugins_path="${2:-$spads_root/var/plugins}"
etc_path=$spads_root/etc

plugins_arg="${1:-$SPADS_PLUGINS}"
plugins=($(echo $plugins_arg | tr ";" "\n"))

mkdir -p $plugins_path

echo "Installing spads plugins: $1"

for plugin in "${plugins[@]}"
do
  echo "> Installing spads plugin $plugin"
  curl -SLO --fail https://raw.githubusercontent.com/Yaribz/SPADS/master/plugins/officials/$plugin/$plugin.pm --output-dir $plugins_path
  curl -SLO --fail https://raw.githubusercontent.com/Yaribz/SPADS/master/plugins/officials/$plugin/${plugin}Help.dat --output-dir $plugins_path
  curl -SLO --fail https://raw.githubusercontent.com/Yaribz/SPADS/master/plugins/officials/$plugin/$plugin.conf --output-dir $etc_path
done

echo "Finished installing spads plugins"
