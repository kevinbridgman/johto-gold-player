#!/usr/bin/env python3
"""Make the cave's south exit visibly marked and usable across both tiles."""
import argparse
from pathlib import Path
from patch_cave_shop import literal_lz, palette

def apply(repo,dry_run=False):
 changes={}
 p='maps/NewBarkCave.asm';s=(repo/p).read_text()
 old='\twarp_event 3, 5, CAVE_SUPPLY_MART, 1'
 if s.count(old)!=1 or '\twarp_event 8, 15,' in s:raise ValueError('Unexpected or already updated cave warps')
 changes[p]=(s.replace(old,old+'\n\twarp_event 8, 15, ROUTE_29, 2',1)).encode()
 p='data/tilesets/cave_town_collision.asm';s=(repo/p).read_text()
 old='\ttilecoll FLOOR, FLOOR, FLOOR, WARP_CARPET_DOWN ; 24'
 if s.count(old)!=1:raise ValueError('Unexpected exit collision')
 changes[p]=s.replace(old,'\ttilecoll FLOOR, FLOOR, WARP_CARPET_DOWN, WARP_CARPET_DOWN ; 24').encode()
 # Reuse Gold's existing downward staircase art in both lower quadrants.
 # Only the cave-specific tileset changes; original caves remain untouched.
 p='data/tilesets/cave_town_metatiles.bin';meta=bytearray((repo/p).read_bytes())
 stairs=meta[0x0b*16:0x0c*16]
 room=(repo/'maps/NewBarkCave.blk').read_bytes()
 used={t for b in set(room)|{1} for t in meta[b*16:b*16+16]}|{0x14,0x40}
 originals=sorted({stairs[row*4+col] for row in (2,3) for col in (2,3)})
 free=[t for t in range(96) if t not in used]
 if len(free)<len(originals):raise ValueError('No room for exit art below font slots')
 remap=dict(zip(originals,free))
 encoded=(repo/'gfx/tilesets/cave_town.lz').read_bytes();gfx=bytearray();i=0
 while encoded[i]!=255:
  count=encoded[i]+1
  if count>32:raise ValueError('Expected literal cave art')
  gfx.extend(encoded[i+1:i+1+count]);i+=1+count
 original=(repo/'gfx/tilesets/cave.2bpp').read_bytes()
 colors=palette((repo/'gfx/tilesets/cave_town_palette_map.asm').read_text())
 original_colors=palette((repo/'gfx/tilesets/cave_palette_map.asm').read_text())
 for old,new in remap.items():
  gfx[new*16:new*16+16]=original[old*16:old*16+16];colors[new]=original_colors[old]
 changes['gfx/tilesets/cave_town.lz']=literal_lz(bytes(gfx))
 changes['gfx/tilesets/cave_town_palette_map.asm']=('\n'.join('\ttilepal 0, '+', '.join(colors[i:i+8]) for i in range(0,96,8))+'\n').encode()
 block=bytearray(meta[0x24*16:0x25*16])
 for row in (2,3):
  for col in range(4):block[row*4+col]=remap[stairs[row*4+2+col%2]]
 meta[0x24*16:0x25*16]=block;changes[p]=bytes(meta)
 for path,data in changes.items():
  if not dry_run:(repo/path).write_bytes(data)
 return changes
if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('repo',type=Path);ap.add_argument('--dry-run',action='store_true');a=ap.parse_args();apply(a.repo,a.dry_run)
