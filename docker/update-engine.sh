#!/bin/sh

cd /spring-engines
latest_url=`curl -s https://api.github.com/repos/beyond-all-reason/spring/releases | jq '.[0]["assets"] | .[] | select (.name | contains("linux-64-minimal-portable")) | .["browser_download_url"]' | tr -d '"'`
latest_engine=`readlink latest | sed -e 's/.*\///g'`
latest_remote_engine=`echo $latest_url | sed -e 's/.*\///g' -e 's/\.7z$//g'`

echo "Latest remote $latest_remote_engine"
echo "Latest local $latest_engine"

if [ -z $latest_engine ] || [ "$latest_engine" != "$latest_remote_engine" ]; then
  echo "> Updating to latest engine"

  mkdir /spring-engines/$latest_remote_engine
  cd /spring-engines/$latest_remote_engine
  curl -SLO $latest_url
  7z x *.7z
  rm *.7z
  unlink /spring-engines/latest
  ln -s -f /spring-engines/$latest_remote_engine /spring-engines/latest

  echo "> Engine updated successfully to $latest_remote_engine"
else
  echo "> Engine already latest"
fi
