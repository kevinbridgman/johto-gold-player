#!/usr/bin/env python3
"""Offer six unique starter gifts while preserving Elm's original story events."""
import argparse
import difflib
from pathlib import Path
import re

# Only the first gift sets Gold's rival-selection flags.
CHOICES = (
    ('Bulbasaur', 'Chikorita', 'grass'),
    ('Charmander', 'Cyndaquil', 'fire'),
    ('Squirtle', 'Totodile', 'water'),
    ('Chikorita', 'Chikorita', 'grass'),
    ('Cyndaquil', 'Cyndaquil', 'fire'),
    ('Totodile', 'Totodile', 'water'),
)
GIFT_FLAGS = tuple('EVENT_ELM_GIFT_' + name.upper() for name, _, _ in CHOICES)
MIGRATION_FLAG = 'EVENT_ELM_STARTER_GIFTS_INITIALIZED'


def patch_events(src):
    """Name seven unused persistent bits without moving any existing event ID."""
    marker = '\tconst_skip ; unused'
    if MIGRATION_FLAG in src or src.count(marker) < 7:
        raise ValueError('Unexpected event flag layout or gifts already applied')
    for flag in (*GIFT_FLAGS, MIGRATION_FLAG):
        src = src.replace(marker, '\tconst ' + flag, 1)
    return src


def menu_tree(prefix=(), index=0):
    """Compile all 64 subsets; each displayed row maps to its remaining species.

    Native static menus avoid extra WRAM, custom rendering, and volatile save data.
    """
    label = 'SixStarterSubset' + (''.join(map(str, prefix)) or 'Root')
    text = label + ':\n'
    if index < len(CHOICES):
        no = 'SixStarterSubset' + ''.join(map(str, (*prefix, 0)))
        yes = 'SixStarterSubset' + ''.join(map(str, (*prefix, 1)))
        text += f'\tcheckevent {GIFT_FLAGS[index]}\n\tiftrue {yes}\n\tsjump {no}\n\n'
        return text + menu_tree((*prefix, 0), index + 1) + menu_tree((*prefix, 1), index + 1)
    remaining = [c for claimed, c in zip(prefix, CHOICES) if not claimed]
    if not remaining:
        return text + '\tsjump SixStarterAllTakenScript\n\n'
    header = label + 'Header'
    text += f'\tloadmenu {header}\n\tverticalmenu\n\tclosewindow\n'
    for row, (name, _, _) in enumerate(remaining, 1):
        text += f'\tifequal {row}, SixStarterChoose{name}Script\n'
    text += '\tsjump SixStarterCancelScript\n\n'
    text += (f'{header}:\n\tdb MENU_BACKUP_TILES\n'
             f'\tmenu_coords 0, 0, 14, {2 * len(remaining) + 1}\n'
             '\tdw .MenuData\n\tdb 1 ; default option\n\n.MenuData:\n'
             f'\tdb STATICMENU_CURSOR\n\tdb {len(remaining)} ; remaining gifts (B cancels)\n')
    for name, _, _ in remaining:
        text += f'\tdb "{name.upper()}@"\n'
    return text + '\n'


