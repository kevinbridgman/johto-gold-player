"""Exercise choice/confirmation/story flow against the real upstream lab script."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'build-tools'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from patch_six_starters import patch, patch_events, CHOICES, GIFT_FLAGS, MIGRATION_FLAG
import itertools
import re

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
        self.texts = []
        self.caught = set()
        self.current_menu = None
        self.menus = []
        self.party_limit = 6

    def run(self, entry, choice, confirm=True):
        pc, stack, value = self.labels[entry], [], 0
        for _ in range(1200):
            line = self.lines[pc].strip()
            pc += 1
            if not line or line.startswith(';') or line.endswith(':'):
                continue
            op, _, tail = line.partition(' ')
            args = tail.split(', ')
            if op == 'checkevent':
                value = int(tail in self.events)
            elif op == 'checkflag':
                value = 0
            elif op == 'setevent':
                self.events.add(tail)
            elif op == 'loadmenu':
                self.current_menu = tail
            elif op == 'verticalmenu':
                section = '\n'.join(self.lines[self.labels[self.current_menu]:])
                count = int(re.search(r'db (\d+) ; remaining gifts', section).group(1))
                rows = re.findall(r'db "([A-Z]+)@"', section)[:count]
                self.menus.append(rows)
                value = rows.index(choice) + 1 if isinstance(choice, str) and choice in rows else choice if isinstance(choice, int) else 0
            elif op == 'callasm':
                value = int(tail.removeprefix('SixStarterCaught').upper() in self.caught)
            elif op == 'yesorno':
                value = int(confirm)
            elif op == 'setval':
                value = {'TRUE': 1, 'FALSE': 0}[tail]
            elif op == 'iftrue' and value or op == 'iffalse' and not value:
                pc = self.labels[tail]
            elif op == 'ifequal':
                if value == (int(args[0]) if args[0].isdigit() else self.party_limit if args[0] == 'PARTY_LENGTH' else args[0]):
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
                self.caught.add(args[0])
                value = 0
            elif op == 'pokepic':
                self.previews.append(tail)
            elif op == 'disappear':
                self.hidden.add(tail)
            elif op == 'setscene':
                self.scene = tail
            elif op == 'readvar':
                value = len(self.party) if tail == 'VAR_PARTYCOUNT' else 'DOWN'
            elif op == 'writetext':
                self.texts.append(tail)
            elif op in {'iftrue', 'iffalse', 'faceplayer', 'turnobject', 'opentext', 'writetext',
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

    def test_every_first_choice_and_ball_preserves_first_story_and_rival(self):
        for ball, (name, original, _) in itertools.product(('Cyndaquil', 'Totodile', 'Chikorita'), CHOICES):
            with self.subTest(ball=ball, name=name):
                runner = ScriptRunner(self.patched)
                runner.run(ball + 'PokeBallScript', name.upper())
                self.assertEqual(runner.party, [[name.upper(), '5', 'BERRY']])
                self.assertEqual(runner.previews, [name.upper()])
                flag = 'EVENT_GOT_' + original.upper() + '_FROM_ELM'
                self.assertEqual({f for f in runner.events if f in {
                    'EVENT_GOT_CHIKORITA_FROM_ELM', 'EVENT_GOT_CYNDAQUIL_FROM_ELM',
                    'EVENT_GOT_TOTODILE_FROM_ELM'}}, {flag})
                self.assertIn('EVENT_GOT_A_POKEMON_FROM_ELM', runner.events)
                self.assertIn('EVENT_RIVAL_CHERRYGROVE_CITY', runner.events)
                self.assertIn('EVENT_ELM_GIFT_' + name.upper(), runner.events)
                self.assertEqual(runner.scene, 'SCENE_ELMSLAB_AIDE_GIVES_POTION')
                self.assertNotIn('SixStarterReturnText', runner.texts)
                self.assertIn('ElmDirectionsText1', runner.texts)

    def test_all_720_collection_orders_shrink_without_changing_story(self):
        species = [c[0].upper() for c in CHOICES]
        for order in itertools.permutations(species):
            runner = ScriptRunner(self.patched)
            runner.run('CyndaquilPokeBallScript', order[0])
            story_flags = {e for e in runner.events if e not in GIFT_FLAGS}
            hidden, scene = runner.hidden.copy(), runner.scene
            for index, name in enumerate(order[1:], 1):
                runner.run('SixStarterReturnScript', name)
                self.assertEqual(runner.menus[-1], [s for s in species if s not in order[:index]])
                self.assertEqual(len(runner.party), index + 1)
                self.assertEqual({e for e in runner.events if e not in GIFT_FLAGS}, story_flags)
                self.assertEqual(runner.hidden, hidden)
                self.assertEqual(runner.scene, scene)
            runner.run('SixStarterReturnScript', 1)
            self.assertEqual(len(runner.party), 6)
            self.assertEqual(runner.texts[-1], 'SixStarterAllTakenText')

    def test_all_64_subsets_and_row_mappings(self):
        species = [c[0].upper() for c in CHOICES]
        for mask in range(64):
            remaining = [s for i, s in enumerate(species) if not mask & 1 << i]
            for row, selected in enumerate(remaining, 1):
                runner = ScriptRunner(self.patched)
                runner.events.update({MIGRATION_FLAG, 'EVENT_GOT_A_POKEMON_FROM_ELM'})
                runner.events.update(f for i, f in enumerate(GIFT_FLAGS) if mask & 1 << i)
                runner.run('SixStarterMenuScript', row)
                self.assertEqual(runner.menus, [remaining])
                self.assertEqual(runner.party, [[selected, '5', 'BERRY']])

    def test_cancel_decline_full_party_and_duplicate_guard_preserve_claims(self):
        for entry, choice, confirm, full in [
            ('CyndaquilPokeBallScript', 0, True, False),
            ('SixStarterMenuScript', 3, False, False),
            ('SixStarterReturnScript', 1, False, False),
            ('SixStarterMenuScript', 2, True, True),
        ]:
            runner = ScriptRunner(self.patched)
            runner.events.add(MIGRATION_FLAG)
            if full:
                runner.party = [['PIDGEY']] * 6
            before = runner.party.copy()
            runner.run(entry, choice, confirm)
            self.assertEqual(runner.party, before)
            self.assertEqual(runner.events, {MIGRATION_FLAG})
        runner = ScriptRunner(self.patched)
        runner.run('CyndaquilPokeBallScript', 'BULBASAUR')
        runner.party.clear()  # deposited, released, or traded away
        runner.run('SixStarterChooseBulbasaurScript', 1)
        self.assertEqual(runner.party, [])
        runner.run('SixStarterMenuScript', 'BULBASAUR')
        self.assertNotIn('BULBASAUR', runner.menus[-1])
        self.assertEqual(runner.party, [])

    def test_old_v11_save_migration_uses_pokedex_not_current_party(self):
        for name, _, _ in CHOICES:
            runner = ScriptRunner(self.patched)
            runner.events.add('EVENT_GOT_A_POKEMON_FROM_ELM')
            runner.caught.add(name.upper())
            runner.run('SixStarterReturnScript', 0)
            self.assertIn('EVENT_ELM_GIFT_' + name.upper(), runner.events)
            self.assertIn(MIGRATION_FLAG, runner.events)
            runner.run('SixStarterMenuScript', 0)
            self.assertNotIn(name.upper(), runner.menus[-1])
            self.assertEqual(len(runner.menus[-1]), 5)

    def test_original_story_runs_before_repeat_offer(self):
        runner = ScriptRunner(self.patched)
        runner.run('ProfElmScript', 0)
        self.assertEqual(runner.texts, ['ElmText_LetYourMonBattleIt'])
        runner.events.add('EVENT_GOT_A_POKEMON_FROM_ELM')
        runner.caught.add('CHIKORITA')
        runner.run('ProfElmScript', 0, confirm=False)
        self.assertEqual(runner.texts[-3:], ['ElmDescribesMrPokemonText', 'SixStarterReturnText', 'DidntChooseStarterText'])

    def test_unrelated_story_map_layout_and_first_dialogue_preserved(self):
        for label in ('ElmDirectionsScript:', 'ElmAfterTheftScript:', 'ElmsLab_MapEvents:'):
            old = SOURCE.split(label, 1)[1].split('\n\n', 1)[0]
            self.assertIn(label + old, self.patched)
        self.assertEqual(self.patched.split('ElmsLab_MapEvents:', 1)[1], SOURCE.split('ElmsLab_MapEvents:', 1)[1])
        for label in ('DidntChooseStarterText:', 'ChoseStarterText:', 'ReceivedStarterText:', 'ElmDirectionsText1:'):
            old = SOURCE.split(label, 1)[1].split('\n\n', 1)[0]
            self.assertIn(label + old, self.patched)

    def test_unused_bits_reused_without_shifting_existing_event_ids(self):
        original = (Path(__file__).parent / 'fixtures/event_flags.asm').read_text()
        new = patch_events(original)
        def ids(source):
            value, result = 0, {}
            for line in source.splitlines():
                line = line.split(';')[0].strip()
                if line.startswith('const_next'):
                    value = int(line.split()[1], 0)
                elif line.startswith('const_skip'):
                    value += int(line.split()[1], 0) if len(line.split()) > 1 else 1
                elif line.startswith('const '):
                    result[line.split()[1]] = value
                    value += 1
            return result
        before, after = ids(original), ids(new)
        for name, value in before.items():
            self.assertEqual(after[name], value)
        self.assertEqual(len(after) - len(before), 7)
        self.assertTrue(all(after[f] > 7 for f in (*GIFT_FLAGS, MIGRATION_FLAG)))
        with self.assertRaises(ValueError):
            patch_events(new)

    def test_reapplication_and_changed_upstream_fail(self):
        with self.assertRaises(ValueError):
            patch(self.patched)
        with self.assertRaises(ValueError):
            patch(SOURCE.replace('givepoke CYNDAQUIL', 'givepoke MAREEP'))


if __name__ == '__main__':
    unittest.main()
