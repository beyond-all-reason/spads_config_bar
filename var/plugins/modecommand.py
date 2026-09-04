import perl
import re
import os
import json
import threading
import urllib.request

spads = perl.ModeCommand

pluginVersion = '0.2'
requiredSpadsVersion = '0.12.29'


# !mode applies one of the game's mode presets: modes.json, baked by BAR CI from
# the game's modes/*.lua and published as a release asset (modes-<sha>.json for
# the hosted commit, else modes-<channel>.json). Fetched in the background, cached,
# with a host-dropped file as the last resort.
# Local testing: MODECOMMAND_RELEASE_BASE, MODECOMMAND_MODES_VERSION (asset key),
# MODECOMMAND_MODES_CHANNEL=test|stable.

_PLUGIN_DIR = os.path.dirname(os.path.abspath(__file__))

_DEFAULT_RELEASE_BASE = 'https://github.com/beyond-all-reason/Beyond-All-Reason/releases/download/modes'
_CACHE_PATH = os.path.join(_PLUGIN_DIR, 'modes.cache.json')
_LOCAL_PATHS = [
    os.path.join(_PLUGIN_DIR, 'modes.json'),
    '/opt/spads/var/plugins/modes.json',
]
_FETCH_TIMEOUT = 5
_SCHEMA_VERSION = 1

# Modes for the hosted version (modName); a rehost to another version refetches.
_UNSET = object()
_state = {'modName': _UNSET, 'data': {}, 'pending': None}


def _conf():
    try:
        return spads.getSpadsConf()
    except Exception:
        return {}


def _current_mod_name():
    try:
        return _conf().get('modName')
    except Exception:
        return None


def _release_base():
    return (os.environ.get('MODECOMMAND_RELEASE_BASE') or _DEFAULT_RELEASE_BASE).rstrip('/')


def _channel(mod_name):
    override = (os.environ.get('MODECOMMAND_MODES_CHANNEL') or 'auto').lower()
    if override in ('test', 'stable'):
        return override
    return 'test' if (mod_name and 'test' in mod_name.lower()) else 'stable'


def _commit_sha(mod_name):
    # Trailing git short SHA of the hosted version ("...test-24450-6c81e38" -> "6c81e38").
    override = os.environ.get('MODECOMMAND_MODES_VERSION')
    if override:
        return override.strip() or None
    if not mod_name:
        return None
    m = re.search(r'-([0-9a-f]{7,40})\s*$', mod_name)
    return m.group(1) if m else None


def _fetch(mod_name):
    # Worker thread: no spads.* calls here; log lines return as (message, level).
    base = _release_base()
    urls = []
    sha = _commit_sha(mod_name)
    if sha:
        urls.append(('%s/modes-%s.json' % (base, sha), True))
    urls.append(('%s/modes-%s.json' % (base, _channel(mod_name)), False))

    log = []
    for (url, pinned) in urls:
        try:
            with urllib.request.urlopen(url, timeout=_FETCH_TIMEOUT) as resp:
                body = resp.read()
            data = json.loads(body)
            if not pinned and sha:
                log.append(('mode: no modes asset pinned to commit %s; serving the rolling %s asset, '
                            'which may not match the hosted version' % (sha, _channel(mod_name)), 2))
            schema = data.get('schemaVersion') if isinstance(data, dict) else None
            if schema != _SCHEMA_VERSION:
                log.append(('mode: %s has schemaVersion %r, this plugin reads %r; modes may not apply correctly'
                            % (url, schema, _SCHEMA_VERSION), 1))
            try:
                with open(_CACHE_PATH, 'wb') as f:
                    f.write(body)
            except OSError:
                pass
            return data, log
        except Exception as e:
            log.append(('mode: could not fetch %s: %s' % (url, e), 2))
    return None, log


def _load_local():
    for path in [_CACHE_PATH] + _LOCAL_PATHS:
        try:
            with open(path) as f:
                return json.load(f)
        except Exception:
            continue
    return None


def _start_fetch(mod_name):
    pending = {'modName': mod_name, 'done': False, 'data': None, 'log': []}

    def run():
        try:
            pending['data'], pending['log'] = _fetch(mod_name)
        except Exception as e:
            pending['data'], pending['log'] = None, [('mode: fetch failed: %s' % e, 2)]
        pending['done'] = True

    _state['pending'] = pending
    threading.Thread(target=run, name='ModeCommand-fetch', daemon=True).start()
    return pending


