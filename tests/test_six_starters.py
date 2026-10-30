"""Exercise choice/confirmation/story flow against the real upstream lab script."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'build-tools'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from patch_six_starters import patch

SOURCE = (Path(__file__).parent / 'fixtures/ElmsLab.asm').read_text()


class ScriptRunner:
    """Small interpreter for the event/branch commands used by these lab flows.

    Rendering/audio are recorded or ignored; this does not replace emulator testing.
    """
    def __init__(self, source):
        self.lines = source.splitlines()
        self.labels = {s[:-1]: i + 1 for i, s in enumerate(self.lines) if s.endswith(':')}
        self.events = set()
        self.party = []
        self.previews = []
        self.hidden = set()
        self.scene = None

    def run(self, entry, choice, confirm=True):
        pc, stack, value = self.labels[entry], [], 0
        for _ in range(300):
            line = self.lines[pc].strip()
            pc += 1
            if not line or line.startswith(';') or line.endswith(':'):
                continue
            op, _, tail = line.partition(' ')
            args = tail.split(', ')
            if op == 'checkevent':
                value = int(tail in self.events)
            elif op == 'setevent':
                self.events.add(tail)
            elif op == 'verticalmenu':
                value = choice
            elif op == 'yesorno':
                value = int(confirm)
            elif op == 'setval':
                value = {'TRUE': 1, 'FALSE': 0}[tail]
            elif op == 'iftrue' and value or op == 'iffalse' and not value:
                pc = self.labels[tail]
            elif op == 'ifequal':
                if args[0].isdigit() and value == int(args[0]):
                    pc = self.labels[args[1]]
            elif op == 'sjump':
                pc = self.labels[tail]
            elif op == 'scall':
                stack.append(pc)
                pc = self.labels[tail]
            elif op == 'end':
                if not stack:
                    return
                pc = stack.pop()
            elif op == 'givepoke':
                self.party.append(args)
            elif op == 'pokepic':
                self.previews.append(tail)
            elif op == 'disappear':
                self.hidden.add(tail)
            elif op == 'setscene':
                self.scene = tail
            elif op == 'readvar':
                value = 'DOWN'
            elif op in {'iftrue', 'iffalse', 'turnobject', 'opentext', 'writetext',
                        'loadmenu', 'closewindow', 'closetext', 'waitbutton', 'cry',
                        'closepokepic', 'reanchormap', 'promptbutton', 'waitsfx',
                        'getmonname', 'playsound', 'applymovement', 'addcellnum', 'setmapscene'}:
                pass
            else:
                raise AssertionError('Unexpected instruction: ' + line)
        raise AssertionError('Script did not terminate')


class SixStarterTests(unittest.TestCase):
    def setUp(self):
        self.patched = patch(SOURCE)

    def test_all_six_choices_from_each_ball(self):
        expected = [('BULBASAUR', 'CHIKORITA', 3), ('CHARMANDER', 'CYNDAQUIL', 1),
                    ('SQUIRTLE', 'TOTODILE', 2), ('CHIKORITA', 'CHIKORITA', 3),
                    ('CYNDAQUIL', 'CYNDAQUIL', 1), ('TOTODILE', 'TOTODILE', 2)]
        for ball in ('Cyndaquil', 'Totodile', 'Chikorita'):
            for choice, (species, flag, hidden) in enumerate(expected, 1):
                with self.subTest(ball=ball, species=species):
                    runner = ScriptRunner(self.patched)
                    runner.run(ball + 'PokeBallScript', choice)
                    self.assertEqual(runner.party, [[species, '5', 'BERRY']])
                    self.assertEqual(runner.previews, [species])
                    self.assertEqual(runner.hidden, {'ELMSLAB_POKE_BALL' + str(hidden)})
                    starter_flags = {e for e in runner.events if e.endswith('_FROM_ELM') and e != 'EVENT_GOT_A_POKEMON_FROM_ELM'}
                    self.assertEqual(starter_flags, {'EVENT_GOT_' + flag + '_FROM_ELM'})
                    self.assertIn('EVENT_GOT_A_POKEMON_FROM_ELM', runner.events)
                    self.assertIn('EVENT_RIVAL_CHERRYGROVE_CITY', runner.events)
                    self.assertEqual(runner.scene, 'SCENE_ELMSLAB_AIDE_GIVES_POTION')
                    for other in ('Cyndaquil', 'Totodile', 'Chikorita'):
                        runner.run(other + 'PokeBallScript', choice)
                    self.assertEqual(len(runner.party), 1)

    def test_cancel_and_decline_allow_a_later_choice(self):
        for choice, confirm in [(0, True)] + [(i, False) for i in range(1, 7)]:
            with self.subTest(choice=choice, confirm=confirm):
                runner = ScriptRunner(self.patched)
                runner.run('CyndaquilPokeBallScript', choice, confirm)
                self.assertEqual(runner.party, [])
                self.assertEqual(runner.events, set())
                self.assertEqual(runner.hidden, set())
                self.assertIsNone(runner.scene)
                runner.run('TotodilePokeBallScript', 1)
                self.assertEqual(runner.party, [['BULBASAUR', '5', 'BERRY']])

    def test_unrelated_story_and_map_layout_preserved(self):
        for label in ('ElmDirectionsScript:', 'ElmAfterTheftScript:', 'ElmsLab_MapEvents:'):
            old = SOURCE.split(label, 1)[1].split('\n\n', 1)[0]
            self.assertIn(label + old, self.patched)
        self.assertEqual(self.patched.split('ElmsLab_MapEvents:', 1)[1], SOURCE.split('ElmsLab_MapEvents:', 1)[1])

    def test_reapplication_and_changed_upstream_fail(self):
        with self.assertRaises(ValueError):
            patch(self.patched)
        with self.assertRaises(ValueError):
            patch(SOURCE.replace('givepoke CYNDAQUIL', 'givepoke MAREEP'))


if __name__ == '__main__':
    unittest.main()
