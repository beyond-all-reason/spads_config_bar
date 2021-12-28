# Import the perl module so we can call the SPADS Plugin API
import perl
import traceback
import sys
import json
import base64
import zlib
import os
import time

# perl.BarManager is the Perl representation of the BarManager plugin module
# We will use this object to call the plugin API
spads = perl.BarManager

# ------------------ Instance global "constants" -------------

BMP = "BarManager|"
DBGLEVEL = 3
pluginParams = {}
# ---------------- Battleroom Variables to Track --------------
AiProfiles = {}  # dict of BotName : {username : Owner, profile: Defensive} dunno the format yet, should support script tags to set AI profiles
aiList = {}
isBattleLocked = False
ChobbyState = {}

TachyonBattle = {"boss":"", 'preset':"", 'ailist' : [], 'teamSize' : 6, 'nbTeams':2} # https://github.com/beyond-all-reason/teiserver/blob/master/documents/tachyon/types.md#battle
timerTachyonBattle = False # do we have a timer set to update the game?

myBattleID = None
playersInMyBattle = {}

whoIsBoss = None

aiProfiles = {}  # there are multiple ai profiles one can set, especially for barbarians, This info is currently discarded, but could use a new command

spadsConf = None  # {'lobbyReconnectDelay': 15, 'banList': 'empty', 'mapLink': 'http://springfiles.com/search_result.php?search=%m&select=select_all', 'promoteMsg': '%pplayer(s) needed for battle "%b" [%o, %a] (%u)', 'autoLock': 'off', 'lobbyPassword': 'petike', 'lobbyFollowRedirect': '1', 'lobbyHost': 'bar.teifion.co.uk', 'allowedLocalAIs': 'E323AI;HughAI;KAIK;RAI', 'logGameChat': '1', 'msgFloodAutoKick': '15;7', 'masterChannel': 'autohosts', 'allowGhostMaps': '0', 'maxBots': '16', 'lobbyInterfaceLogLevel': '5', 'opOnMasterChannel': '0', 'teamSize': 6, 'lobbyPort': '8200', 'commandsFile': 'commands.conf', 'unlockSpecDelay': '5;30', 'logPvChat': '1', 'extraBox': '0', 'alertDuration': '72', 'privacyTrustLevel': '130', 'springServer': '/home/eru/spads/var/spring/spring_bar_.BAR.104.0.1-1956-g0092498_linux-64-minimal-portable/spring-headless', 'simpleEventLogLevel': '5', 'springDataDir': '/home/eru/spads/var/spring/data', 'autoBlockColors': '0', 'autoManagedSpringDir': '/home/eru/spads/var/spring', 'rotationManual': 'random', 'rotationType': 'map;certified', 'defaultPreset': 'team', 'spoofProtection': 'warn', 'minPlayers': 1, 'welcomeMsgInGame': 'Hi %u (%d), welcome to %n .', 'shareId': '', 'autoCallvote': '1', 'ircColors': '0', 'voteMode': 'normal', 'autoStart': 'on', 'reCallVoteDelay': 10, 'springServerType': 'headless', 'promoteChannels': 'main', 'autoHostPort': '53199', 'welcomeMsg': 'Hi %u (%d), welcome to %n .', 'maxAutoHostMsgLength': '240', 'rotationEndGame': 'off', 'logBattleJoinLeave': '1', 'cmdFloodAutoIgnore': '8;8;4', 'pluginsDir': '/home/eru/spads/var/plugins', 'autoSpecExtraPlayers': '1', 'autoLearnMaps': '1', 'voteTime': 45, 'springConfig': '', 'description': 'Team Game Global Settings', 'advertDelay': '15', 'logChanChat': '0', 'kickFloodAutoBan': '5;120;5', 'dataDumpDelay': 60, 'clanMode': 'tag(5);pref(5)', 'nbTeams': 2, 'rotationEmpty': 'random', 'alertDelay': '6', 'lobbyLogin': '[teh]host15', 'botsRank': '3', 'hostingPreset': 'enginetesting', 'noSpecDraw': '0', 'autoManagedSpringVersion': '', 'battlePreset': 'team', 'autoAddBotNb': 0, 'freeSettings': 'autoLock;teamSize(1-8)', 'maxSpecs': '', 'colorSensitivity': 55, 'autoReloadArchivesMinDelay': 30, 'endGameAwards': '1', 'ghostMapLink': 'http://springfiles.com/search_result.php?search=%m&select=select_all', 'broadcastChannels': 'autohosts', 'maxChatMessageLength': 1024, 'logDir': '/home/eru/spads/var/spads_host15/log', 'autoBlockBalance': '1', 'autoHostInterfaceLogLevel': '5', 'hideMapPresets': '0', 'kickBanDuration': '300', 'maxBytesSent': 49000, 'logBattleChat': '1', 'useWin32Process': '0', 'map': 'Comet Catcher Remake 1.8', 'allowMapOptionsValues': '1', 'autoSaveBoxes': '2', 'voteRingDelay': '0', 'allowModOptionsValues': '1', 'eventModel': 'auto', 'promoteDelay': '600', 'maxLocalBots': '16', 'votePvMsgDelay': '0', 'maxRemoteBots': '16', 'statusFloodAutoKick': '24;8', 'userDataRetention': '-1;-1;-1', 'autoSetVoteMode': '1', 'logGameServerMsg': '1', 'instanceDir': '/home/eru/spads/var/spads_host15', 'maxLowPrioBytesSent': 48000, 'allowSettingsShortcut': '1', 'autoStop': 'gameOver', 'skillMode': 'TrueSkill', 'rankMode': 'account', 'localLanIp': '192.168.1.102', 'minTeamSize': '1', 'rotationDelay': 600, 'idShareMode': 'off', 'logChanJoinLeave': '0', 'forceHostIp': '', 'spadsLogLevel': '5', 'autoLockClients': 64, 'endGameCommandEnv': '', 'speedControl': '2', 'endGameCommand': '', 'autoLoadPlugins': 'BarManager;AutoRegister;JsonStatus;InGameMute', 'restoreDefaultPresetDelay': '30', 'springieEmulation': 'warn', 'logGameJoinLeave': '1', 'sendRecordPeriod': 5, 'noSpecChat': '0', 'autoLockRunningBattle': '0', 'balanceMode': 'clan;skill', 'updaterLogLevel': '5', 'varDir': '/home/eru/spads/var', 'midGameSpecLevel': '0', 'handleSuggestions': '0', 'unitsyncDir': '/home/eru/spads/var/spring/spring_bar_.BAR.104.0.1-1956-g0092498_linux-64-minimal-portable/', 'endGameCommandMsg': '', 'etcDir': '/home/eru/spads/etc', 'localBots': 'joe 0 E323AI;jim core#FF0000 KAIK', 'minRingDelay': '20', 'minVoteParticipation': '50', 'advertMsg': '', 'maxChildProcesses': '32', 'autoRestartForUpdate': 'off', 'forwardLobbyToGame': '1', 'nbPlayerById': 1, 'autoLoadMapPreset': '0', 'autoFixColors': 'advanced', 'preset': 'team', 'alertLevel': 130, 'autoBalance': 'advanced', 'maxSpecsImmuneLevel': '100', 'floodImmuneLevel': 100, 'autoUpdateRelease': '', 'mapList': 'all', 'autoUpdateDelay': '300'}

