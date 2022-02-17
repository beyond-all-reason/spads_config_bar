# Captains Draft Plugin
# This plugin provides a mode to pick teams whereby assigned captains take turns drafting players

# Author: Jazcash

# Usage: !preset draft
# AllyTeam 3 represents the list of 'added' players. When the draft preset is enabled, all current players get added and moved to AllyTeam 3
# Players can 'unadd' at any time by simply becoming a spectator
# !draft must be called to begin the drafting phase. An even number of players is required to begin drafting with at least 6 players minimum
# The two highest TS players are then automatically made captains of each team
# The lowest TS of the two captains gets first pick. Players are picked with !pick [username]
# Players are picked one after another, until all players are picked
# Players must !cv start as normal
# Once game has finished, plugin reverts to adding state

import perl
import sys
import traceback
from collections import Counter
from datetime import datetime

spads=perl.CaptainsDraftPlugin
pluginVersion="0.4"
requiredSpadsVersion="0.12.29"
globalPluginParams = {
    "commandsFile": ["notNull"],
    "helpFile": ["notNull"]
}
presetPluginParams = None
minimumPlayers = 6

accountIdSkill = {}
playerNameSkill = {}

debug = False

def getVersion(pluginObject):
    return pluginVersion

def getRequiredSpadsVersion(pluginName):
    return requiredSpadsVersion

def getParams(pluginName):
    return [globalPluginParams, presetPluginParams]

