import urllib.request
import json
import perl
spads = perl.RatingManager

pluginVersion = '0.1'
requiredSpadsVersion = '0.12.29'

host_url = "https://server2.beyondallreason.info/teiserver/api/spads/get_rating"

def getVersion(pluginObject):
    return pluginVersion

def getRequiredSpadsVersion(pluginName):
    return requiredSpadsVersion

class RatingManager:
    def __init__(self, context):
        spads.slog("MyPlugin plugin loaded (version %s)" % pluginVersion, 3)

    def updatePlayerSkill(self, playerSkill, accountId, modName, gameType):
      with urllib.request.urlopen(f"{host_url}/{accountId}/{accountId}/{gameType}") as f:
        raw_data = f.read().decode('utf-8')
        data = json.loads(raw_data)
        rating = data["rating"]

      return [1, rating]
