#!/usr/bin/env python3
"""Add a saved 1x-10x experience setting to Gold's in-game OPTIONS menu."""
import argparse
import difflib
from pathlib import Path


def replace_once(src, old, new):
    if src.count(old) != 1:
        raise ValueError('Unexpected upstream source: ' + repr(old[:80]))
    return src.replace(old, new, 1)


def patch_ram(src):
    return replace_once(src, '''wOptions2::
; bit 0: menu account off/on
\tdb

\tds 2
''', '''wOptions2::
; bit 0: menu account off/on
\tdb

; Formerly unused options byte. Encoding 0-9 means 1x-10x; old saves use 0.
; Keep wOptionsEnd and every existing WRAM/SRAM offset unchanged.
wExpMultiplier:: db
\tds 1
''')


def patch_options(src):
    if 'Options_Experience:' in src:
        raise ValueError('Experience setting already applied')
    src = replace_once(src, '\tconst OPT_CANCEL        ; 7\nDEF NUM_OPTIONS EQU const_value ; 8',
                       '\tconst OPT_EXPERIENCE    ; 7\n\tconst OPT_CANCEL        ; 8\nDEF NUM_OPTIONS EQU const_value ; 9')
    src = replace_once(src, '; BUG: Options menu fails to clear joypad state on initialization (see docs/bugs_and_glitches.md)\n', '')
    src = replace_once(src, '\tld c, NUM_OPTIONS - 2 ; omit frame type, the last option', '\tld c, NUM_OPTIONS - 1 ; omit CANCEL; paint experience too')
    src = replace_once(src, '\tldh [hJoyLast], a\n\tcall GetOptionPointer', '\tldh [hJoyLast], a\n\tldh [hJoyPressed], a\n\tcall GetOptionPointer')
    src = replace_once(src, '\tdb "FRAME<LF>"\n\tdb "        :TYPE<LF>"\n\tdb "CANCEL@"',
                       '\tdb "FRAME   :TYPE<LF>"\n\tdb "EXP GAIN:<LF>"\n\tdb "CANCEL@"')
    src = replace_once(src, '\tdw Options_Frame\n\tdw Options_Cancel', '\tdw Options_Frame\n\tdw Options_Experience\n\tdw Options_Cancel')
    src = replace_once(src, '\thlcoord 16, 15 ; where on the screen the number is drawn', '\thlcoord 16, 14 ; compact frame row leaves room for EXP GAIN')
    src = replace_once(src, '''\thlcoord 1, 2
\tld bc, 2 * SCREEN_WIDTH
\tld a, [wJumptableIndex]
\tcall AddNTimes
\tld [hl], '▶'
''', '''\tld a, [wJumptableIndex]
\tcp OPT_EXPERIENCE
\tjr c, .RegularRow
\tsub OPT_EXPERIENCE
\thlcoord 1, 15
\tld bc, SCREEN_WIDTH
\tjr .PlaceCursor
.RegularRow:
\thlcoord 1, 2
\tld bc, 2 * SCREEN_WIDTH
.PlaceCursor:
\tcall AddNTimes
\tld [hl], '▶'
''')
    return src + '''
Options_Experience:
\tld a, [wExpMultiplier]
\tcp 10
\tjr c, .Valid
\txor a ; invalid old/reserved data safely means 1x
.Valid:
\tld c, a
\tldh a, [hJoyPressed]
\tbit B_PAD_LEFT, a
\tjr nz, .Left
\tbit B_PAD_RIGHT, a
\tjr z, .Save
\tinc c
\tld a, c
\tcp 10
\tjr c, .Save
\tld c, 0
\tjr .Save
.Left:
\tld a, c
\tand a
\tjr nz, .Decrease
\tld c, 10
.Decrease:
\tdec c
.Save:
\tld a, c
\tld [wExpMultiplier], a
\tld b, 0
\tld hl, .Strings
\tadd hl, bc
\tadd hl, bc
\tld a, [hli]
\tld d, [hl]
\tld e, a
\thlcoord 13, 15
\tcall PlaceString
\tand a
\tret
.Strings:
\tdw .X1, .X2, .X3, .X4, .X5, .X6, .X7, .X8, .X9, .X10
.X1:  db "1x @"
.X2:  db "2x @"
.X3:  db "3x @"
.X4:  db "4x @"
.X5:  db "5x @"
.X6:  db "6x @"
.X7:  db "7x @"
.X8:  db "8x @"
.X9:  db "9x @"
.X10: db "10x@"
'''


