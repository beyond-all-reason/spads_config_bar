import urllib.request
import json
import perl
import traceback
spads = perl.RatingManager

pluginVersion = '0.2'
requiredSpadsVersion = '0.12.29'

host_url = "https://server2.beyondallreason.info/teiserver/api/spads/get_rating"

def getVersion(pluginObject):
    return pluginVersion

def getRequiredSpadsVersion(pluginName):
    return requiredSpadsVersion

class RatingManager:
    def __init__(self, context):
        spads.slog("RatingManager plugin loaded (version %s)" % pluginVersion, 3)

    def updatePlayerSkill(self, playerSkill, accountId, modName, gameType):
        try:
            with urllib.request.urlopen(f"{host_url}/{accountId}/{gameType}") as f:
                raw_data = f.read().decode('utf-8')
                data = json.loads(raw_data)

                return [1, data["rating_value"], data["uncertainty"]]
        except Exception as e:
            spads.slog("Unhandled exception: " + str(sys.exc_info()
                       [0]) + "\n" + str(traceback.format_exc()), 0)
            return [1, 16.66, 8.33]