class CaptainsDraftPlugin:
    def __init__(self, context):
        try:
            lobbyInterface = spads.getLobbyInterface()
            spads.addSpadsCommandHandler({
                "draft": self.draft,
                "pick": self.pick
            })

            if (spads.getLobbyState() > 3):
                self.onLobbyConnected(lobbyInterface)

            spads.slog("Plugin loaded (version %s)" % pluginVersion, 3)
        except Exception as e:
            spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

    def onLobbyConnected(self, _lobbyInterface):
        try:
            spads.addLobbyCommandHandler({"CLIENTBATTLESTATUS": self.clientBattleStatusChange})
            self.reset()
        except Exception as e:
            spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

    def onUnload(self, reason):
        try:
            spads.removeLobbyCommandHandler(["CLIENTBATTLESTATUS"])
            spads.removeSpadsCommandHandler(["draft", "pick"])

            spads.slog("Plugin unloaded", 3)
        except Exception as e:
            spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

    def reset(self):
        try:
            self.state = "disabled" # disabled, adding, drafting, ready
            self.addedPlayers = set()
            self.playerPool = set()
            self.teamApicking = False
            self.teamAcap = ""
            self.teamBcap = ""
            self.teamA = {}
            self.teamB = {}
        except Exception as e:
            spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

    def onBattleClosed(self):
        try:
            self.reset()
        except Exception as e:
            spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

    def onBattleOpened(self):
        try:
            currentSpadsConf = spads.getSpadsConf()
            if (currentSpadsConf["preset"] == "draft"):
                self.state = "adding"
        except Exception as e:
            spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

    def onSpringStop(self, _pid):
        try:
            if (self.state != "disabled"):
                spads.sayBattle(f"Game ended, returning to adding state")
                self.resetToAddingState()
        except Exception as e:
            spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

    def onPresetApplied(self, oldPresetName, newPresetName):
        try:
            if (newPresetName == "draft"):
                self.disable()
                self.enable()
            else:
                self.disable()
        except Exception as e:
            spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

    def onLeftBattle(self, userName):
        try:
            if (userName not in self.addedPlayers):
                return

            self.addedPlayers.discard(userName)

            if self.state == "drafting" or self.state == "ready":
                spads.sayBattle(f"{userName} left, returning to adding state")
                self.resetToAddingState()
        except Exception as e:
            spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

    def enable(self):
        try:
            self.state = "adding"
            spads.sayBattle("Captains Draft enabled, call !draft to begin picking")

            lobbyInterface = spads.getLobbyInterface()
            users = lobbyInterface.getBattle()["users"]
            for userName in users:
                userStatus = users[userName]["battleStatus"]
                if (userStatus is not None and userStatus["mode"] == "1"):
                    self.addedPlayers.add(userName)

            self.fixPlayerStatuses()
        except Exception as e:
            spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

    def disable(self):
        try:
            self.reset()
        except Exception as e:
            spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

    def resetToAddingState(self):
        try:
            self.state = "adding"
            self.teamA = {}
            self.teamB = {}
            self.teamAcap = ""
            self.teamBcap = ""
            self.addedPlayers = set()
            self.playerPool.clear()
            self.fixPlayerStatuses()
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

            if (len(self.addedPlayers) < minimumPlayers):
                spads.sayBattle(f"Can't start draft with less than ${minimumPlayers} added players ({len(self.addedPlayers)} added)")
                return 0

            if (len(params) != 0):
                if (len(params) == 2):
                    lobbyInterface = spads.getLobbyInterface()
                    usersInBattle = list(lobbyInterface.getBattle()["users"])

                    teamAcapmatches = perl.cleverSearch(params[0], usersInBattle)
                    if len(teamAcapmatches == 0):
                        spads.sayBattle(f"Player {params[0]} not found")
                        return 0

                    teamBcapmatches = perl.cleverSearch(params[1], usersInBattle)
                    if len(teamBcapmatches == 0):
                        spads.sayBattle(f"Player {params[1]} not found")
                        return 0

                else:
                    spads.sayBattle(f"Must be called with no arguments (e.g. !draft) or with 2 captains (e.g. !draft player1 player2)")
                    return 0

            if (checkOnly):
                return 1

            self.state = "drafting"
            self.playerPool = self.addedPlayers.copy()
            self.updateSkills()
            if (len(params) == 0):
                self.assignCaptainsBySkill()
            else:
                self.assignCaptains(teamAcapmatches[0], teamBcapmatches[0])
        except Exception as e:
            spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

    def pick(self, source, user, params, checkOnly):
        try:
            if (self.state != "drafting"):
                spads.answer(f"Cannot pick player while Captains Draft is in the {self.state} state")
                return 0

            if len(params) != 1:
                spads.sayBattle(f"You must pick a single player, e.g. !pick bob")
                return 0

            lobbyInterface = spads.getLobbyInterface()
            usersInBattle = list(lobbyInterface.getBattle()["users"])
            matchingUsers = perl.cleverSearch(params[0], usersInBattle)

            if (len(matchingUsers) == 0):
                spads.sayBattle(f"Player {params[0]} not found")
                return 0

            pickedPlayer = matchingUsers[0]
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
                self.teamA[pickedPlayer] = None
            else:
                self.teamB[pickedPlayer] = None

            self.teamApicking = not self.teamApicking

            if (len(self.playerPool) > 1):
                spads.sayBattle(f"{cap} picked {pickedPlayer}. It is {otherCap}'s turn to !pick")
            else:
                lastUnpickedPlayer = self.playerPool.pop()
                spads.sayBattle(f"{lastUnpickedPlayer} is last pick so goes to {otherCap}\'s team")

                if self.teamApicking:
                    self.teamA[lastUnpickedPlayer] = None
                else:
                    self.teamB[lastUnpickedPlayer] = None

                self.ready()
                self.fixPlayerStatuses()
                self.fixPlayerIds()

                return

            self.fixPlayerStatuses()
        except Exception as e:
            spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

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

    def assignCaptains(self, teamAcap, teamBcap):
        try:
            self.teamAcap = teamAcap
            self.teamBcap = teamBcap
            self.teamA[self.teamAcap] = None
            self.teamB[self.teamBcap] = None
            self.playerPool.discard(self.teamAcap)
            self.playerPool.discard(self.teamBcap)
            self.teamApicking = False

            self.fixPlayerStatuses()

            spads.sayBattle(f"Captains are {self.teamAcap} and {self.teamBcap}, based on TrueSkill. {self.teamBcap} gets first !pick")
        except Exception as e:
            spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

    def assignCaptainsBySkill(self):
        try:
            playerPoolList = list(self.playerPool)
            playerPoolList.sort(key=lambda x: playerNameSkill[x], reverse=True)

            self.assignCaptains(playerPoolList[0], playerPoolList[1])
        except Exception as e:
            spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

    def clientBattleStatusChange(self, command, userName, rawBattleStatus, teamColor):
        try:
            lobbyInterface = spads.getLobbyInterface()
            battleStatus = lobbyInterface.unmarshallBattleStatus(rawBattleStatus)
            status = self.getUserBattleStatus(userName, battleStatus)

            if debug:
                spads.slog("battlestatuschanged " + userName + " :" + str(battleStatus), 3)

            self.fixPlayerStatus(userName, status)
        except Exception as e:
            spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

    def fixPlayerStatuses(self):
        try:
            if (self.state == "disabled"):
                return

            lobbyInterface = spads.getLobbyInterface()
            battle = lobbyInterface.getBattle()
            users = battle["users"]

            for userName in users:
                self.fixPlayerStatus(userName)

        except Exception as e:
            spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

    def fixPlayerStatus(self, userName, status=None):
        try:
            if (self.state == "disabled"):
                return

            if status is None:
                status = self.getUserBattleStatus(userName)

            if status is None:
                return

            if (self.state == "adding"):
                if (status["isSpec"] and status["isAdded"]):
                    self.addedPlayers.discard(userName)
                elif (not status["isSpec"]):
                    self.addedPlayers.add(userName)
                    if (status["allyTeamId"] != 2):

                        if debug:
                            spads.slog("Changing " + userName + " team from " + str(status["allyTeamId"]) + " to 2", 0)

                        self.forceAllyTeam(userName, 2)
            elif (self.state == "drafting" or self.state == "ready"):
                if (status["isSpec"] and status["isAdded"]):
                    spads.sayBattle(f"{userName} specced, returning to adding state")
                    self.resetToAddingState()
                elif (not status["isSpec"] and not status["isAdded"]):
                    spads.sayBattle(f"{userName}, you must wait for the next draft")

                    if debug:
                        spads.slog("Forcespec " + userName, 0)

                    self.forceSpec(userName)
                elif (status["isAdded"] and status["isTeamA"] and status["allyTeamId"] != 0):
                    if debug:
                        spads.slog("Forceallyteam 1 " + userName, 0)
                    self.forceAllyTeam(userName, 0)
                elif (status["isAdded"] and status["isTeamB"] and status["allyTeamId"] != 1):
                    if debug:
                        spads.slog("Forceallyteam 2 " + userName, 0)
                    self.forceAllyTeam(userName, 1)
                elif (status["isAdded"] and (not status["isTeamA"]) and (not status["isTeamB"]) and status["allyTeamId"] != 2):
                    if debug:
                        spads.slog("Forceallyteam 3 " + userName, 0)
                    self.forceAllyTeam(userName, 2)

        except Exception as e:
            spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

    def fixTeamIds(self, team, users, initialIdx=1):
        for idx, userName in enumerate(team, start=initialIdx):
            if debug:
                spads.slog("fixid for " + userName + " idx= " + str(idx), 3)
            status = users[userName]["battleStatus"]

            if status is not None and status["id"] != idx:

                if debug:
                    spads.slog("fixplayerid " + userName + " from " + str(status["id"]) + " -> " + str(idx), 3)

                spads.queueLobbyCommand(["FORCETEAMNO", userName, idx])


    def fixPlayerIds(self):
        if self.state != "ready":
            if debug:
                spads.slog("Fixplayerids called and not ready!", 3)
            return

        spads.slog("Fixplayerids called!")

        lobbyInterface = spads.getLobbyInterface()
        battle = lobbyInterface.getBattle()
        users = battle["users"]
        founder = battle["founder"]
        founderId = int(users[founder]["battleStatus"]["id"])

        if founderId != 0:

            if debug:
                spads.slog("fixfounderid from " + str(founderId), 3)

            spads.queueLobbyCommand(["FORCETEAMNO", founder, 0])

        self.fixTeamIds(self.teamA, users)
        self.fixTeamIds(self.teamB, users, len(self.teamA) + 1)

    def forceSpec(self, userName):
        try:
            spads.queueLobbyCommand(["FORCESPECTATORMODE", userName]);
        except Exception as e:
            spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

    def forceAllyTeam(self, userName, allyTeamId):
        try:
            spads.queueLobbyCommand(["FORCEALLYNO", userName, allyTeamId]);
        except Exception as e:
            spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)

    def ready(self):
        self.state = "ready"
        spads.sayBattle("All players picked!")

    def getUserBattleStatus(self, userName, battleStatus=None):
        try:
            if battleStatus is None:
                lobbyInterface = spads.getLobbyInterface()
                battleStatus = lobbyInterface.getBattle()["users"][userName]["battleStatus"]

            if battleStatus is None:
                return

            return {
                "isAdded": userName in self.addedPlayers,
                "isTeamA": userName in self.teamA,
                "isTeamB": userName in self.teamB,
                "isSpec": int(battleStatus["mode"]) == 0,
                "allyTeamId": int(battleStatus["team"])
            }
        except Exception as e:
            spads.slog("Unhandled exception: " + str(sys.exc_info()[0]) + "\n" + str(traceback.format_exc()), 0)
