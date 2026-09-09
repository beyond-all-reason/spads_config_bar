# GameVersion
#
# BAR autohosts are pinned to one game version by the modName value of their hosting preset, and
# "!hSet modName" only accepts the values listed there. This plugin adds "!gameVersion <rapidTag>",
# which downloads the requested build with pr-downloader (under the SPADS unitsync lock, like the
# periodic pr-downloader service does), points modName at "rapid://<tag>", tags the battle title,
# marks the games unranked and rehosts. "!gameVersion" with no argument applies the default preset
# again, which is also what SPADS does by itself once the battle has been empty for
# restoreDefaultPresetDelay seconds.

import fcntl
import os
import re
import subprocess
import time
import traceback

import perl

spads = perl.GameVersion

pluginVersion = '0.1'
# first release whose rapid:// resolver accepts a wider range of characters in name.
requiredSpadsVersion = '0.13.52'

globalPluginParams = {
    'commandsFile': ['notNull'],
    'helpFile': ['notNull'],
    'allowedRapidTags': ['notNull'],
    'prDownloaderPath': ['absoluteExecutableFile'],
    'prDownloaderWritePath': ['notNull'],
    'prDownloaderEnv': [],
    'timeout': ['integer'],
}
presetPluginParams = None

# spads.pl constant: reload the game archives without rescanning the maps
LOADARCHIVES_GAME_ONLY = 2


def getVersion(pluginObject):
    return pluginVersion


def getRequiredSpadsVersion(pluginName):
    return requiredSpadsVersion


def getParams(pluginName):
    return [globalPluginParams, presetPluginParams]


def guarded(method):
    """Log and swallow exceptions of methods called from Perl. Also reset "busy", otherwise an
    exception raised in the middle of a switch would leave it set forever and every later
    "!gameVersion" would be refused with "already in progress"."""
    def wrapper(self, *args):
        try:
            return method(self, *args)
        except Exception:
            spads.slog('Unhandled exception in %s: %s' % (method.__name__, traceback.format_exc()), 0)
            self.busy = False
            return 0
    return wrapper


# Exit codes of pr-downloader, see DownloadStart() in https://github.com/beyond-all-reason/pr-downloader/blob/master/src/pr-downloader.cpp
PR_DOWNLOADER_ERRORS = {
    1: 'no such game version',
    2: 'download incomplete',
    5: 'not enough free disk space',
    6: 'failed to download dependencies',
}


