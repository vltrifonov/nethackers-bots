import functools

import nle.nethack as nh

from .monflag import *


# NetHack (NLE 1.3): summon_minion directly selects ndemon's ordinary
# generatable demons or one of four elementals, then sets instance isminion.
# These species need not carry the species-level M2_MINION flag.
_DEITY_SERVANT_SPECIES = frozenset({
    'succubus', 'horned devil', 'incubus', 'erinys', 'barbed devil',
    'marilith', 'vrock', 'hezrou', 'bone devil', 'ice devil', 'nalfeshnee',
    'pit fiend', 'balrog', 'air elemental', 'fire elemental',
    'earth elemental', 'water elemental',
})


def is_monster(glyph):
    return nh.glyph_is_monster(glyph)


def is_pet(glyph):
    return nh.glyph_is_pet(glyph)


@functools.lru_cache(nh.NUMMONS * 10)
def permonst(glyph):
    if nh.glyph_is_monster(glyph):
        return nh.permonst(nh.glyph_to_mon(glyph))
    elif nh.glyph_is_pet(glyph):
        return nh.permonst(nh.glyph_to_pet(glyph))
    elif nh.glyph_is_body(glyph):
        return nh.permonst(glyph - nh.GLYPH_BODY_OFF)
    else:
        assert 0, glyph


def find(glyph):
    if glyph in ALL_MONS or glyph in MON.ALL_PETS:
        return f'MON.fn({repr(permonst(glyph).mname)})'


@functools.lru_cache(nh.NUMMONS)
def from_name(name):
    return nh.GLYPH_MON_OFF + id_from_name(name)


@functools.lru_cache(nh.NUMMONS)
def id_from_name(name):
    for i in range(nh.NUMMONS):
        if nh.permonst(i).mname == name:
            return i
    # Guardians and directly summoned servants display a deity suffix.
    # Preserve canonical names containing " of " before considering it.
    species, separator, deity = name.partition(' of ')
    if separator and deity.strip():
        for i in range(nh.NUMMONS):
            monster = nh.permonst(i)
            if monster.mname == species and (
                    monster.mflags2 & M2_MINION or species in _DEITY_SERVANT_SPECIES):
                return i
    assert 0, name


@functools.lru_cache(nh.NUMMONS)
def ids_from_name(name):
    """Species matching a displayed name; shared role titles need glyph context."""
    for i in range(nh.NUMMONS):
        if nh.permonst(i).mname == name:
            return (i,)
    # Caveman and Cavewoman monsters use these same NetHack rank titles.
    # Keep both candidates so corpse tracking uses the actual vanished glyph.
    if name.lower() in {
            'troglodyte', 'aborigine', 'wanderer', 'vagrant', 'wayfarer',
            'roamer', 'nomad', 'rover', 'pioneer'}:
        return (id_from_name('caveman'), id_from_name('cavewoman'))
    return (id_from_name(name),)


def body_from_name(name):
    return id_from_name(name) + nh.GLYPH_BODY_OFF


fn = from_name

ALL_MONS = [nh.GLYPH_MON_OFF + i for i in range(nh.NUMMONS)]
ALL_PETS = [nh.GLYPH_PET_OFF + i for i in range(nh.NUMMONS)]