# getLobbyInterface(): 'acceptedHandler', 'addBotHandler', 'addCallbacks', 'addPreCallbacks', 'addStartRectHandler', 'addUserHandler', 'aindex', 'all', 'any', 'battleClosedHandler', 'battleOpenedHandler', 'channelTopicHandler', 'checkIntParams', 'checkTimeouts', 'clientBattleStatusHandler', 'clientIpPortHandler', 'clientStatusHandler', 'clientsHandler', 'connect', 'dclone', 'disableUnitsHandler', 'disconnect', 'enableAllUnitsHandler', 'enableUnitsHandler', 'first', 'forceAllyNoHook', 'forceTeamNoHook', 'generateStartData', 'getBattle', 'getBattles', 'getChannels', 'getLogin', 'getRunningBattle', 'getSkillValue', 'getUsers', 'getVersion', 'gracefulSocketShutdown', 'inet_aton', 'inet_ntoa', 'isTlsAvailable', 'joinBattleHandler', 'joinBattleHook', 'joinBattleRequestHandler', 'joinHandler', 'joinedBattleHandler', 'joinedHandler', 'leaveChannelHandler', 'leftBattleHandler', 'leftHandler', 'loginHook', 'marshallBattleStatus', 'marshallClientStatus', 'marshallColor', 'marshallCommand', 'marshallPasswd', 'md5_base64', 'new', 'none', 'notall', 'okHandler', 'openBattleHandler', 'openBattleHook', 'pack_sockaddr_in', 'pack_sockaddr_in6', 'pack_sockaddr_un', 'prioSort', 'receiveCommand', 'removeBotHandler', 'removeCallbacks', 'removePreCallbacks', 'removeScriptTagsHandler', 'removeStartRectHandler', 'removeUserHandler', 'sendCommand', 'setScriptTagsHandler', 'shuffle', 'sockaddr_family', 'sockaddr_in', 'sockaddr_in6', 'sockaddr_un', 'specSort', 'storeRunningBattle', 'tasserverHandler', 'unmarshallBattleStatus', 'unmarshallClientStatus', 'unmarshallColor', 'unmarshallCommand', 'unmarshallParams', 'unpack_sockaddr_in', 'unpack_sockaddr_in6', 'unpack_sockaddr_un', 'updateBattleInfoHandler', 'updateBotHandler', 'updateBotHook']


