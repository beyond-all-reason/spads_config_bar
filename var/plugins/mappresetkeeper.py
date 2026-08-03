# MapPresetKeeper
#
# SPADS core only applies the map preset (the preset named "<map name>.smf", which carries the
# map specific metadata as modoptions) when the map changes. It is not re-applied when another
# preset is loaded, so loading a global preset which resets the battle settings (resetoptions)
# silently drops all the map specific modoptions.
#
# This plugin re-applies the map preset every time another preset is applied, so the map metadata
# modoptions are always present and consistent with the current map. The same happens when a battle
# preset is applied with the "!bPreset" command, which has the same effect but no dedicated
# callback in the plugin API.
#
# It's based on the implementation suggested by Yaribz in https://github.com/Yaribz/SPADS/issues/94.

import perl

spads = perl.MapPresetKeeper

pluginVersion = '0.1'
requiredSpadsVersion = '0.13.50'


def getVersion(pluginObject):
    return pluginVersion


def getRequiredSpadsVersion(pluginName):
    return requiredSpadsVersion


class MapPresetKeeper:

    def __init__(self, context):
        spads.slog("Plugin loaded (version %s)" % pluginVersion, 3)

    def onPresetApplied(self, oldPreset, newPreset):
        newPreset = spads.fix_string(newPreset)

        # skip processing if the preset being applied is already a map preset (avoid looping)
        if newPreset.endswith('.smf'):
            return

        self.reapplyMapPreset()

    def postSpadsCommand(self, command, source, user, params, commandResult):
        # SPADS has no callback for the application of a battle preset, so the "!bPreset" command
        # is watched instead: applying a battle preset with "resetoptions" enabled drops the map
        # metadata modoptions, exactly like applying a global preset does
        # (SPADS lower-cases the command name, and considers it failed only if the result is 0)
        if command == 'bpreset' and commandResult != 0:
            self.reapplyMapPreset()

    def reapplyMapPreset(self):
        # skip processing if the map preset functionality is disabled
        spadsConf = spads.getSpadsConf()
        if spadsConf['autoLoadMapPreset'] == '0':
            return

        # build map preset name by appending ".smf" to current map name if needed
        # (old engine versions used to include the "smf" extension in the map name)
        currentMap = spads.fix_string(spadsConf['map'])
        mapPresetName = currentMap if currentMap.endswith('.smf') else currentMap + '.smf'

        # auto-load the map preset if found, or the default map preset if it exists
        spadsPresets = spads.getSpadsConfFull().presets
        if mapPresetName in spadsPresets:
            spads.applyPreset(mapPresetName)
        elif '_DEFAULT_.smf' in spadsPresets:
            spads.applyPreset('_DEFAULT_.smf')