def patch(src):
    if 'SixStarterMenuScript:' in src:
        raise ValueError('Six-starter menu already applied')
    out, originals = src, {}
    for name, following in (('Cyndaquil', 'TotodilePokeBallScript'),
                            ('Totodile', 'ChikoritaPokeBallScript'),
                            ('Chikorita', 'DidntChooseStarterScript')):
        label, end = name + 'PokeBallScript:', following + ':'
        if src.count(label) != 1 or src.count(end) != 1:
            raise ValueError('Unexpected starter script boundaries: ' + name)
        section = src.split(label, 1)[1].split(end, 1)[0]
        for command in ('pokepic', 'cry', 'givepoke', 'getmonname STRING_BUFFER_3,'):
            if not re.search(r'\t' + re.escape(command) + ' ' + name.upper() + r'\b', section):
                raise ValueError('Unexpected original starter: ' + name)
        originals[name] = section
        first = section.index('\treanchormap\n')
        last = section.index('\tclosetext\n', first) + len('\tclosetext\n')
        before = section[:first].replace('iftrue LookAtElmPokeBallScript', 'iftrue SixStarterReturnScript')
        replacement = before + '\tscall SixStarterMenuScript\n\tiffalse SixStarterEndScript\n' + section[last:]
        out = out.replace(label + section + end, label + replacement + end, 1)

    # Run the original quest/reward conversation before the optional gift offer.
    # A script call returns across its original sjump/end branches as normal.
    elm = 'ProfElmScript:\n\tfaceplayer\n\topentext\n'
    if out.count(elm) != 1:
        raise ValueError('Unexpected Elm conversation entry')
    out = out.replace(elm, '''ProfElmScript:
\tscall SixStarterOriginalElmScript
\tcheckevent EVENT_GOT_A_POKEMON_FROM_ELM
\tiffalse SixStarterEndScript
\tsjump SixStarterReturnScript

SixStarterOriginalElmScript:
\tfaceplayer
\topentext
''', 1)
    menu = '''SixStarterEndScript:
\tend

SixStarterReturnScript:
\tfaceplayer
\tscall SixStarterInitializeScript
'''
    for flag in GIFT_FLAGS:
        menu += f'\tcheckevent {flag}\n\tiffalse SixStarterOfferScript\n'
    menu += '''\topentext
\tsjump SixStarterAllTakenScript

SixStarterOfferScript:
\topentext
\twritetext SixStarterReturnText
\tyesorno
\tiffalse SixStarterCancelScript
\tscall SixStarterMenuScript
\tend

SixStarterMenuScript:
\tscall SixStarterInitializeScript
\topentext
\twritetext SixStarterMenuText
\tsjump SixStarterSubsetRoot

SixStarterCancelScript:
\twritetext DidntChooseStarterText
\twaitbutton
\tclosetext
\tsetval FALSE
\tend

SixStarterNoRoomScript:
\twritetext SixStarterNoRoomText
\twaitbutton
\tclosetext
\tsetval FALSE
\tend

SixStarterAllTakenScript:
\twritetext SixStarterAllTakenText
\twaitbutton
\tclosetext
\tsetval FALSE
\tend

SixStarterInitializeScript:
'''
    menu += f'\tcheckevent {MIGRATION_FLAG}\n\tiftrue SixStarterEndScript\n'
    menu += '\tcheckevent EVENT_GOT_A_POKEMON_FROM_ELM\n\tiffalse SixStarterInitializeDoneScript\n'
    # v1.1 had no species-specific gift flags. Its Pokedex remembers base forms
    # even after evolution, deposit, release or trading away. Conservatively
    # retire all starter species previously owned when migrating an old save.
    for index, ((name, _, _), flag) in enumerate(zip(CHOICES, GIFT_FLAGS)):
        menu += (f'\tcallasm SixStarterCaught{name}\n'
                 f'\tiffalse SixStarterInitializeNext{index}\n\tsetevent {flag}\n'
                 f'SixStarterInitializeNext{index}:\n')
    menu += f'SixStarterInitializeDoneScript:\n\tsetevent {MIGRATION_FLAG}\n\tend\n\n'
    for name, _, _ in CHOICES:
        species = name.upper()
        menu += (f'SixStarterCaught{name}:\n'
                 f'\tld a, [wPokedexCaught + ({species} - 1) / 8]\n'
                 f'\tand 1 << (({species} - 1) % 8)\n\tld [wScriptVar], a\n\tret\n\n')
    menu += menu_tree()
    for (name, original, typ), flag in zip(CHOICES, GIFT_FLAGS):
        section = originals[original]
        first = section.index('\treanchormap\n')
        last = section.index('\tclosetext\n', first) + len('\tclosetext\n')
        core = section[first:last]
        original_gift = re.search(r'\tdisappear [^\n]+\n\tsetevent [^\n]+\n', core).group()
        core = core.replace(original_gift, '')
        for command in ('pokepic', 'cry', 'givepoke', 'getmonname STRING_BUFFER_3,'):
            core = core.replace(command + ' ' + original.upper(), command + ' ' + name.upper())
        core = core.replace('Take' + original + 'Text', 'SixStarterTake' + name + 'Text')
        core = core.replace('iffalse DidntChooseStarterScript', 'iffalse SixStarterCancelScript')
        core = core.replace('\twritetext ChoseStarterText',
                            '\treadvar VAR_PARTYCOUNT\n\tifequal PARTY_LENGTH, SixStarterNoRoomScript\n\twritetext ChoseStarterText')
        core = core.replace('\tclosetext\n', '')
        menu += (f'SixStarterChoose{name}Script:\n\tcheckevent {flag}\n'
                 '\tiftrue SixStarterCancelScript\n\tclosetext\n' + core
                 + '\tifequal 2, SixStarterNoRoomScript ; GivePoke failure\n'
                 + f'\tsetevent {flag}\n\tcheckevent EVENT_GOT_A_POKEMON_FROM_ELM\n'
                 + '\tiftrue SixStarterGiftDoneScript\n' + original_gift
                 + '\tsjump SixStarterGiftDoneScript\n\n')
        menu += (f'SixStarterTake{name}Text:\n\ttext "ELM: Do you want"\n'
                 f'\tline "{name.upper()}, the"\n\tcont "{typ} #MON?"\n\tdone\n\n')
    menu += '''SixStarterGiftDoneScript:
\tclosetext
\tsetval TRUE
\tend

SixStarterMenuText:
\ttext "Choose a partner!"
\tline "B: Cancel"
\tdone

SixStarterReturnText:
\ttext "ELM: I hope your"
\tline "#MON is doing"
\tcont "well!"

\tpara "I have some others"
\tline "for you if you"
\tcont "want another"
\tcont "companion on your"
\tcont "journey!"

\tpara "Help yourself!"
\tline "Want to choose?"
\tdone

SixStarterNoRoomText:
\ttext "ELM: Your party"
\tline "is full!"

\tpara "Make room for a"
\tline "new companion,"
\tcont "then come back."
\tdone

SixStarterAllTakenText:
\ttext "ELM: You've taken"
\tline "all six partners!"

\tpara "Take good care of"
\tline "your companions!"
\tdone

'''
    out = out.replace('DidntChooseStarterScript:\n', menu + 'DidntChooseStarterScript:\n', 1)
    old_intro = '\tpara "Go on. Pick one!"\n'
    if out.count(old_intro) != 1:
        raise ValueError('Unexpected Elm introduction')
    # Identical to v1.1: first-choice dialogue is unchanged in this release.
    out = out.replace(old_intro, '''\tpara "There are six"
\tline "partners to choose"
\tcont "from today."

\tpara "Check any # BALL"
\tline "to see all six!"
''', 1)
    return out


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('repo', type=Path)
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args()
    # Validate both transformations before writing either file.
    changes = []
    for relative, transform in [('maps/ElmsLab.asm', patch), ('constants/event_flags.asm', patch_events)]:
        path = args.repo / relative
        old = path.read_text()
        changes.append((relative, path, old, transform(old)))
    for relative, path, old, new in changes:
        if args.dry_run:
            print(''.join(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
                                             fromfile='a/' + relative, tofile='b/' + relative)))
        else:
            path.write_text(new)
    if not args.dry_run:
        print('Added six unique starter gifts, repeat visits, and persistent claim tracking')
