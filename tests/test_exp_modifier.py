"""Source integration and safe-application checks for the experience setting."""
from contextlib import redirect_stdout
import io
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'build-tools'))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from patch_exp_modifier import TRANSFORMS, apply, patch_options, patch_ram

FIXTURES = {'ram/wram.asm': 'wram.asm', 'engine/menus/options_menu.asm': 'options_menu.asm',
            'engine/battle/core.asm': 'battle_core.asm', 'data/text/common_1.asm': 'common_1.asm'}

class ExperienceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for destination, source in FIXTURES.items():
            p = self.root / destination
            p.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(Path(__file__).parent / 'fixtures' / source, p)

    def snapshot(self):
        return {name: (self.root / name).read_bytes() for name in FIXTURES}

    def test_complete_application_and_reapplication_cannot_partially_write(self):
        original = self.snapshot()
        apply(self.root)
        modified = self.snapshot()
        self.assertTrue(all(original[n] != modified[n] for n in original))
        with self.assertRaises(ValueError):
            apply(self.root)
        self.assertEqual(self.snapshot(), modified)

    def test_changed_upstream_is_rejected_before_any_file_changes(self):
        target = self.root / 'data/text/common_1.asm'
        target.write_text(target.read_text().replace('wStringBuffer2, 2, 4', 'wStringBuffer2, 2, 5', 1))
        before = self.snapshot()
        with self.assertRaises(ValueError):
            apply(self.root)
        self.assertEqual(self.snapshot(), before)

    def test_dry_run_shows_all_changes_without_mutation(self):
        before, output = self.snapshot(), io.StringIO()
        with redirect_stdout(output):
            apply(self.root, True)
        self.assertEqual(self.snapshot(), before)
        for name in FIXTURES:
            self.assertIn('+++ b/' + name, output.getvalue())

    def test_existing_options_allocation_and_handlers_are_preserved(self):
        source = (self.root / 'ram/wram.asm').read_text()
        modified = patch_ram(source)
        self.assertEqual(modified.split('wOptions2::')[0], source.split('wOptions2::')[0])
        old_tail = source.split('wOptions2::')[1]
        new_tail = modified.split('wOptions2::')[1]
        def allocated(tail):
            return sum(1 if line.strip() == 'db' or line.strip().endswith(':: db') else int(line.split()[1])
                       if line.strip().startswith('ds ') else 0 for line in tail.splitlines())
        self.assertEqual(allocated(old_tail), allocated(new_tail))
        source = (self.root / 'engine/menus/options_menu.asm').read_text()
        modified = patch_options(source)
        for name in ('TextSpeed', 'BattleScene', 'BattleStyle', 'Sound', 'Print', 'MenuAccount', 'Cancel'):
            body = source.split('Options_' + name + ':', 1)[1].split('\n\n', 1)[0]
            self.assertIn('Options_' + name + ':' + body, modified)

if __name__ == '__main__':
    unittest.main()
