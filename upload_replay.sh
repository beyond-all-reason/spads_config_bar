#!/bin/bash

demoName=$(basename -- "$1")

sshpass -p "$SFTP_PASSWORD" sftp -l 1000 -P 21344 -o "StrictHostKeyChecking no" $SFTP_LOGIN@bar-rts.com <<EOF
cd /var/www/demos/unprocessed
put "$1" "$demoName.filepart"
rename "$demoName.filepart" "$demoName"
exit
EOF