def _collect_fetch():
    pending = _state['pending']
    if not pending or not pending['done']:
        return
    _state['pending'] = None
    for (message, level) in pending['log']:
        spads.slog(message, level)
    if pending['data'] is not None and pending['modName'] == _state['modName']:
        _state['data'] = _as_dict(pending['data'])
        spads.slog('mode: modes for "%s" loaded' % pending['modName'], 3)


def _modes():
    # Never blocks: serves the cache while the fetch runs, then the fetched data.
    _collect_fetch()
    mod_name = _current_mod_name()
    if mod_name != _state['modName']:
        _state['modName'] = mod_name
        local = _load_local()
        _state['data'] = _as_dict(local)
        if local is None:
            spads.slog('mode: no cached modes for "%s"; !mode has nothing to apply until the fetch lands' % mod_name, 2)
        else:
            spads.slog('mode: serving cached modes for "%s" while the current ones are fetched' % mod_name, 3)
        _start_fetch(mod_name)
    return _state['data']


def _as_dict(v):
    # Lua's Json.encode writes an empty table as [], so never trust the shape.
    return v if isinstance(v, dict) else {}

globalPluginParams = {
    'commandsFile': ['notNull'],
    'helpFile': ['notNull'],
}
presetPluginParams = None


def getVersion(pluginObject):
    return pluginVersion

def getRequiredSpadsVersion(pluginName):
    return requiredSpadsVersion

def getParams(pluginName):
    return [globalPluginParams, presetPluginParams]


class ModeCommand:

    def __init__(self, context):
        spads.addSpadsCommandHandler({'mode': hSpadsMode})
        spads.slog("Plugin loaded (version %s)" % pluginVersion, 3)
        _modes()

    def onUnload(self, reason):
        spads.removeSpadsCommandHandler(['mode'])
        spads.slog("Plugin unloaded", 3)


def hSpadsMode(source, user, params, checkOnly):
    (source, user) = spads.fix_string(source, user)
    for i in range(len(params)):
        params[i] = spads.fix_string(params[i])

    if len(params) < 2:
        spads.invalidSyntax(user, 'mode')
        return 0

    category = params[0]
    mode_key = params[1]
    kv_params = params[2:]

    category_data = _as_dict(_modes().get('categories')).get(category)
    if not category_data:
        spads.answer('Unknown mode category "%s"' % category)
        return 0
    presets = _as_dict(category_data.get('presets'))
    preset = presets.get(mode_key)
    if not preset:
        valid = ', '.join(sorted(presets)) or '(none)'
        spads.answer('Unknown mode "%s" for category "%s" (valid: %s)' % (mode_key, category, valid))
        return 0

    mod_options = _as_dict(preset.get('modOptions'))

    settings = []
    for param in kv_params:
        m = re.match(r'^([^=]+)=(.*)$', param)
        if not m:
            spads.answer('Invalid parameter format "%s" (expected key=value)' % param)
            return 0
        settings.append((m.group(1).lower(), m.group(2)))

    locked_keys = set(
        key.lower() for key, spec in mod_options.items()
        if isinstance(spec, dict) and spec.get('locked')
    )

    # Unknown keys are refused in the check phase, so a typo never reaches a vote.
    valid_keys = set(k.lower() for k in mod_options)
    for (key, _val) in settings:
        if key not in valid_keys:
            spads.answer('Unknown option "%s" for mode "%s %s" (valid: %s)'
                         % (key, category, mode_key, ', '.join(sorted(valid_keys)) or '(none)'))
            return 0

    if checkOnly:
        return 1

    selector_key = category_data.get('selector') or ('%s_mode' % category)
    spads.updateSetting('bSet', selector_key, mode_key)

    # The full preset, then overrides; locked options keep the preset's value.
    effective = {}
    for (key, spec) in mod_options.items():
        if isinstance(spec, dict) and 'value' in spec:
            effective[key.lower()] = spec['value']
    for (key, val) in settings:
        if key not in locked_keys:
            effective[key] = val

    change_descs = ['%s=%s' % (selector_key, mode_key)]
    for key in sorted(effective):
        spads.updateSetting('bSet', str(key), str(effective[key]))
        change_descs.append('%s=%s' % (key, effective[key]))

    changes_str = ', '.join(change_descs)
    mode_label = '%s %s' % (category, mode_key)
    if changes_str:
        spads.sayBattleAndGame('Mode "%s" applied by %s (%s)' % (mode_label, user, changes_str))
    else:
        spads.sayBattleAndGame('Mode "%s" applied by %s' % (mode_label, user))
    if source == 'pv':
        if changes_str:
            spads.answer('Mode "%s" applied (%s)' % (mode_label, changes_str))
        else:
            spads.answer('Mode "%s" applied' % mode_label)

    return 1
