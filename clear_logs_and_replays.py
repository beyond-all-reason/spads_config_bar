#!/bin/python

import os
import sys
import argparse

if __file__:
	scriptdir = os.path.dirname(os.path.realpath(__file__))
	if scriptdir != os.getcwd():
		print("Changing working directory to the scripts path:", os.path.dirname(os.path.realpath(__file__)))
		os.chdir(scriptdir)
		
os.chdir('../var/ClusterManager')

logstotruncate = [
'log/spring-dedicated.log',
'log/spads.log',
'log/spads.log',
'log/chat/game.log',
'log/chat/battle.log',
'log/chat/pv_AutohostMonitor.log',
]

def truncate_logfile(fname, keepsize = 100000):
	fp = open(fname)
	full_log = fp.read()
	fp.close()
	trunc = full_log[-keepsize:]
	
	print(fname, len(full_log)/1000000.0,'MB', full_log[-50:])
	
	fp = open(fname,'w')
	fp.write(trunc)
	fp.close()
	return 

for hostdir in os.listdir(os.getcwd()):
	if os.path.isdir(hostdir):
		print (hostdir)
		for logtotruncate in logstotruncate:
			if os.path.isfile(os.path.join(hostdir, logtotruncate)):
				#print (logtotruncate)
				truncate_logfile(os.path.join(hostdir, logtotruncate))
		if os.path.isdir(os.path.join(hostdir,'demos-server')):
			cmd_delete_older_than_month = 'find %s/demos-server -type f -mtime +30 -delete | wc -l' %(hostdir)
			print ("Deleting Replays older than a month", cmd_delete_older_than_month)
			os.system(cmd_delete_older_than_month)
