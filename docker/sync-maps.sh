#!/bin/sh
/usr/bin/rclone config create --non-interactive BYAR-maps drive scope=drive.readonly token="$RCLONE_DRIVE_TOKEN" team_drive=
/usr/bin/rclone config show
/usr/bin/rclone sync -v --drive-shared-with-me BYAR-maps:BYAR-maps /spring-data/maps

