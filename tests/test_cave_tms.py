"""All TMs, bounded catalog sizes, cancellation paths and safe source changes."""
from pathlib import Path
import json
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'build-tools'))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from patch_cave_tms import apply, tm_items, RANGES

class TMCatalogTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup);self.root=Path(self.temp.name)
  self.inputs=json.loads((Path(__file__).parent/'fixtures/tm_catalog_inputs.json').read_text())
  for path,src in self.inputs.items():
   p=self.root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(src)
 def snapshot(self):return {str(p.relative_to(self.root)):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
 def test_all_fifty_tms_are_present_once_in_five_bounded_pages(self):
  apply(self.root)
  items=tm_items(self.inputs['constants/item_constants.asm'])
  self.assertEqual(len(items),50);self.assertEqual(items[4],'TM_ROAR');self.assertEqual(items[28],'TM_PSYCHIC_M')
  stock=(self.root/'data/items/marts.asm').read_text()
  for first,last in RANGES:
   body=stock.split(f'MartCaveTMs{first:02d}:',1)[1].split('\tdb -1',1)[0]
   self.assertIn('\tdb 10\n',body)
   self.assertEqual([v.strip().removeprefix('db ') for v in body.splitlines() if v.strip().startswith('db TM_')],list(items[first-1:last]))
 def test_existing_mart_ids_hm_stock_and_gear_script_are_preserved(self):
  apply(self.root)
  old=self.inputs['constants/mart_constants.asm'];new=(self.root/'constants/mart_constants.asm').read_text()
  extra=''.join(f'\tconst MART_CAVE_TMS_{a}_{b}\n' for a,b in RANGES)
  self.assertEqual(new.replace(extra,''),old)
  old_clerk=self.inputs['maps/CaveSupplyMart.asm'].split('CaveSupplyMartGearClerk:',1)[1]
  self.assertTrue((self.root/'maps/CaveSupplyMart.asm').read_text().endswith(old_clerk))
 def test_cancel_back_and_post_purchase_return_paths_exist(self):
  apply(self.root);src=(self.root/'maps/CaveSupplyMart.asm').read_text()
  self.assertIn('ifequal 1, .HMs',src);self.assertIn('ifequal 2, .TMs',src)
  self.assertIn('\tclosetext\n\tend\n.HMs:',src)
  self.assertEqual(src.count('\tsjump .TMs\n'),5)
  self.assertIn('CaveSupplyMartTMText:\n\ttext "TMs are used once."',src)
  self.assertIn('wMap2Object + MAPOBJECT_SCRIPT_POINTER',(self.root/'data/maps/scripts.asm').read_text())
 def test_changed_or_already_patched_sources_cannot_partially_write(self):
  apply(self.root);before=self.snapshot()
  with self.assertRaises(ValueError):apply(self.root)
  self.assertEqual(before,self.snapshot())
 def test_invalid_tm_table_is_rejected_without_writes(self):
  p=self.root/'constants/item_constants.asm';p.write_text(p.read_text().replace('add_tm ROAR','add_tm HEADBUTT'))
  before=self.snapshot()
  with self.assertRaises(ValueError):apply(self.root)
  self.assertEqual(before,self.snapshot())
if __name__=='__main__':unittest.main()
