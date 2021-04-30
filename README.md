This directory contains the configuration information and map-game updater scripts to successfully host a SPADS instance for BAR

Remember to look through the paths to set them correcly for your host, as well as the logins and passwords!

Spads available here: http://planetspads.free.fr/


## Service Script

The spads.service file is for starting single instances of spads hosts.

Use `systemctl start spads.service` to start the service
Use `systemctl enable spads.service` to start the service on startup

The spads@.service file is for starting multiple instances of spads hosts.

Use `systemctl start spads@<hostid>.service` to start the service
Use `systemctl enable spads@<hostid>.service` to start the service on startup
Replacing the <hostid> with the relevant id number

Update the paths in the file/s to suit your system.

## Keeping game and maps up to date:

# Maps
Updated with rclone from google drive folder:

# rclone installation

- sudo apt-get install rclone
- rclone config
- select new
- name: BYAR-maps
- storage type: 13 (drive)
- no client id
- no client secret
- access type: 2 (drive.readonly)
- root folder id: blank
- service account credentials: blank
- service accoutn file: blank
- Edit advanced config: n
- Use auto config: n
- Configure this as team drive: n
 
Then to update maps:

rclone sync --drive-shared-with-me BYAR-maps:BYAR-maps /home/xxxx/spads/var/spring/data/maps/

copy the relevant .timer and .service files into, 

/etc/systemd/system 

and make sure they contain the correct paths to executables and data storage, and the User names are correct!

https://opensource.com/article/20/7/systemd-timers

systemctl daemon-reload

systemctl status rclone-maps.service

systemctl start rclone-maps.service 

systemctl enable --now rclone-maps.timer

Use --now to not wait till next reboot

# Game

install pr-downloader by copying pr-downloader from an engine build into /usr/local/bin

copy the relevant .timer and .service files into:

/etc/systemd/system/

Make sure the username and executable path and data storage path is correct

https://opensource.com/article/20/7/systemd-timers

systemctl daemon-reload

systemctl status pr-downloader.service

systemctl start pr-downloader.service 

systemctl enable --now pr-downloader.timer

## SPADS:

Make sure instancedir and instancedir/log exists (e.g. /spads/var/spads_host01/log)

Disable plugins if not installed (autoloadplugins in spads.conf)