# ------------------ JSON OBJECT INFO ------------------
# Each json string will contain a dict, for example, for a votestart

# This is the first version of the plugin
pluginVersion = '0.1'

# This plugin requires a SPADS version which supports Python plugins
# (only SPADS versions >= 0.12.29 support Python plugins)
requiredSpadsVersion = '0.12.29'

# We define 2 global settings (mandatory for plugins implementing new commands):
# - commandsFile: name of the plugin commands rights configuration file (located in etc dir, same syntax as commands.conf)
# - helpFile: name of plugin commands help file (located in plugin dir, same syntax as help.dat)
globalPluginParams = {'crashDir': ['notNull'], 'crashFilePattern': ['notNull'], 'crashFilesToSave': ['notNull'],
					  'crashInfologPatterns': ['notNull'], 'chobbyGuiSettings': ['notNull'],
					  'barManagerDebugLevel': ['notNull'],
					  'commandsFile': ['notNull'],
					  'helpFile': ['notNull']
					  }
presetPluginParams = None

# This is how SPADS gets our version number (mandatory callback)
def getVersion(pluginObject):
	return pluginVersion

# This is how SPADS determines if the plugin is compatible (mandatory callback)
def getRequiredSpadsVersion(pluginName):
	return requiredSpadsVersion

# This is how SPADS finds what settings we need in our configuration file (mandatory callback for configurable plugins)
def getParams(pluginName):
	return [globalPluginParams, presetPluginParams]

def jsonGzipBase64(toencode):
	return base64.b64encode(zlib.compress(json.dumps(toencode).encode("utf-8"))).decode() 

def jsonBase64(toencode):
	return base64.b64encode(json.dumps(toencode).encode("utf-8")).decode()

def SendChobbyState():
	try:
		barmanagermessage = BMP + json.dumps({"BattleStateChanged": ChobbyState})
		spads.sayBattle(barmanagermessage)
		spads.slog(barmanagermessage, DBGLEVEL)
	except Exception as e:
		spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

def ChobbyStateChanged(changedKey, changedValue):
	try:
		if changedKey not in ChobbyState or (changedKey in ChobbyState and ChobbyState[changedKey] != changedValue):
			ChobbyState[changedKey] = changedValue
			SendChobbyState()
		else:
			spads.slog("No change in battle state: %s:%s" % (changedKey, changedValue), DBGLEVEL)


	except Exception as e:
		spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

def refreshChobbyState():
	spadsConf = spads.getSpadsConf()
	ChobbyState['autoBalance'] = spadsConf['autoBalance']
	ChobbyState['teamSize'] = str(spadsConf['teamSize'])
	updateTachyonBattle('teamSize',spadsConf['teamSize'] )
	ChobbyState['nbTeams'] = str(spadsConf['nbTeams'])
	updateTachyonBattle('nbTeams',spadsConf['nbTeams'] )

	ChobbyState['balanceMode'] = spadsConf['balanceMode']
	ChobbyState['preset'] = spadsConf['preset']
	updateTachyonBattle('preset',spadsConf['preset'] )
	SendChobbyState()

def sendTachyonBattle():
	global timerTachyonBattle, TachyonBattle
	try:
		timerTachyonBattle = False
		bsjson = json.dumps(TachyonBattle)
		spads.slog("Trying to update tachyonbattlestatus " + bsjson,DBGLEVEL)
		spads.queueLobbyCommand(["c.battle.update_host", json.dumps(TachyonBattle)])
	except Exception as e:
		spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)