def patch_battle(src):
    if 'ApplyExpMultiplier:' in src:
        raise ValueError('Experience multiplier already applied')
    # Expand the awarded amount to 24 bits throughout display, animation and
    # actual party data, so 10x high-level/traded/Lucky Egg awards never wrap.
    src = replace_once(src, '\tld [wStringBuffer2 + 2], a\n\tld a, [wBattleMode]', '\tld [wStringBuffer2 + 3], a\n\tld a, [wBattleMode]')
    src = replace_once(src, '''\tcp LUCKY_EGG
\tcall z, BoostExp
\tldh a, [hQuotient + 3]
\tld [wStringBuffer2 + 1], a
\tldh a, [hQuotient + 2]
\tld [wStringBuffer2], a
''', '''\tcp LUCKY_EGG
\tcall z, BoostExp
\tcall ApplyExpMultiplier
\tldh a, [hQuotient + 3]
\tld [wStringBuffer2 + 2], a
\tldh a, [hQuotient + 2]
\tld [wStringBuffer2 + 1], a
\tldh a, [hQuotient + 1]
\tld [wStringBuffer2], a
''')
    src = replace_once(src, '''\tld a, [wStringBuffer2 + 1]
\tldh [hQuotient + 3], a
\tld a, [wStringBuffer2]
\tldh [hQuotient + 2], a
''', '''\tld a, [wStringBuffer2 + 2]
\tldh [hQuotient + 3], a
\tld a, [wStringBuffer2 + 1]
\tldh [hQuotient + 2], a
\tld a, [wStringBuffer2]
\tldh [hQuotient + 1], a
''')
    src = replace_once(src, '''\tld [hl], a
\tjr nc, .no_exp_overflow
\tdec hl
\tinc [hl]

.no_exp_overflow
''', '''\tld [hld], a
\tldh a, [hQuotient + 1]
\tadc [hl]
\tld [hl], a

.no_exp_overflow
''')
    src = replace_once(src, '\tld a, [wStringBuffer2 + 2] ; IsTradedMon', '\tld a, [wStringBuffer2 + 3] ; IsTradedMon')
    src = replace_once(src, '''\tld [wExperienceGained + 1], a
\tpush af
\txor a
\tld [wExperienceGained], a
''', '''\tld [wExperienceGained + 1], a
\tpush af
\tldh a, [hProduct + 1]
\tld [wExperienceGained], a
\tpush af
''')
    src = replace_once(src, '''\tld [hld], a
\tjr nc, .NoOverflow
\tinc [hl]

.NoOverflow:
''', '''\tld [hld], a
\tld a, [wExperienceGained]
\tadc [hl]
\tld [hl], a

.NoOverflow:
''')
    src = replace_once(src, '''\tcall TerminateExpBarSound
\tpop af
\tldh [hProduct + 2], a
''', '''\tcall TerminateExpBarSound
\tpop af
\tldh [hProduct + 1], a
\tpop af
\tldh [hProduct + 2], a
''')
    # Routine resides in the same bank as the original battle experience path.
    return src + '''
ApplyExpMultiplier:
\tpush bc
\tld a, [wExpMultiplier]
\tcp 10
\tjr c, .Valid
\txor a
.Valid:
\tinc a ; stored 0-9 becomes an actual 1x-10x multiplier
\tldh [hMultiplier], a
\txor a
\tldh [hMultiplicand], a ; vanilla bonuses fit in the low 16 bits
\tcall Multiply
\tpop bc
\tret
'''


def patch_text(src):
    old = '\ttext_decimal wStringBuffer2, 2, 4'
    if src.count(old) != 2:
        raise ValueError('Unexpected experience message format')
    return src.replace(old, '\ttext_decimal wStringBuffer2, 3, 6')


TRANSFORMS = {
    'ram/wram.asm': patch_ram,
    'engine/menus/options_menu.asm': patch_options,
    'engine/battle/core.asm': patch_battle,
    'data/text/common_1.asm': patch_text,
}


def apply(repo, dry_run=False):
    changes = []
    for relative, transform in TRANSFORMS.items():
        path = repo / relative
        old = path.read_text()
        changes.append((relative, path, old, transform(old)))
    # All inputs must validate before the first file changes.
    for relative, path, old, new in changes:
        if dry_run:
            print(''.join(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
                                             fromfile='a/' + relative, tofile='b/' + relative)))
        else:
            path.write_text(new)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repo', type=Path)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    apply(args.repo, args.dry_run)
