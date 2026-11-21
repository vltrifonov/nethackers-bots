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
OUTPUT = Path('/out/diagnostics/arena-observations.json')
make_environment = trajectory.make_environment


class RecordedEnvironment:
    def __init__(self, inner):
        self.inner = inner
        self.initial = None
        self.tail = deque(maxlen=256)
        self.injuries = deque(maxlen=64)
        self.action_count = inner.action_count
        self.last_hp = None

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
        self.last_hp = row['hp']
        return row

    def reset(self, spec):
        obs = self.inner.reset(spec)
        self.initial = self.record(obs)
        return obs

    def step(self, action):
        result = self.inner.step(action)
        self.tail.append(self.record(result[0], action))
        return result

    def metrics(self):
        return self.inner.metrics()

    def close(self):
        try:
            OUTPUT.write_text(json.dumps({'initial': self.initial, 'damage': list(self.injuries), 'tail': list(self.tail)},
                                         separators=(',', ':'))+'\n')
        finally:
            self.inner.close()


def record_environment(*args, **kwargs):
    return RecordedEnvironment(make_environment(*args, **kwargs))


if __name__ == '__main__':
    trajectory.make_environment = record_environment
    raise SystemExit(run.main())
