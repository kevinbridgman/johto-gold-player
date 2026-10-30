#!/usr/bin/env python3
"""Offer the Kanto and Johto starters through a shared menu in Elm's lab."""
import argparse
import difflib
from pathlib import Path
import re

# Keep Gold's three original starter flags: they select the rival's counter type.
CHOICES = (
    ('Bulbasaur', 'Chikorita', 'grass'),
    ('Charmander', 'Cyndaquil', 'fire'),
    ('Squirtle', 'Totodile', 'water'),
    ('Chikorita', 'Chikorita', 'grass'),
    ('Cyndaquil', 'Cyndaquil', 'fire'),
    ('Totodile', 'Totodile', 'water'),
)


def patch(src):
    if 'SixStarterMenuScript:' in src:
        raise ValueError('Six-starter menu already applied')
    out = src
    originals = {}
    for name, following in (('Cyndaquil', 'TotodilePokeBallScript'),
                            ('Totodile', 'ChikoritaPokeBallScript'),
                            ('Chikorita', 'DidntChooseStarterScript')):
        label = name + 'PokeBallScript:'
        end = following + ':'
        if src.count(label) != 1 or src.count(end) != 1:
            raise ValueError('Unexpected starter script boundaries: ' + name)
        section = src.split(label, 1)[1].split(end, 1)[0]
        # Refuse an already-customized or incompatible source tree.
        for command in ('pokepic', 'cry', 'givepoke', 'getmonname STRING_BUFFER_3,'):
            if not re.search(r'\t' + re.escape(command) + ' ' + name.upper() + r'\b', section):
                raise ValueError('Unexpected original starter: ' + name)
        originals[name] = section
        first = section.index('\treanchormap\n')
        last = section.index('\tclosetext\n', first) + len('\tclosetext\n')
        # Retain the ball-specific movement and the original post-choice story.
        replacement = (section[:first] + '\tscall SixStarterMenuScript\n'
                       '\tiffalse SixStarterEndScript\n' + section[last:])
        out = out.replace(label + section + end, label + replacement + end, 1)

    menu = '''SixStarterEndScript:
\tend

SixStarterMenuScript:
\topentext
\twritetext SixStarterMenuText
\tloadmenu SixStarterMenuHeader
\tverticalmenu
\tclosewindow
'''
    for index, (name, _, _) in enumerate(CHOICES, 1):
        menu += f'\tifequal {index}, SixStarterChoose{name}Script\n'
    menu += '''\tsjump SixStarterCancelScript

SixStarterCancelScript:
\twritetext DidntChooseStarterText
\twaitbutton
\tclosetext
\tsetval FALSE
\tend

SixStarterMenuHeader:
\tdb MENU_BACKUP_TILES
\tmenu_coords 0, 0, 14, 13
\tdw .MenuData
\tdb 1 ; default option

.MenuData:
\tdb STATICMENU_CURSOR
\tdb 6 ; items (B cancels)
'''
    for name, _, _ in CHOICES:
        menu += f'\tdb "{name.upper()}@"\n'
    menu += '''
SixStarterMenuText:
\ttext "Choose a partner!"
\tline "B: Cancel"
\tdone

'''
    for name, original, typ in CHOICES:
        section = originals[original]
        first = section.index('\treanchormap\n')
        last = section.index('\tclosetext\n', first) + len('\tclosetext\n')
        core = section[first:last]
        # Change species and prompt only, never the story flag or ball identity.
        for command in ('pokepic', 'cry', 'givepoke', 'getmonname STRING_BUFFER_3,'):
            core = core.replace(command + ' ' + original.upper(), command + ' ' + name.upper())
        core = core.replace('Take' + original + 'Text', 'SixStarterTake' + name + 'Text')
        core = core.replace('iffalse DidntChooseStarterScript', 'iffalse SixStarterCancelScript')
        menu += ('SixStarterChoose' + name + 'Script:\n\tclosetext\n' + core
                 + '\tsetval TRUE\n\tend\n\n')
        menu += (f'SixStarterTake{name}Text:\n\ttext "ELM: Do you want"\n'
                 f'\tline "{name.upper()}, the"\n\tcont "{typ} #MON?"\n\tdone\n\n')

    out = out.replace('DidntChooseStarterScript:\n', menu + 'DidntChooseStarterScript:\n', 1)
    old_intro = '\tpara "Go on. Pick one!"\n'
    if out.count(old_intro) != 1:
        raise ValueError('Unexpected Elm introduction')
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
    path = args.repo / 'maps/ElmsLab.asm'
    old = path.read_text()
    new = patch(old)
    if args.dry_run:
        print(''.join(difflib.unified_diff(old.splitlines(True), new.splitlines(True),
                                         fromfile='a/maps/ElmsLab.asm', tofile='b/maps/ElmsLab.asm')))
    else:
        path.write_text(new)
        print('Added all six Kanto/Johto starter choices; original rival teams retained')
