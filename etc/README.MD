# Use spads_coop_instance.conf

The spads_coop_instance.conf config is the one to use for SPADS.

# running spads clusters:

CHECKLIST:

1. Look in spads_cluster_launcher.sh and change all relevant varaibles. 

2. Make sure you have the correct engine installed and specified

3. Make sure you have the autoregister and clustermanager plugins installed (included in repo)

4. Make sure your clustermanager account is set to admin flag in lobby server



Run spads with ./spads_cluster_launcher.sh

Some ramblings (Beherith) about running autohosts:
- Running autohosts by third parties is not encouraged by default. Please get in touch with developers if you want to do this. You will need to do this anyway to obtain botflags. 
- If you do, make sure you have all of the users permissions (BAR devs) set accordingly
- Please adhere to the certified/official maps list, exemption requests are welcome.
- Please try to adhere to the setup in the default spads.conf in this repo
- Attempt to use the springsettings.cfg in this repo
- Keep your hosts up to date (pr-downloader timer service, byar-maps timer service)