def updateTachyonBattle(key, value):
	global timerTachyonBattle
	# Manages the Tachyon Battle State, a list of keys are passed which update the dicts
	try:
		if key not in TachyonBattle or TachyonBattle[key] != value:
			TachyonBattle[key] = value


			#spads.queueLobbyCommand() # message = "c.telemetry.log_client_event  " .. cmdName .. " " ..args.." ".. machineHash .. "\n"
			if not timerTachyonBattle:
				spads.addTimer("TachyonBattleTimer", 3, 0, sendTachyonBattle)
				timerTachyonBattle = True
			return True

		#lets set a timer to update every 5 secs only :)

	except Exception as e:
		spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)
	return False

# This is the class implementing the plugin
class BarManager:

	# This is our constructor, called when the plugin is loaded by SPADS (mandatory callback)
	def __init__(self, context):
		global DBGLEVEL
		# We declare our new command and the associated handler
		spads.addSpadsCommandHandler({'myCommand': hMyCommand})
		spads.addSpadsCommandHandler({'aiProfile': hAiProfile})
		spads.addSpadsCommandHandler({'splitbattle': hSplitBattle})

		# Declare handler for lobby commands (see https://springrts.com/dl/LobbyProtocol/ProtocolDescription.html)
		spads.addLobbyCommandHandler({"JOINEDBATTLE": hJOINEDBATTLE})
		spads.addLobbyCommandHandler({"LEFTBATTLE": hLEFTBATTLE})
		spads.addLobbyCommandHandler({"REMOVEBOT": hREMOVEBOT})
		spads.addLobbyCommandHandler({"ADDBOT": hADDBOT})
		spads.addLobbyCommandHandler({"UPDATEBATTLEINFO": hUPDATEBATTLEINFO })

		# We call the API function "slog" to log a notice message (level 3) when the plugin is loaded
		spads.slog("Plugin loaded (version %s)" % pluginVersion, 3)
		if spads.get_flag("can_add_socket"):
			spads.slog("This plugin can use sockets", 3)
		if spads.get_flag("can_fork"):
			spads.slog("This plugin can fork processes", 3)
		if spads.get_flag("use_byte_string"):
			spads.slog("This plugin can uses byte strings", 3)

		try:
			pluginParams = spads.getPluginConf()
			DBGLEVEL = int(pluginParams['barManagerDebugLevel'])
			spadsConf = spads.getSpadsConf()
			spads.slog("pluginParams = " + str(pluginParams), DBGLEVEL)
			CrashDir = os.path.join(spadsConf['varDir'], 'log', pluginParams['crashDir'])
			if not os.path.exists(CrashDir):
				spads.slog("Created CrashDir" + CrashDir, DBGLEVEL)
				os.makedirs(CrashDir)
			else:
				spads.slog("OK:CrashDir already exists" + CrashDir, DBGLEVEL)

		except Exception as e:
			spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

	# This is the callback called when the plugin is unloaded
	def onUnload(self, reason):

		# We remove our new command handler
		spads.removeSpadsCommandHandler(['myCommand'])

		# We log a notice message when the plugin is unloaded
		spads.slog("Plugin unloaded", 3)

	def onBattleOpened(self):
		global myBattleID  # todo: this is the slipperiest slope of all
		global ChobbyState
		try:
			spads.slog("Battle Opened", DBGLEVEL)
			# spads.queueLobbyCommand(["!preset coop","!map DSDR"])
			# spads.addTimer("initrandommap",5, 0, lambda : spads.queueLobbyCommand(["map Talus"]))
			# spads.addTimer("yell",5, 0, lambda : spads.sayPrivate("[teh]Beherith","hi"))

			# dump stuff for testing
			# spadsdir = dir(spads)
			# spads.slog(str(spadsdir),3)

			# confFull = spads.getSpadsConfFull()
			# spads.slog("maps=" + str(confFull.maps),3)

			# spads.slog(type(confFull),3)
			# spads.slog(str(confFull),3)
			# attrs = vars(confFull)
			# spads.slog(attrs,3)
			# attrs2 = dir(attrs)
			# spads.slog("attrdirdir:"+str(attrs2)+str(attrs.keys()),3)
			# for k in sorted(attrs.keys()):
			#	spads.slog("%s:%s"%(str(k),str(attrs[k])),3)
			# spadsconf = spads.getSpadsConf()
			# spadsconf['map'] = "TheRock_V2"
			# a = None
			# b = a + 1 # this is just a try:except: test

			spadsConf = spads.getSpadsConf()
			spads.slog("Trying to print spads configuration:", 3)

			spads.slog("getRunningBattle()" + str(dir(spads.getRunningBattle())), 3)
			# TODO: Init battlestatuschanged sanely!

			# spads.slog(str(spadsConf),3)
			lobbyInterface = spads.getLobbyInterface()

			# spads.slog("getLobbyInterface()" + str(dir(lobbyInterface)),3)

			# spads.slog(str(lobbyInterface.getBattles()),3) # this works, and gets all battles
			spads.slog(str(lobbyInterface.getBattle()),
					   3)  # {'scriptTags': {}, 'password': '*', 'founder': '[teh]host15', 'startRects': {'0': {'left': '0', 'right': '34', 'top': '0', 'bottom': '200'}, '1': {'left': '166', 'bottom': '200', 'top': '0', 'right': '200'}}, 'botList': [], 'modHash': '-1321904802', 'battleId': '99', 'users': {'[teh]host15': {'port': None, 'battleStatus': None, 'ip': None, 'color': None}}, 'bots': {}, 'disabledUnits': []}
			myBattle = lobbyInterface.getBattle()
			myBattleID = myBattle['battleId']
			spads.slog("My BattleID is:" + str(myBattleID), 3)  #
			ChobbyState['locked'] = 'unlocked' # this is assumed by server when opening a battleroom
			refreshChobbyState()


		# for k,v in lobbyInterface:
		#	spads.slog(str((k,v)), 3)

		# spads.slog("getLobbyInterface() keys" + str(vars(spads.getLobbyInterface())), 3)
		# spads.slog("getLobbyInterface()" + str(spads.getLobbyInterface()),3)

		# for k in sorted(attrs.keys()):
		#	spads.slog("%s:%s"%(str(k),str(attrs[k])),3)

		except Exception as e:
			spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

	def onGameEnd(self, endGameData):
		# The \%endGameData parameter is a reference to a hash containing all the data stored by SPADS concerning the game that just ended.
		# TODO: Send all of this lovely endGameData dict as a base64 encoded json to the bot account called AutohostMonitor as a private message
		try:
			spads.slog("onGameEnd", DBGLEVEL)
			spads.slog("endGameData" + str(endGameData), 3)
			spads.sayPrivate('AutohostMonitor', 'endGameData ' + jsonBase64(endGameData))

		except Exception as e:
			spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

	def onJoinBattleRequest(self, userName, ipAddr):
		# todo: send whole battle state to user
		try:
			spads.slog("onJoinBattleRequest:" + str(userName), DBGLEVEL)
		except Exception as e:
			spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)
		return 0  # return 1 if the user isnt allowed to join (return string for reason)

	def onPresetApplied(self, oldPresetName, newPresetName):
		# todo: send the updated preset to all battle participants
		try:
			spads.slog("onPresetApplied: " + str(oldPresetName) + " -> " + str(newPresetName), DBGLEVEL)
			refreshChobbyState()
		except Exception as e:
			spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

	def onPrivateMsg(self, userName, message):
		# todo: nothing yet
		try:
			spads.slog("onPrivateMsg: " + str([userName, message]), DBGLEVEL)

		except Exception as e:
			spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)
		return 0  # return 1 if dont want Spads core to parse this message

	def onVoteRequest(self, source, user, command, remainingVoters):
		# $source indicates the way the vote has been requested ("pv": private lobby message, "battle": battle lobby message, "chan": master lobby channel message, "game": in game message)
		# $user is the name of the user requesting the vote
		# \@command is an array reference containing the command for which a vote is requested
		# \%remainingVoters is a reference to a hash containing the players allowed to vote. This hash is indexed by player names. Perl plugins can filter these players by removing the corresponding entries from the hash directly, but Python plugins must use the alternate method based on the return value described below.
		try:
			spads.slog("onVoteRequest: " + ','.join(map(str, [source, user, command, remainingVoters])), DBGLEVEL)

		except Exception as e:
			spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)
		return 1  # allow the vote, 0 for disallow

	def onVoteStart(self, user, command):
		# command is an array reference containing the command for which a vote is started
		try:
			spads.slog("onVoteStart: " + ','.join(map(str, [user, command])), DBGLEVEL)
			barmanagermessage = BMP + json.dumps({"onVoteStart": {'user': user, 'command': command}})
			spads.sayBattle(barmanagermessage)
			spads.slog(barmanagermessage, DBGLEVEL)
		except Exception as e:
			spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

	def onVoteStop(self, voteResult):
		# This callback is called each time a vote poll is stoped.
		# $voteResult indicates the result of the vote: -1 (vote failed), 0 (vote cancelled), 1 (vote passed)
		try:
			spads.slog("onVoteStop: voteResult=" + str(voteResult), DBGLEVEL)

		except Exception as e:
			spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

	def onSpringStop(self, springPid):
		# This callback is called each time the Spring process ends.
		try:
			spadsConf = spads.getSpadsConf()
			spads.slog("onSpringStop: springPid=" + str(springPid), DBGLEVEL)
			instanceDir = spadsConf["instanceDir"]
			pluginParams = spads.getPluginConf()

			crashDir = os.path.join(spadsConf['varDir'], 'log', pluginParams['crashDir'])
			# Check for spring has crashed, and save the script and the infolog.txt
			infologlines = open(instanceDir + "/infolog.txt").readlines()
			for line in infologlines:
				for pattern in pluginParams['crashInfologPatterns'].split('|'):
					if pattern in line:
						for crashFileToSave in pluginParams['crashFilesToSave'].split('|'):
							outf = open(os.path.join(crashDir, pluginParams['crashFilePattern'] % (
								int(time.time()), crashFileToSave)), 'w')
							outf.write(''.join(open(os.path.join(instanceDir, crashFileToSave)).readlines()))
							outf.close()
						break

		except Exception as e:
			spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

	def onSpringStart(self, springPid):
		# This callback is called each time a Spring process is launched to host a game.
		try:
			spads.slog("onSpringStart: springPid=" + str(springPid), DBGLEVEL)
		except Exception as e:
			spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

	def preGameCheck(self, force, checkOnly, automatic):
		# This callback is called each time a game is going to be launched, to allow plugins to perform pre-game checks and prevent the game from starting if needed.
		# $force is 1 if the game is being launched using !forceStart command, 0 else
		# $checkOnly is 1 if the callback is being called in the context of a vote call, 0 else
		# $automatic is 1 if the game is being launched automatically through autoStart functionality, 0 else
		# The return value must be the reason for preventing the game from starting (for example "too many players for current map"), or 1 if no reason can be given, or undef to allow the game to start.
		# todo: dont allow startpostype = (fixed or random) on maps with less start positions than players!
		try:
			spads.slog("preGameCheck: " + ','.join(map(str, [force, checkOnly, automatic])), DBGLEVEL)
		except Exception as e:
			spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)
		return None  #

	def postSpadsCommand(self, command, source, user, params, commandResult):
		# This callback is called each time a SPADS command has been called.
		# $command is the name of the command (without the parameters)
		# $source indicates the way the command has been called ("pv": private lobby message, "battle": battle lobby message, "chan": master lobby channel message, "game": in game message)
		# $user is the name of the user who called the command
		# \@params is a reference to an array containing the parameters of the command
		# $commandResult indicates the result of the command (if it is defined and set to 0 then the command failed, in all other cases the command succeeded)
		# todo: say the results of the changed stuff in battle room
		try:
			spads.slog("postSpadsCommand: " + ','.join(map(str, [command, source, user, params, commandResult])), DBGLEVEL)
			global whoIsBoss
			if command == "lock":
				ChobbyStateChanged("locked", "locked")
			elif command == "unlock":
				ChobbyStateChanged("locked", "unlocked")
			elif command == "set":  # autoLock|autoStart|autoBalance|autoFixColors|nbTeams|balanceMode|clanMode|locked|preset
				lowercommand = params[0].lower()
				if lowercommand == 'autobalance':
					ChobbyStateChanged("autoBalance", params[1])
				elif lowercommand == 'balancemode':
					ChobbyStateChanged("balanceMode", params[1])
				elif lowercommand == 'nbteams':
					ChobbyStateChanged("nbTeams", params[1])
				elif lowercommand == 'teamsize':
					ChobbyStateChanged("teamSize", params[1])

			elif command == "vote":
				# todo: also pass vote status here!
				if params[0] in ['yes', 'y', 'no', 'n', 'blank', 'b']:
					if params[0] == 'yes':
						pass
			elif command == "boss":
				if len(params) == 0:
					whoIsBoss = None
				else:
					whoIsBoss = params[0]
				updateTachyonBattle('boss',whoIsBoss)

		except Exception as e:
			spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)
		return None  #

	def preSpadsCommand(self, command, source, user, params):
		# This callback is called each time a SPADS command is called, just before it is actually executed.
		# $command is the name of the command (without the parameters)
		# $source indicates the way the command has been called ("pv": private lobby message, "battle": battle lobby message, "chan": master lobby channel message, "game": in game message)
		# $user is the name of the user who called the command
		# \@params is a reference to an array containing the parameters of the command
		# This callback must return 0 to prevent the command from being processed by other plugins and SPADS core, or 1 to allow it.
		try:
			spads.slog("preSpadsCommand: " + ','.join(map(str, [command, source, user, params])), DBGLEVEL)
		except Exception as e:
			spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)
		return 1

	def filterRotationMaps(self, rotationMaps):
		try:
			spads.slog("filterRotationMaps: rotationMaps=" + str(rotationMaps), DBGLEVEL)
		except Exception as e:
			spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

		return rotationMaps  # The callback must return a reference to a new array containing the filtered map names

	def addStartScriptTags(self, additionalData):
		global AiProfiles
		'''
			[ai1]
			{
				[options]
				{
					comm_merge = true;
					cheating = false;
					profile = porc;
					disabledunits = ;
					ally_aware = true;
				}
				Host = 0;
				IsFromDemo = 0;
				Name = BARbarianAI(1);
				ShortName = BARb;
				Team = 2;
				Version = stable;
		}
		  [AI0]
		  {
			Name=BARbarianAI(1);
			ShortName=BARb;
			Team=1;
			Host=0;
			[options]
			{
			  testtag=testvalue;
			}
		  }
		
		'''

		try:
			spads.slog("addStartScriptTags: "+ str(AiProfiles), 3)
			if len(AiProfiles) > 0:
				extraaitags = {}
				for botname, aiprofile in AiProfiles.items():
					extraaitags[botname] = {'options': aiprofile}
					spads.slog("Setting AI profile" + str(extraaitags) + ' for ' + botname, 3)

				return {'aiData': extraaitags}
		except Exception as e:
			spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)
		return {}


