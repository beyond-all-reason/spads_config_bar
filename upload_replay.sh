#!/bin/bash

demoName=$(basename -- "$1")

sftp -i ~/.ssh/beherith@bar-rts.com -l 1000 -P 21344 -o "StrictHostKeyChecking no" beherith@bar-rts.com <<EOF
cd /var/www/demos/unprocessed
put "$1" "$demoName.filepart"
rename "$demoName.filepart" "$demoName"
exit
EOF

# line endings fixed