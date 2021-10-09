# Captains Draft Plugin
# This plugin provides a mode to pick teams whereby assigned captains take turns drafting players

# Author: Jazcash

# Usage: !preset captainsdraft
# Everybody gets forced to spec and anybody who wishes to play must type !add
# Players can !remove at any time, or leave the lobby, and the plugin will revert to the adding state
# !draft must then be called to begin the drafting phase. An even number of players is required to begin drafting
# The two highest TS players are then automatically made captains of each team
# The lowest TS of the two captains gets first pick. Players are picked with !pick [username]
# Players are picked one after another, until all players are picked

import perl
import sys
import traceback
from collections import Counter
from datetime import datetime

spads=perl.CaptainsDraftPlugin
pluginVersion='0.1'
requiredSpadsVersion='0.12.29'
globalPluginParams = { 'commandsFile': ['notNull'],
                       'helpFile': ['notNull'] }
presetPluginParams = None

lobbyInterface = spads.getLobbyInterface()
accountIdSkill = {}
playerNameSkill = {}

def getVersion(pluginObject):
    return pluginVersion

def getRequiredSpadsVersion(pluginName):
    return requiredSpadsVersion

def getParams(pluginName):
    return [globalPluginParams, presetPluginParams]

class CaptainsDraftPlugin:
    def __init__(self, context):
        self.reset()

        spads.addSpadsCommandHandler({
            'add': self.add,
            'draft': self.draft,
            'remove': self.remove,
            'pick': self.pick
        })

        spads.slog("Plugin loaded (version %s)" % pluginVersion, 3)

    def reset(self):
        self.state = "disabled" # disabled, adding, drafting, ready
        self.addedPlayers = set()
        self.playerPool = set()
        self.teamApicking = False
        self.teamAcap = ""
        self.teamBcap = ""
        self.teamA = set()
        self.teamB = set()

    def onLobbyConnected(self, _lobbyInterface):
        self.__init__()

    def onUnload(self, reason):
        spads.removeSpadsCommandHandler(['add', "remove", "draft", "pick"])
        spads.removeLobbyCommandHandler(['CLIENTBATTLESTATUS'])

        spads.slog("Plugin unloaded", 3)

    def onBattleClosed(self):
        self.reset()

    def onSpringStop(self):
        spads.sayBattle(f"Game ended, returning to adding state")
        self.reset()
        self.resetToAddingState()

    def onPresetApplied(self, oldPresetName, newPresetName):
        if (newPresetName == "captainsdraft"):
            self.disable()
            self.enable()
        else:
            self.disable()

    def onLeftBattle(self, userName):
        try:
            if (userName not in self.addedPlayers):
                return

            self.addedPlayers.discard(userName)

            if self.state == "adding":
                self.printAddedPlayers()
            elif self.state == "drafting" or self.state == "ready":
                self.resetToAddingState()
        except Exception as e:
            spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

    def onJoinedBattle(self, userName):
        try:
            if (self.state != "disabled"):
                addMsg = " Type !add if you wish to play"
                draftMessage = " You must wait for the next draft to play"
                extraMsg = addMsg if self.state == "adding" else draftMessage
                spads.sayBattle(f"Welcome to Captains Draft, {userName}. Currently in {self.state} state.{extraMsg}")
        except Exception as e:
            spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

    def enable(self):
        try:
            self.state = "adding"
            spads.sayBattle('Captains Draft enabled, forcing all players to spectators. Type !add if you wish to play, and !draft to begin picking. !remove if you wish to unadd')

            spads.addTimer("correctUserStates", 0, 1, self.correctUsersStates)
        except Exception as e:
            spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

    def disable(self):
        try:
            self.reset()

            spads.removeTimer("correctUserStates")
        except Exception as e:
            spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

    def resetToAddingState(self):
        self.state = "adding"
        self.teamA = set()
        self.teamB = set()
        spads.sayBattle(f"A player removed, returning to adding state")
        self.printAddedPlayers()

    def add(self, source, user, params, checkOnly):
        try:
            if (self.state != "adding"):
                spads.answer(f"Cannot add while in the {self.state} state")
                return 0

            if (user in self.addedPlayers):
                spads.answer(f"You are already added, {user}")
                return 0

            self.addedPlayers.add(user)
            self.printAddedPlayers()
        except Exception as e:
            spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

    def remove(self, source, user, params, checkOnly):
        try:
            if (self.state != "adding" and self.state != "drafting"):
                spads.answer(f"Cannot remove while in the {self.state} state")
                return 0

            if (user not in self.addedPlayers):
                spads.answer(f"You are already removed, {user}")
                return 0

            self.addedPlayers.discard(user)

            if (self.state == "drafting"):
                self.resetToAddingState()
            else:
                self.printAddedPlayers()

        except Exception as e:
            spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

    def draft(self, source, user, params, checkOnly):
        try:
            if (self.state != "adding"):
                spads.answer(f"Cannot start draft while Captains Draft is in the {self.state} state")
                return 0

            if (len(self.addedPlayers) % 2 != 0):
                spads.sayBattle(f"Can't start draft without an even number of players ({len(self.addedPlayers)} added)")
                return 0

            if (len(self.addedPlayers) < 6):
                spads.sayBattle(f"Can't start draft with less than 6 added players ({len(self.addedPlayers)} added)")
                return 0

            if (checkOnly):
                return 1

            self.state = "drafting"
            self.playerPool = self.addedPlayers.copy()
            self.updateSkills()
            self.assignCaptainsBySkill()
            self.printRemainingPlayers()
        except Exception as e:
            spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

    def pick(self, source, user, params, checkOnly):
        try:
            if (self.state != "drafting"):
                spads.answer(f"Cannot pick player while Captains Draft is in the {self.state} state")
                return 0

            if len(params) == 0:
                spads.sayBattle(f"You must pick a player, e.g. !pick bob")
                return 0

            pickedPlayer = params[0]
            cap = self.teamAcap if self.teamApicking else self.teamBcap
            otherCap = self.teamAcap if not self.teamApicking else self.teamBcap

            if ((user != self.teamAcap and user != self.teamBcap) or (user == self.teamAcap and not self.teamApicking) or (user == self.teamBcap and self.teamApicking)):
                spads.sayBattle(f"Only {cap} can !pick now")
                return 0

            if ((pickedPlayer in self.teamA) or (pickedPlayer in self.teamB)):
                spads.sayBattle(f"{pickedPlayer} has already been picked")
                return 0

            if (pickedPlayer not in self.playerPool):
                spads.sayBattle(f"{pickedPlayer} is not added")
                return 0

            self.playerPool.discard(pickedPlayer)
            if self.teamApicking:
                self.teamA.add(pickedPlayer)
            else:
                self.teamB.add(pickedPlayer)

            self.teamApicking = not self.teamApicking

            if (len(self.playerPool) > 1):
                self.printRemainingPlayers(f"{cap} picked {pickedPlayer}. ")
            else:
                lastUnpickedPlayer = self.playerPool.pop()
                spads.sayBattle(f"{lastUnpickedPlayer} is last pick so goes to {otherCap}\'s team")
                if self.teamApicking:
                    self.teamA.add(lastUnpickedPlayer)
                else:
                    self.teamB.add(lastUnpickedPlayer)

                self.ready()
        except Exception as e:
            spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

    def printRemainingPlayers(self, msg = ""):
        try:
            cap = self.teamAcap if self.teamApicking else self.teamBcap
            remainingPlayers = ', '.join(list(self.playerPool))
            spads.sayBattle(f"{msg}It is {cap}\'s turn to !pick. Remaining players: {remainingPlayers}")
        except Exception as e:
            spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)
    
    def printAddedPlayers(self):
        spads.sayBattle(f"{len(self.addedPlayers)} players added. Call !draft when ready to start picking")

    def updatePlayerSkill(self, playerSkill, accountId, modName, gameType):
        try:
            accountIdSkill[accountId] = float(playerSkill["skill"])
        except Exception as e:
            spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

    def updateSkills(self):
        try:
            lobbyInterface = spads.getLobbyInterface()
            serverUsers = lobbyInterface.getUsers()
            for playerName in serverUsers:
                player = serverUsers[playerName]
                accountId = player["accountId"]
                if accountId in accountIdSkill:
                    playerNameSkill[playerName] = accountIdSkill[player["accountId"]]
        except Exception as e:
            spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

    def assignCaptainsBySkill(self):
        try:
            sortedPlayersBySkill = Counter(playerNameSkill).most_common()
            self.teamAcap = sortedPlayersBySkill[0][0]
            self.teamBcap = sortedPlayersBySkill[1][0]
            self.teamA.add(self.teamAcap)
            self.teamB.add(self.teamBcap)
            self.playerPool.discard(self.teamAcap)
            self.playerPool.discard(self.teamBcap)

            spads.sayBattle(f"Captains are {self.teamAcap} and {self.teamBcap}, based on TrueSkill")
        except Exception as e:
            spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

    def correctUsersStates(self):
        try:
            if (self.state == "disabled"):
                return

            users = lobbyInterface.battle["users"];
            for userName in users:
                self.correctUserState(userName)
        except Exception as e:
            spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)
    
    def correctUserState(self, userName):
        try:
            if (self.state == "disabled"):
                return

            battleStatus = lobbyInterface.battle["users"][userName]["battleStatus"]
            isSpec = battleStatus["mode"] == "0" # mode is string for some reason, even though it can only be 1 (player) or 0 (spec)
            allyId = battleStatus["team"]

            if userName in self.teamA and (allyId != 0 or isSpec):
                if isSpec:
                    lobbyInterface.battle["users"][userName]["battleStatus"]["mode"] = "1"
                    spads.queueLobbyCommand(["SAYBATTLE", f"$forceplay {userName}"]);

                lobbyInterface.battle["users"][userName]["battleStatus"]["team"] = 0
                spads.queueLobbyCommand(["FORCEALLYNO", userName, 0]);
            elif userName in self.teamB and (allyId != 1 or isSpec):
                if isSpec:
                    lobbyInterface.battle["users"][userName]["battleStatus"]["mode"] = "1"
                    spads.queueLobbyCommand(["SAYBATTLE", f"$forceplay {userName}"]);

                lobbyInterface.battle["users"][userName]["battleStatus"]["team"] = 1
                spads.queueLobbyCommand(["FORCEALLYNO", userName, 1]);
            elif not isSpec and userName not in self.teamA and userName not in self.teamB:
                lobbyInterface.battle["users"][userName]["battleStatus"]["mode"] = "0"
                spads.queueLobbyCommand(["FORCESPECTATORMODE", userName]);
        except Exception as e:
            spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

    def ready(self):
        spads.sayBattle("All players picked!")