# This is the handler for our new command
def hMyCommand(source, user, params, checkOnly):
	# checkOnly is true if this is just a check for callVote command, not a real command execution
	if checkOnly:
		# MyCommand is a basic command, we have nothing to check in case of callvote
		return 1

	# Fix strings received from Perl if needed
	# This is in case Inline::Python handles Perl strings as byte strings instead of normal strings
	# (this step can be skipped if your Inline::Python version isn't afffected by this bug)
	user = spads.fix_string(user)
	for i in range(len(params)):
		params[i] = spads.fix_string(params[i])

	# We join the parameters provided (if any), using ',' as delimiter
	paramsString = ','.join(params)

	# We log the command call as notice message
	spads.slog("User %s called command myCommand with parameter(s) \"%s\"" % (user, paramsString), 3)


# This is the handler for our new command
def hAiProfile(source, user, params, checkOnly):  # !aiProfile BARbarianAI(1) {"testtag":"testvalue"}
	try:
		# checkOnly is true if this is just a check for callVote command, not a real command execution
		if checkOnly:
			return 1  # no need to check CV
		lobbyInterface = spads.getLobbyInterface()
		battle = lobbyInterface.getBattle()

		spads.slog(str(lobbyInterface.getBattle()),  DBGLEVEL)
		# 'users': {'[teh]host15': {'color': {'green': 255, 'red': 255, 'blue': 255}, 'battleStatus': {'team': 0, 'ready': '1', 'sync': 1, 'side': 0, 'bonus': 0, 'id': 0, 'mode': '0'}, 'port': None, 'ip': None},
		# 			'[teh]Behe_Chobby3': {'port': None, 'scriptPass': '070b4b5f', 'ip': None, 'battleStatus': {'team': 0, 'id': 0, 'bonus': 0, 'mode': '1', 'ready': '0', 'sync': 2, 'side': 0}, 'color': {'red': 255, 'blue': 0, 'green': 255}}},
		# 			'modHash': '-1321904802', 'founder': '[teh]host15',
		# {'bots': {'Bot1': {'owner': '[teh]Behe_Chobby3', 'color': {'red': 0, 'blue': 255, 'green': 0}, 'aiDll': 'BARb|stable', 'battleStatus': {'ready': '1', 'sync': 1, 'side': 0, 'id': 1, 'bonus': 0, 'mode': '1', 'team': 1}}}, 'battleId': '268', 'botList': ['Bot1']}

		botlist = [] if 'botList' not in battle else battle['botList']
		bots = {} if 'bots' not in battle else battle['bots']

		botName = params[0]
		profileInfo = ' '.join(params[1:])

		if botName not in botlist:
			spads.sayBattle(" %s is not an existing bot name"%(botName))
		else:
			if user != bots[botName]['owner']:
				spads.sayBattle("AI %s is not owned by player %s"% (botName,user))
			else:
				try:
					profileInfo = json.loads(profileInfo)
					if type(profileInfo) != type({}):
						raise
					AiProfiles[botName] = profileInfo
				except:
					spads.sayBattle("Unable to parse profile info json dict: %s"%(profileInfo))
					return
				spads.sayBattle("AI %s options are set to %s" % (botName, profileInfo))
		# We log the command call as notice message
		spads.slog("User %s called command hAiProfile with parameter(s) \"%s\"" % (user, ','.join(params)), 3)

	except Exception as e:
		spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

