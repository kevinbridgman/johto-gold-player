import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('publisher', Path(__file__).resolve().parents[1] / 'build-tools/publish_release.py')
publisher = importlib.util.module_from_spec(spec)
spec.loader.exec_module(publisher)


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'patches').mkdir()
        self.catalog = self.root / 'patches/catalog.json'
        self.catalog.write_text(json.dumps({'schemaVersion': 1, 'patches': []}))
        self.metadata = {'id': 'johto-starters-rival', 'version': '1.0', 'name': 'Starters', 'description': 'Description', 'notes': 'Experimental'}
        self.baseline = self.root / 'baseline'
        self.baseline.write_bytes(b'original')
        self.patch = self.root / 'candidate'
        self.patch.write_bytes(b'PATCHEOF')

    def publish(self):
        (self.root / 'release.json').write_text(json.dumps(self.metadata))
        return publisher.publish(self.root, self.baseline, self.patch)

    def snapshot(self):
        return {p.name: p.read_bytes() for p in (self.root / 'patches').iterdir()}

    def test_versions_remain_selectable_and_identical_rerun_is_noop(self):
        self.assertTrue(self.publish())
        first = self.snapshot()
        self.assertFalse(self.publish())
        self.assertEqual(first, self.snapshot())
        self.metadata['version'] = '1.1'
        self.patch.write_bytes(b'PATCH\x00\x00\x01\x00\x01xEOF')
        self.assertTrue(self.publish())
        entries = json.loads(self.catalog.read_text())['patches']
        self.assertEqual([p['version'] for p in entries], ['1.1', '1.0'])
        self.assertEqual(len({p['id'] for p in entries}), 2)
        for filename, contents in first.items():
            if filename != 'catalog.json':
                self.assertEqual((self.root / 'patches' / filename).read_bytes(), contents)

    def test_changed_release_is_rejected_without_writes(self):
        self.publish()
        before = self.snapshot()
        for change in ('patch', 'baseline', 'description'):
            with self.subTest(change=change):
                old_patch, old_base = self.patch.read_bytes(), self.baseline.read_bytes()
                if change == 'patch':
                    self.patch.write_bytes(b'PATCH\x00\x00\x01\x00\x01xEOF')
                elif change == 'baseline':
                    self.baseline.write_bytes(b'other ROM')
                else:
                    self.metadata['description'] = 'Changed'
                with self.assertRaisesRegex(ValueError, 'Bump'):
                    self.publish()
                self.assertEqual(before, self.snapshot())
                self.patch.write_bytes(old_patch)
                self.baseline.write_bytes(old_base)

    def test_orphan_file_is_not_overwritten(self):
        target = self.root / 'patches/johto-starters-rival-v1.0.ips'
        target.write_bytes(b'keep me')
        before = self.snapshot()
        with self.assertRaisesRegex(ValueError, 'refusing'):
            self.publish()
        self.assertEqual(before, self.snapshot())

    def test_invalid_version_is_rejected(self):
        self.metadata['version'] = '../1.0'
        before = self.snapshot()
        with self.assertRaises(ValueError):
            self.publish()
        self.assertEqual(before, self.snapshot())
