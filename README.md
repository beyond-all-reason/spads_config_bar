This directory contains the configuration information and map-game updater scripts to successfully host a SPADS instance for BAR

**This repository is synced to all spads instances at noon UTC**

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

Install dependency

```
sudo apt-get install -y python3-paho-mqtt
```

Install script (as root after `sudo -i`)

```
curl -L https://raw.githubusercontent.com/beyond-all-reason/maps-metadata/main/tools/map_syncer/map_syncer.py > /usr/local/bin/map_syncer.py
sudo chmod +x /usr/local/bin/map_syncer.py
```

Copy `map_syncer.service` to

```
/etc/systemd/system
```

Modify the service file by updating:
- spads-map-sync-**us1** to correct server name
- last argument to correct directory with maps 

Enable service

```
systemctl daemon-reload
systemctl enable map_syncer
systemctl start map_syncer
```

Check it's running and started downloading maps:

```
systemctl status map_syncer
```

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

# Spadsupdater packages required:

needs p7zip-full to be able to update engine easily

and perl cpan Inline::Python for BarManager

# Running spads clusters:

CHECKLIST:

1. Look in spads_cluster_launcher.sh and change all relevant varaibles. 

2. Make sure you have the correct engine installed and specified

3. Make sure you have the autoregister and clustermanager plugins installed (included in repo)

4. Make sure your clustermanager account is set to admin flag in lobby server


Run spads with ./spads_cluster_launcher.sh

# Policy
 
Some ramblings (Beherith) about running autohosts:
- Running autohosts by third parties is not encouraged by default. Please get in touch with developers if you want to do this. You will need to do this anyway to obtain botflags. 
- If you do, make sure you have all of the users permissions (BAR devs) set accordingly
- Please adhere to the certified/official maps list, exemption requests are welcome.
- Please try to adhere to the setup in the default spads.conf in this repo
- Attempt to use the springsettings.cfg in this repo
- Keep your hosts up to date (pr-downloader timer service, byar-maps timer service)