def hSplitBattle(source, user, params, checkOnly):
	# checkOnly is true if this is just a check for callVote command, not a real command execution
	if checkOnly:
		# MyCommand is a basic command, we have nothing to check in case of callvote
		return 1

	# Fix strings received from Perl if needed
	# This is in case Inline::Python handles Perl strings as byte strings instead of normal strings
	# (this step can be skipped if your Inline::Python version isn't afffected by this bug)
	user = spads.fix_string(user)
	for i in range(len(params)):
		params[i] = spads.fix_string(params[i])

	# We join the parameters provided (if any), using ',' as delimiter
	paramsString = ','.join(params)

	# We log the command call as notice message
	spads.slog("User %s called command hSplitBattle with parameter(s) \"%s\"" % (user, paramsString), 3)

def updatebotlist():
	lobbyInterface = spads.getLobbyInterface()
	battle = lobbyInterface.getBattle()
	spads.slog(str(battle['bots']), DBGLEVEL)
	bots = {} if 'bots' not in battle else battle['bots']
	uniquebottypes = []
	for botname, botinfo in bots.items():
		if botinfo['aiDll'] not in uniquebottypes:
			uniquebottypes.append(botinfo['aiDll'])
	updateTachyonBattle('botlist', uniquebottypes)


# botlist = [] if 'botList' not in battle else battle['botList']
# 'users': {'[teh]host15': {'color': {'green': 255, 'red': 255, 'blue': 255}, 'battleStatus': {'team': 0, 'ready': '1', 'sync': 1, 'side': 0, 'bonus': 0, 'id': 0, 'mode': '0'}, 'port': None, 'ip': None},
# 			'[teh]Behe_Chobby3': {'port': None, 'scriptPass': '070b4b5f', 'ip': None, 'battleStatus': {'team': 0, 'id': 0, 'bonus': 0, 'mode': '1', 'ready': '0', 'sync': 2, 'side': 0}, 'color': {'red': 255, 'blue': 0, 'green': 255}}},
# 			'modHash': '-1321904802', 'founder': '[teh]host15',
# {'bots': {'Bot1': {'owner': '[teh]Behe_Chobby3', 'color': {'red': 0, 'blue': 255, 'green': 0}, 'aiDll': 'BARb|stable', 'battleStatus': {'ready': '1', 'sync': 1, 'side': 0, 'id': 1, 'bonus': 0, 'mode': '1', 'team': 1}}}, 'battleId': '268', 'botList': ['Bot1']}

