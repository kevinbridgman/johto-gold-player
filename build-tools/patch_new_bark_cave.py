#!/usr/bin/env python3
"""Add an empty, fully lit cave immediately west of New Bark Town."""
import argparse
import difflib
from pathlib import Path

WIDTH, HEIGHT = 10, 8  # blocks; each block is two by two walking tiles
ENTRANCE_X, ENTRANCE_Y = 52, 5  # Route 29's east end, reachable without HMs
EXIT_X, EXIT_Y = 9, 15
MAP_SCRIPT = '''\tobject_const_def

NewBarkCave_MapScripts:
\tdef_scene_scripts
\tdef_callbacks

NewBarkCave_MapEvents:
\tdb 0, 0 ; filler
\tdef_warp_events
\twarp_event 9, 15, ROUTE_29, 2
\tdef_coord_events
\tdef_bg_events
\tdef_object_events
'''


def replace_once(src, old, new):
    if src.count(old) != 1:
        raise ValueError('Unexpected upstream source: ' + repr(old[:80]))
    return src.replace(old, new, 1)


def cave_blocks():
    # Original cave tiles, with a continuous floor and one south-facing exit.
    rows = [[0x04] + [0x05] * (WIDTH - 2) + [0x06]]
    rows += [[0x08] + [0x02] * (WIDTH - 2) + [0x0a] for _ in range(HEIGHT - 2)]
    rows += [[0x0c] + [0x0d] * (WIDTH - 2) + [0x0e]]
    rows[EXIT_Y // 2][EXIT_X // 2] = 0x24
    return bytes(block for row in rows for block in row)


def apply(repo, dry_run=False):
    if (repo / 'maps/NewBarkCave.asm').exists() or (repo / 'maps/NewBarkCave.blk').exists():
        raise ValueError('New Bark Cave already exists')
    changes = {}
    def edit(relative, transform):
        old = (repo / relative).read_text()
        changes[relative] = (old.encode(), transform(old).encode())

    edit('constants/map_constants.asm', lambda s: replace_once(s,
        '\tmap_const ROUTE_29_ROUTE_46_GATE,                       5,  4 ; 13\n\tendgroup',
        '\tmap_const ROUTE_29_ROUTE_46_GATE,                       5,  4 ; 13\n'
        '\tmap_const NEW_BARK_CAVE,                              10,  8 ; 14\n\tendgroup'))
    edit('data/maps/maps.asm', lambda s: replace_once(s,
        '\tassert_table_length NUM_NEW_BARK_MAPS',
        '\tmap NewBarkCave, TILESET_CAVE, CAVE, LANDMARK_ROUTE_29, MUSIC_UNION_CAVE, TRUE, PALETTE_DAY, FISHGROUP_LAKE\n'
        '\tassert_table_length NUM_NEW_BARK_MAPS'))
    edit('data/maps/attributes.asm', lambda s: s.rstrip() + '\n\tmap_attributes NewBarkCave, NEW_BARK_CAVE, $01\n')
    edit('data/maps/blocks.asm', lambda s: s.rstrip() + '''

SECTION "New Bark Cave Blocks", ROMX
NewBarkCave_Blocks:
\tINCBIN "maps/NewBarkCave.blk"
ENDSECTION
''')
    edit('data/maps/scripts.asm', lambda s: s.rstrip() + '''

SECTION "New Bark Cave Script", ROMX
INCLUDE "maps/NewBarkCave.asm"
ENDSECTION
''')
    edit('maps/Route29.asm', lambda s: replace_once(s,
        '\twarp_event 27,  1, ROUTE_29_ROUTE_46_GATE, 3',
        '\twarp_event 27,  1, ROUTE_29_ROUTE_46_GATE, 3\n\twarp_event 52,  5, NEW_BARK_CAVE, 1'))
    route = (repo / 'maps/Route29.blk').read_bytes()
    if len(route) != 30 * 9:
        raise ValueError('Unexpected Route 29 block dimensions')
    offset = ENTRANCE_Y // 2 * 30 + ENTRANCE_X // 2
    if route[offset] != 0x05:
        raise ValueError('Route 29 entrance site has changed')
    modified = bytearray(route)
    modified[offset] = 0x73  # existing Johto cave-mouth block; CAVE at lower left
    changes['maps/Route29.blk'] = (route, bytes(modified))
    changes['maps/NewBarkCave.asm'] = (b'', MAP_SCRIPT.encode())
    changes['maps/NewBarkCave.blk'] = (b'', cave_blocks())
    # All changes validate first. No event flags, WRAM, SRAM, wild encounter
    # tables, trainer data, items, or existing map IDs need to change.
    for relative, (old, new) in changes.items():
        if dry_run:
            if relative.endswith('.blk'):
                print(f'{relative}: {len(old)} -> {len(new)} bytes')
            else:
                print(''.join(difflib.unified_diff(old.decode().splitlines(True), new.decode().splitlines(True),
                                                 fromfile='a/' + relative, tofile='b/' + relative)))
        else:
            (repo / relative).write_bytes(new)
    return changes


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repo', type=Path)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    apply(args.repo, args.dry_run)
