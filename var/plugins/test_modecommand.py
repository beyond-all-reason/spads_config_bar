"""Unit tests for the parts of the ModeCommand plugin that do not need SPADS.

Run from this directory: python3 -m unittest test_modecommand
"""
import json
import os
import sys
import tempfile
import threading
import time
import types
import unittest

# The plugin imports SPADS's perl bridge at module scope; stand one in.
_calls = {'slog': [], 'answer': [], 'bSet': [], 'say': []}


class _FakeLobby:
    hosted = 'Beyond All Reason test-24450-abc1234'

    def getBattle(self):
        return {'battleId': '7'} if self.hosted else None

    def getBattles(self):
        return {'7': {'mod': self.hosted}} if self.hosted else {}


class _FakeSpads:
    lobby = _FakeLobby()

    def getSpadsConf(self):
        return {}

    def getLobbyInterface(self):
        return self.lobby

    def removeTimer(self, name):
        _calls.setdefault('timers_removed', []).append(name)

    def slog(self, message, level):
        _calls['slog'].append((message, level))

    def addSpadsCommandHandler(self, handlers):
        pass

    def removeSpadsCommandHandler(self, names):
        pass

    def fix_string(self, *args):
        return args if len(args) > 1 else args[0]

    def invalidSyntax(self, user, command):
        _calls['answer'].append('invalid syntax')

    def answer(self, message):
        _calls['answer'].append(message)

    def updateSetting(self, kind, key, value):
        _calls['bSet'].append((key, value))

    def sayBattleAndGame(self, message):
        _calls['say'].append(message)

    def get_flag(self, name):
        return True

    def addTimer(self, name, delay, interval, callback):
        _calls.setdefault('timers', []).append(name)

    # forkCall stand-in: run the child function now, hand the result to the
    # callback only when the test releases it, so "asynchronous" is observable.
    released = []

    def forkCall(self, fn, callback):
        result = fn()
        self.released.append(lambda: callback(result))
        return 4242


fake_perl = types.ModuleType('perl')
fake_perl.ModeCommand = _FakeSpads()
sys.modules['perl'] = fake_perl
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import modecommand  # noqa: E402


def _reset(data, pending=None):
    modecommand._state.update({'modName': 'Beyond All Reason test-24450-abc1234', 'data': data, 'pending': pending})
    for v in _calls.values():
        v.clear()


MODES = {
    'schemaVersion': 1,
    'categories': {
        'transfer': {
            'selector': 'transfer_mode',
            'presets': {
                'enabled': {
                    'modOptions': {
                        'ResourceMult': {'value': '1', 'locked': True},
                        'tax_rate': {'value': '0.1', 'locked': False},
                    }
                }
            },
        }
    },
}


class ModesShape(unittest.TestCase):
    def test_a_list_at_the_top_level_reads_as_no_modes(self):
        modecommand._state.update({'modName': None, 'data': {}, 'pending': None})
        modecommand._load_local = lambda: ['not', 'an', 'object']
        modecommand._start_fetch = lambda mod_name: None
        self.assertEqual({}, modecommand._modes())
        self.assertEqual({}, modecommand._as_dict(modecommand._modes().get('categories')))


class LockedKeys(unittest.TestCase):
    def test_a_lock_holds_whatever_the_casing(self):
        _reset(MODES)
        modecommand.hSpadsMode('pv', 'alice', ['transfer', 'enabled', 'resourcemult=9'], False)
        self.assertIn(('resourcemult', '1'), _calls['bSet'])
        self.assertNotIn(('resourcemult', '9'), _calls['bSet'])

    def test_an_unlocked_option_takes_the_override(self):
        _reset(MODES)
        modecommand.hSpadsMode('pv', 'alice', ['transfer', 'enabled', 'tax_rate=0.5'], False)
        self.assertIn(('tax_rate', '0.5'), _calls['bSet'])


class BackgroundFetch(unittest.TestCase):
    def test_the_first_lookup_serves_the_cache_and_the_callback_swaps_in_the_fetch(self):
        modecommand._state.update({'modName': None, 'data': {}, 'pending': None})
        fake_perl.ModeCommand.released.clear()
        modecommand._fetch = lambda mod_name: (MODES, [('fetched', 3)])
        modecommand._load_local = lambda: {'schemaVersion': 1, 'categories': {}}
        first = modecommand._modes()
        self.assertEqual({}, first['categories'])
        self.assertEqual(1, len(fake_perl.ModeCommand.released))
        fake_perl.ModeCommand.released.pop()()
        self.assertEqual(MODES['categories'], modecommand._modes()['categories'])
        self.assertIn(('fetched', 3), _calls['slog'])

    def test_nothing_is_fetched_before_spads_knows_the_hosted_version(self):
        modecommand._state.update({'modName': None, 'data': {}, 'pending': None})
        fake_perl.ModeCommand.released.clear()
        fake_perl.ModeCommand.lobby.hosted = None
        try:
            self.assertEqual({}, modecommand._modes())
            self.assertEqual(0, len(fake_perl.ModeCommand.released))
        finally:
            fake_perl.ModeCommand.lobby.hosted = _FakeLobby.hosted


if __name__ == '__main__':
    unittest.main()