def hREMOVEBOT(command, battleID, botName):
	try:
		if battleID == myBattleID:
			if botName in AiProfiles:
				del AiProfiles[botName]
			updatebotlist()

	except:
		spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

def hADDBOT(command, battleID, name, owner, battleStatus, teamColor, aidll):
	try:
		updatebotlist()


	except:
		spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

def hUPDATEBATTLEINFO(command, battleID, spectatorCount, locked, mapHash, mapName):
	try:
		spads.slog(str(['hUPDATEBATTLEINFO',battleID,locked]),  DBGLEVEL)
		if battleID == myBattleID:
			ChobbyStateChanged("locked","locked" if locked == '1' else 'unlocked')
	except:
		spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

def hLEFTBATTLE(command, battleID, userName):
	global whoIsBoss
	try:
		if battleID == myBattleID and playersInMyBattle[userName]:
			spads.slog("LEFTBATTLE" + str([command, battleID, userName]), 3)
			del playersInMyBattle[userName]
			if whoIsBoss == userName:
				whoIsBoss = None
				updateTachyonBattle("boss","")
	except Exception as e:
		spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)


def hJOINEDBATTLE(command, battleID, userName, battlestatus=0):
	try:
		if battleID == myBattleID:
			spads.slog("JOINEDBATTLE" + str([command, battleID, myBattleID, userName, battlestatus]), DBGLEVEL)
			SendChobbyState()
			playersInMyBattle[userName] = battlestatus
			#spads.queueLobbyCommand(["SAYBATTLEEX", "hello dude"])
	except Exception as e:
		spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

