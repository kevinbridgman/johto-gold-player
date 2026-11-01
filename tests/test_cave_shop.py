"""Check safe generation, isolated shop changes and room for future buildings."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'build-tools'))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from patch_cave_shop import apply, HMS, GEAR
F=Path(__file__).parent/'fixtures/shop_inputs.json'
class ShopTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
  for name,value in json.loads(F.read_text()).items():
   p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True)
   p.write_bytes(value['text'].encode() if isinstance(value,dict) else bytes.fromhex(value))
 def snapshot(self):return {str(p.relative_to(self.root)):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
 def test_small_northwest_plot_preserves_center_exit_and_original_art(self):
  before=self.snapshot();apply(self.root);after=self.snapshot()
  original=before['maps/NewBarkCave.blk'];room=after['maps/NewBarkCave.blk']
  self.assertEqual([i for i,(a,b) in enumerate(zip(original,room)) if a!=b],[11,12,21,22])
  self.assertEqual(room[7*10+4],original[7*10+4])
  self.assertEqual(after['data/tilesets/cave_metatiles.bin'],before['data/tilesets/cave_metatiles.bin'])
  self.assertEqual(after['gfx/tilesets/cave.2bpp'],before['gfx/tilesets/cave.2bpp'])
  meta=after['data/tilesets/cave_town_metatiles.bin']
  self.assertLess(max(meta[64*16:]),96)
  for block in set(original)|{1}:
   self.assertEqual(meta[block*16:block*16+16],before['data/tilesets/cave_metatiles.bin'][block*16:block*16+16])
 def test_stock_fits_native_mart_buffers_and_has_every_hm(self):
  self.assertEqual(len(HMS),7);self.assertEqual(len(GEAR),10)
  self.assertIn('MASTER_BALL',GEAR);self.assertIn('POTION',GEAR)
  apply(self.root)
  src=(self.root/'data/items/marts.asm').read_text()
  for item in HMS+GEAR:self.assertIn('\tdb '+item+'\n',src)
  self.assertIn('MART_CAVE_HMS',(self.root/'maps/CaveSupplyMart.asm').read_text())
  self.assertIn('MART_CAVE_GEAR',(self.root/'maps/CaveSupplyMart.asm').read_text())
 def test_unique_new_ids_are_appended_and_existing_cave_warp_remains(self):
  before=self.snapshot();apply(self.root)
  new=(self.root/'constants/map_constants.asm').read_text()
  insertion='\tmap_const CAVE_SUPPLY_MART,                            6,  4 ; 15\n'
  self.assertEqual(new.replace(insertion,''),before['constants/map_constants.asm'].decode())
  source=(self.root/'maps/NewBarkCave.asm').read_text()
  self.assertIn('warp_event 9, 15, ROUTE_29, 2',source)
  self.assertIn('warp_event 3, 5, CAVE_SUPPLY_MART, 1',source)
  shop=(self.root/'maps/CaveSupplyMart.asm').read_text()
  self.assertEqual(shop.count('object_event '),2)
  self.assertIn('object_event 3, 1,',shop);self.assertIn('object_event 8, 1,',shop)
 def test_price_override_is_map_scoped_and_does_not_change_item_data(self):
  before=self.snapshot();apply(self.root)
  src=(self.root/'engine/items/items.asm').read_text()
  self.assertIn('cp GROUP_CAVE_SUPPLY_MART',src);self.assertIn('cp MAP_CAVE_SUPPLY_MART',src)
  self.assertTrue(src.endswith(before['engine/items/items.asm'].decode().split('\tpush bc',1)[1]))
  self.assertFalse((self.root/'ram/wram.asm').exists());self.assertFalse((self.root/'ram/sram.asm').exists())
 def test_reapplication_and_incompatible_sources_leave_files_intact(self):
  apply(self.root);before=self.snapshot()
  with self.assertRaises(ValueError):apply(self.root)
  self.assertEqual(self.snapshot(),before)
 def test_all_source_validation_precedes_asset_writes(self):
  p=self.root/'engine/items/items.asm';p.write_text('different upstream price routine\n');before=self.snapshot()
  with self.assertRaises(ValueError):apply(self.root)
  self.assertEqual(self.snapshot(),before)
if __name__=='__main__':unittest.main()
