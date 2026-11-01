"""Verify map identity, entrance placement and an empty, navigable cave shell."""
from contextlib import redirect_stdout
from collections import deque
import io
from pathlib import Path
import re
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'build-tools'))
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from patch_new_bark_cave import apply, cave_blocks, WIDTH, HEIGHT, ENTRANCE_X, ENTRANCE_Y, EXIT_X, EXIT_Y
F=Path(__file__).parent/'fixtures'

class CaveTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)
        assets={'constants/map_constants.asm':(F/'cave_map_constants.asm').read_text(),
                'data/maps/maps.asm':(F/'cave_map_headers.asm').read_text(),
                'maps/Route29.asm':(F/'cave_route29.asm').read_text(),
                'data/maps/attributes.asm':'\tmap_attributes Route29, ROUTE_29, $05\n',
                'data/maps/blocks.asm':'SECTION "Original Blocks", ROMX\nENDSECTION\n',
                'data/maps/scripts.asm':'SECTION "Original Scripts", ROMX\nENDSECTION\n',
                'data/wild/johto_grass.asm':'existing encounters\n',
                'ram/wram.asm':'unchanged WRAM\n','ram/sram.asm':'unchanged SRAM\n',
                'constants/event_flags.asm':'unchanged event flags\n'}
        for name,text in assets.items():
            p=self.root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(text)
        (self.root/'maps/Route29.blk').write_bytes(bytes.fromhex((F/'cave_route29.hex').read_text()))
    def snapshot(self):return {str(p.relative_to(self.root)):p.read_bytes() for p in self.root.rglob('*') if p.is_file()}
    def test_all_existing_map_ids_and_unrelated_save_encounter_data_are_preserved(self):
        before=self.snapshot();apply(self.root);after=self.snapshot()
        def ids(src):
            group,index=0,1;result={}
            for line in src.splitlines():
                text=line.strip()
                if text.startswith('newgroup '):group+=1;index=1
                if text.startswith('map_const '):result[text.split()[1].rstrip(',')]=(group,index);index+=1
            return result
        old=ids(before['constants/map_constants.asm'].decode());new=ids(after['constants/map_constants.asm'].decode())
        for name,value in old.items():self.assertEqual(new[name],value)
        self.assertEqual(new['NEW_BARK_CAVE'],(24,14));self.assertEqual(len(new),len(old)+1)
        for path in ['data/wild/johto_grass.asm','ram/wram.asm','ram/sram.asm','constants/event_flags.asm']:
            self.assertEqual(before[path],after[path])
    def test_entrance_changes_only_one_previously_blocked_block_and_appends_warp(self):
        before=self.snapshot();apply(self.root)
        old=before['maps/Route29.blk'];new=(self.root/'maps/Route29.blk').read_bytes()
        expected=ENTRANCE_Y//2*30+ENTRANCE_X//2
        self.assertEqual([i for i,(a,b) in enumerate(zip(old,new)) if a!=b],[expected])
        self.assertEqual((old[expected],new[expected]),(0x05,0x73))
        source=(self.root/'maps/Route29.asm').read_text()
        addition='\n\twarp_event 52,  5, NEW_BARK_CAVE, 1'
        self.assertEqual(source.replace(addition,''),before['maps/Route29.asm'].decode())
        self.assertIn('warp_event 9, 15, ROUTE_29, 2',(self.root/'maps/NewBarkCave.asm').read_text())
        # The immediate approach from Route 29's east-end road is all floor.
        coll=[line.split('tilecoll ',1)[1].split(';')[0].strip().split(', ') for line in (F/'cave_johto_collision.asm').read_text().splitlines() if 'tilecoll ' in line]
        for x,y in [(x,8) for x in range(52,60)]+[(52,6),(52,7)]:
            self.assertEqual(coll[new[y//2*30+x//2]][(y%2)*2+x%2],'FLOOR')
    def test_whole_open_floor_is_connected_to_exit_without_water_hms_or_other_warps(self):
        blocks=cave_blocks();self.assertEqual(len(blocks),WIDTH*HEIGHT)
        collision=[line.split('tilecoll ',1)[1].split(';')[0].strip().split(', ') for line in (F/'cave_collision.asm').read_text().splitlines() if 'tilecoll ' in line]
        grid={(x,y):collision[blocks[y//2*WIDTH+x//2]][y%2*2+x%2] for y in range(HEIGHT*2) for x in range(WIDTH*2)}
        allowed={p for p,c in grid.items() if c in ('FLOOR','WARP_CARPET_DOWN')}
        seen={(EXIT_X,EXIT_Y)};queue=deque(seen)
        while queue:
            x,y=queue.popleft()
            for q in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
                if q in allowed and q not in seen:seen.add(q);queue.append(q)
        self.assertEqual(seen,allowed);self.assertGreater(len(allowed),220)
        self.assertEqual([p for p,c in grid.items() if 'WARP' in c],[(EXIT_X,EXIT_Y)])
        for p in [(1,1),(18,1),(1,14),(18,14)]:self.assertIn(p,seen)
        self.assertFalse(any(c in ('WATER','LADDER','PIT','TALL_GRASS') for c in grid.values()))
    def test_cave_is_lit_and_has_no_added_content(self):
        apply(self.root)
        self.assertIn('TILESET_CAVE, CAVE, LANDMARK_ROUTE_29, MUSIC_UNION_CAVE, TRUE, PALETTE_DAY', (self.root/'data/maps/maps.asm').read_text())
        source=(self.root/'maps/NewBarkCave.asm').read_text()
        self.assertEqual(source.count('warp_event '),1)
        for instruction in ('object_event ','bg_event ','coord_event ','scene_script ','callback ','loadwildmon ','trainer '):self.assertNotIn(instruction,source)
    def test_reapplication_and_changed_site_cannot_partially_write(self):
        apply(self.root);before=self.snapshot()
        with self.assertRaises(ValueError):apply(self.root)
        self.assertEqual(before,self.snapshot())
    def test_changed_entrance_site_and_dry_run_do_not_mutate(self):
        before=self.snapshot();capture=io.StringIO()
        with redirect_stdout(capture):apply(self.root,True)
        self.assertEqual(before,self.snapshot());self.assertIn('NewBarkCave',capture.getvalue())
        p=self.root/'maps/Route29.blk';data=bytearray(p.read_bytes());data[86]=0;p.write_bytes(data);before=self.snapshot()
        with self.assertRaises(ValueError):apply(self.root)
        self.assertEqual(before,self.snapshot())

if __name__=='__main__':unittest.main()
