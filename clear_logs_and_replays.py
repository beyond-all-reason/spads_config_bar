#!/bin/python

import os
import sys
import argparse
import codecs

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
	full_log = ""

	with codecs.open(fname, 'r', encoding='utf-8',
                 errors='ignore') as fdata:
		full_log = fdata.read()
		fdata.close()
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
				try:
					truncate_logfile(os.path.join(hostdir, logtotruncate))
				except:
					print ("Failed to clean log file", hostdir, logtotruncate)
		if os.path.isdir(os.path.join(hostdir,'demos-server')):
			cmd_delete_older_than_two_weeks = 'find %s/demos-server -type f -mtime +8 -delete | wc -l' %(hostdir)
			print ("Deleting Replays older than two weeks", cmd_delete_older_than_two_weeks)
			os.system(cmd_delete_older_than_two_weeks)
