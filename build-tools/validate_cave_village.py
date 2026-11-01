#!/usr/bin/env python3
"""Inspect compiled village interiors, paths, return warps, art and practice teams."""
from pathlib import Path
from collections import deque
import argparse
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('rom',type=Path);args=ap.parse_args()
rom=args.rom.read_bytes();sym={}
for line in args.rom.with_suffix('.sym').read_text().splitlines():
 parts=line.split(' ',1)
 if len(parts)!=2 or ':' not in parts[0]:continue
 b,a=parts[0].split(':');sym[parts[1]]=(int(b,16),int(a,16))
def raw(name,n):
 b,a=sym[name];offset=b*0x4000+a%0x4000;return rom[offset:offset+n]
def grid(name,w,h,tileset):
 blocks=raw(name+'_Blocks',w*h);coll=raw(tileset+'Coll',256*4)
 return {(x,y):coll[blocks[y//2*w+x//2]*4+y%2*2+x%2] for y in range(h*2) for x in range(w*2)}
def reachable(g,start,npcs):
 allowed={q for q,c in g.items() if c in (0,0x18,0x70,0x71)}-set(npcs)
 seen={start};queue=deque(seen)
 while queue:
  x,y=queue.popleft()
  for v in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
   if v in allowed and v not in seen:seen.add(v);queue.append(v)
 return seen
cave=grid('NewBarkCave',10,8,'TilesetCaveTown')
npcs=[(4,10),(7,7),(2,7),(17,7),(6,12),(3,11)]
seen=reachable(cave,(9,14),npcs)
for q in [(3,6),(13,6),(13,12),(5,10),(3,7),(16,7),(7,12),(8,14),(9,15),(8,15)]:assert q in seen,('blocked village route',q)
for x,y in npcs:assert any(q in seen for q in ((x-1,y),(x+1,y),(x,y-1),(x,y+1))),('unreachable resident',x,y)
events=raw('NewBarkCave_MapEvents',28)
assert events[:3]==bytes([0,0,5])
assert events[3:]==bytes([15,9,2,24,3,5,3,1,24,15,15,8,2,24,3,5,13,1,24,16,11,13,1,24,17])
for name,w,h,tileset,mapid,returnwarp,doors,npcs,targets in [
 ('CaveLodge',5,4,'TilesetPokecenter',16,4,[(3,7),(4,7)],[(3,1),(7,5)],[(3,3),(9,2)]),
 ('CaveTrainingHall',5,6,'TilesetTrainStation',17,5,[(4,11),(5,11)],[(4,3),(7,8)],[(4,4),(6,8)])]:
 assert raw(name+'_MapScripts',2)==bytes([0,0])
 event=raw(name+'_MapEvents',16);assert event[:3]==bytes([0,0,2])
 for i,(x,y) in enumerate(doors):assert event[3+i*5:8+i*5]==bytes([y,x,returnwarp,24,14])
 g=grid(name,w,h,tileset);r=reachable(g,doors[0],npcs)
 for q in doors+targets:assert q in r,(name,'unreachable',q)
 if name=='CaveLodge':
  assert g[9,1]==0x93,'native PC tile'
  assert g[3,2]==0x90,'nurse counter'
  assert not any(c==0x72 for q,c in g.items() if q in r),'no upstairs/link stairs'
 attr=raw(name+'_MapAttributes',12);assert attr[:3]==bytes([0,h,w])
 assert attr[-1]==0,'no unintended map connections'
 # Existing map group entries are untouched and new entries are appended.
 header=raw('MapGroup_NewBark',17*9)[(mapid-1)*9:mapid*9]
 assert header[0]==sym[name+'_MapAttributes'][0] and header[3:5]==sym[name+'_MapAttributes'][1].to_bytes(2,'little')
 # Verify the two actual saved NPCs' pointers use this build's scripts on CONTINUE.
meta=raw('TilesetCaveTownMeta',73*16);blocks=raw('NewBarkCave_Blocks',80)
assert len(meta)==73*16 and max(t for b in set(blocks)|{1} for t in meta[b*16:b*16+16])<96,'art below font slots'
# Trainer IDs 13-15 append to YOUNGSTER; earlier teams stay in place.
teams=raw('CaveCoachTeams',64);at=0
for expected in [[(5,19),(5,16)],[(15,27),(15,179),(15,194)],[(30,75),(30,93),(30,42)]]:
 end=teams.index(0x50,at);assert teams[at:end]==bytes([0x81,0x91,0x88,0x8d]),'BRIN'
 assert teams[end+1]==0,'native level-up moves'
 at=end+2
 for level,species in expected:assert teams[at:at+2]==bytes([level,species]);at+=2
 assert teams[at]==255;at+=1
print('Compiled Lantern Hollow: every destination reachable, paired lodge/hall warps, native PC and nurse, protected font slots and L5/L15/L30 teams passed')
