"""Diagnostics-only recorder for the arena's ordinary public observations."""
from collections import deque
import json
from pathlib import Path

from nle import nethack
from nethackers.arena import run, trajectory

FIELDS = {
    'x': nethack.NLE_BL_X, 'y': nethack.NLE_BL_Y,
    'hp': nethack.NLE_BL_HP, 'max_hp': nethack.NLE_BL_HPMAX,
    'energy': nethack.NLE_BL_ENE, 'xp_level': nethack.NLE_BL_XP,
    'dungeon': nethack.NLE_BL_DNUM, 'level': nethack.NLE_BL_DLEVEL,
    'turn': nethack.NLE_BL_TIME, 'hunger': nethack.NLE_BL_HUNGER,
    'condition': nethack.NLE_BL_CONDITION,
}
ACTIONS = tuple(nethack.ACTIONS)
DIRECTIONS = frozenset({'N', 'NE', 'E', 'SE', 'S', 'SW', 'W', 'NW'})
OUTPUT = Path('/out/diagnostics/arena-observations.json')
make_environment = trajectory.make_environment


class RecordedEnvironment:
    def __init__(self, inner):
        self.inner = inner
        self.initial = None
        self.tail = deque(maxlen=256)
        self.injuries = deque(maxlen=64)
        self.bursts = deque(maxlen=12)
        self.critical = deque(maxlen=8)
        self.hunger_changes = deque(maxlen=12)
        self.last_weak = None
        self.stationary_moves = {}
        self.action_count = inner.action_count
        self.last_hp = None
        self.last_hunger = None

    def record(self, observation, action=None):
        stats = observation['blstats']
        row = {key: int(stats[idx]) for key, idx in FIELDS.items()}
        raw_message = bytes(observation['message']).split(b'\0', 1)[0]
        row['message'] = raw_message.decode('latin1', errors='replace')
        if action is not None:
            native_action = ACTIONS[action]
            row['action'] = getattr(native_action, 'name', str(native_action))
        if self.last_hp is not None and row['hp'] < self.last_hp:
            self.injuries.append(row)
            if row['hp'] > 0 and self.last_hp - row['hp'] >= row['max_hp'] / 4:
                self.bursts.append(self.context(row, observation))
        if 0 < row['hp'] <= row['max_hp'] / 3 and \
                (not self.critical or self.critical[-1]['state']['turn'] != row['turn']):
            self.critical.append(self.context(row, observation))
        if row['hp'] > 0 and row['hunger'] >= 3 and row['hunger'] != self.last_hunger:
            change = {'state': row, 'inventory': self.inventory(observation)}
            self.hunger_changes.append(change)
            if row['hunger'] == 3:
                self.last_weak = change
        self.last_hp = row['hp']
        self.last_hunger = row['hunger']
        return row

    @staticmethod
    def inventory(observation):
        return [bytes(item).split(b'\0', 1)[0].decode('latin1') for item in observation['inv_strs'] if item[0]]

    @classmethod
    def context(cls, row, observation):
        y0, x0 = max(0, row['y'] - 3), max(0, row['x'] - 3)
        y1, x1 = row['y'] + 4, row['x'] + 4
        return {
            'state': row, 'origin': (y0, x0),
            'chars': [bytes(line).decode('latin1') for line in observation['chars'][y0:y1, x0:x1]],
            'glyphs': observation['glyphs'][y0:y1, x0:x1].tolist(),
            'inventory': cls.inventory(observation),
        }

    def reset(self, spec):
        obs = self.inner.reset(spec)
        self.initial = self.record(obs)
        return obs

    def step(self, action):
        previous = self.tail[-1] if self.tail else self.initial
        result = self.inner.step(action)
        row = self.record(result[0], action)
        if row['action'] in DIRECTIONS and row['turn'] > previous['turn'] and \
                (row['dungeon'], row['level'], row['x'], row['y']) == \
                (previous['dungeon'], previous['level'], previous['x'], previous['y']):
            message = row['message']
            if message in self.stationary_moves or len(self.stationary_moves) < 160:
                item = self.stationary_moves.setdefault(message, {'count': 0, 'first': row})
                item['count'] += 1
                item['last'] = row
        self.tail.append(row)
        return result

    def metrics(self):
        return self.inner.metrics()

    def close(self):
        try:
            OUTPUT.write_text(json.dumps({'initial': self.initial, 'damage': list(self.injuries),
                                          'bursts': list(self.bursts), 'critical': list(self.critical),
                                          'hunger_changes': list(self.hunger_changes),
                                          'last_weak': self.last_weak,
                                          'stationary_moves': self.stationary_moves,
                                          'tail': list(self.tail)},
                                         separators=(',', ':'))+'\n')
        finally:
            self.inner.close()


def record_environment(*args, **kwargs):
    return RecordedEnvironment(make_environment(*args, **kwargs))


if __name__ == '__main__':
    trajectory.make_environment = record_environment
    raise SystemExit(run.main())