def downloadRapidTags(prd, dataDir, tags, env, timeout, lockFile):
    """Runs in a forked process. Returns an error message, or '' when all tags were downloaded."""
    deadline = time.time() + timeout
    try:
        with open(lockFile, 'w') as lockFh:
            # The lock is taken by SPADS archive reloads, by SPADS instances while their engine
            # starts up, and by the periodic pr-downloader service. Poll instead of blocking so
            # that the timeout also covers the wait.
            while True:
                try:
                    fcntl.flock(lockFh, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except OSError:
                    if time.time() >= deadline:
                        return 'timeout while waiting for exclusive access to the archives cache'
                    time.sleep(1)
            # One run per tag: given several tags at once, pr-downloader exits 0 even if some of
            # them could not be resolved, as long as at least one was downloaded, see
            # https://github.com/beyond-all-reason/pr-downloader/issues/73
            for tag in tags:
                rc = subprocess.run(
                    [prd, '--disable-logging', '--filesystem-writepath', dataDir, '--download-game', tag],
                    env=env, timeout=max(1, deadline - time.time()),
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL).returncode
                if rc != 0:
                    return 'download of "%s" failed: %s' % (
                        tag, PR_DOWNLOADER_ERRORS.get(rc, 'pr-downloader exit code %d' % rc))
    except subprocess.TimeoutExpired:
        return 'pr-downloader timed out'
    except Exception as e:
        return str(e)
    return ''


class GameVersion:

    def __init__(self, context):
        # A switch or restore is in progress (download and/or archive reload)
        self.busy = False
        spads.addSpadsCommandHandler({'gameVersion': self.hGameVersion})
        spads.slog('Plugin loaded (version %s)' % pluginVersion, 3)

    def onUnload(self, reason):
        spads.removeSpadsCommandHandler(['gameVersion'])
        spads.slog('Plugin unloaded', 3)

    def hostingDefaults(self):
        """(modName, battleName) of the current hosting preset."""
        preset = spads.getSpadsConfFull().hPresets[spads.getSpadsConf()['hostingPreset']]
        return preset['modName'][0], preset['battleName'][0]

    def currentTag(self):
        """Rapid tag the room is switched to, or None when it is on the hosting preset default."""
        modName = spads.getSpadsConfFull().hSettings['modName']
        if modName == self.hostingDefaults()[0] or not modName.startswith('rapid://'):
            return None
        return modName[len('rapid://'):]

    @guarded
    def hGameVersion(self, source, user, params, checkOnly):
        user = spads.fix_string(user)
        params = [spads.fix_string(p) for p in params]
        if len(params) > 1:
            spads.invalidSyntax(user, 'gameversion')
            return 0
        if self.busy:
            spads.answer('A game version change is already in progress, please wait.')
            return 0

        tag = params[0] if params else None
        if tag is not None:
            allowedRapidTags = spads.getPluginConf()['allowedRapidTags']
            if re.match(allowedRapidTags, tag) is None:
                spads.answer('"%s" is not allowed here, the game version must match %s'
                             % (tag, allowedRapidTags))
                return 0
            if 'rapid://' + tag == self.hostingDefaults()[0]:
                tag = None
        if tag is None and self.currentTag() is None:
            spads.answer('The room is already using the default game version.')
            return 0
        if checkOnly:
            return 1

        self.busy = True
        if tag is None:
            spads.answer('Restoring the default game version, the battle will be rehosted...')
            spads.applyPreset(spads.getSpadsConf()['defaultPreset'])
            self.rehostWhenReady(None, user)
        else:
            self.download(tag, user)
        return 1

    def download(self, tag, user):
        conf = spads.getPluginConf()
        spadsConf = spads.getSpadsConf()
        env = dict(os.environ)
        for entry in conf['prDownloaderEnv'].split(';'):
            if '=' in entry:
                name, value = entry.split('=', 1)
                env[name] = value
        # Same lock file as loadArchivesBlocking() and sequentialSpadsUnitsyncProcess.pl
        lockDir = spadsConf['varDir'] if int(spadsConf['sequentialUnitsync']) else spadsConf['instanceDir']
        # Every pr-downloader run refreshes the shared rapid index (versions.gz), and SPADS
        # resolves a rapid:// default through that index. If the index moved on to a build that
        # is not downloaded yet, the default game could not be hosted anymore (new instances
        # would not even open a battle) until the periodic pr-downloader service catches up. So
        # always fetch the default tag as well.
        tags = [tag]
        defaultModName = self.hostingDefaults()[0]
        if defaultModName.startswith('rapid://'):
            tags.append(defaultModName[len('rapid://'):])
        args = (conf['prDownloaderPath'], conf['prDownloaderWritePath'], tags, env,
                int(conf['timeout']), os.path.join(lockDir, 'unitsync.lock'))

        # forkCall() needs plain functions: Inline::Python does not turn functools.partial objects
        # into Perl code references
        def run():
            return downloadRapidTags(*args)

        def done(error=None):
            self.onDownloaded(tag, user, error)

        spads.answer('Downloading game version "%s", this can take a while...' % tag)
        spads.slog('Downloading game version "%s" requested by %s' % (tag, user), 3)
        if not spads.forkCall(run, done):
            self.busy = False
            spads.answer('Unable to change game version: failed to fork the download process.')

    @guarded
    def onDownloaded(self, tag, user, error):
        if error != '':
            self.busy = False
            error = error or 'the download process died'
            spads.sayBattleAndGame('Unable to switch game version: %s' % error)
            spads.slog('Failed to switch to game version "%s": %s' % (tag, error), 2)
            return
        spads.updateSetting('hSet', 'modName', 'rapid://' + tag)
        spads.updateSetting('hSet', 'battleName', '[%s] %s' % (tag, self.hostingDefaults()[1]))
        # Teiserver rates matches whatever build they were played on
        spads.updateSetting('bSet', 'ranked_game', '0')
        self.rehostWhenReady(tag, user)

    def rehostWhenReady(self, tag, user):
        """Reload the game archives, then rehost if the new modName can be hosted.

        The reload forces a fresh resolution of the tag, which core otherwise caches until the
        next reload, so that a re-download of the same tag is picked up.
        """
        def done(*_):
            self.onArchivesReloaded(tag, user)
        spads.loadArchives(done, 0, LOADARCHIVES_GAME_ONLY)

    @guarded
    def onArchivesReloaded(self, tag, user):
        self.busy = False
        what = 'the default game version' if tag is None else tag
        # $targetMod is unreachable from Python; re-running updateTargetMod() recomputes it and
        # returns 1 when it resolved to a loadable archive
        if int(perl.updateTargetMod() or 0) == 1:
            if tag is None:
                spads.sayBattleAndGame('Restoring the default game version, the battle is being '
                                       'rehosted, please rejoin.')
                action = 'default game version restored'
            else:
                spads.sayBattleAndGame('Switching to %s, games here will not be rated. '
                                       'The battle is being rehosted, please rejoin.' % tag)
                action = 'game version set to %s' % tag
            spads.rehost('%s by %s' % (action, user))
            spads.slog('%s by %s' % (action.capitalize(), user), 3)
            return
        # The download succeeded but SPADS cannot map the new modName to a loaded archive. If we
        # rehosted now, SPADS would close the battle and not open a new one until an archive
        # matching modName shows up. Instead, go back to the default settings and keep the
        # current battle open, exactly like the empty-room auto-restore does.
        spads.applyPreset(spads.getSpadsConf()['defaultPreset'])
        spads.sayBattleAndGame('Unable to switch to %s: no matching game archive found, default '
                               'settings restored.' % what)
        spads.slog('No game archive found for %s, default preset applied' % what, 2)
