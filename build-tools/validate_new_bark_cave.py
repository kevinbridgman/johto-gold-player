#!/usr/bin/env python3
"""Check compiled cave pointers, warps, daylight and empty encounter data."""
import argparse
from pathlib import Path
from collections import deque
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('rom',type=Path)
args=parser.parse_args()
rom=args.rom.read_bytes()
symbols={}
for line in args.rom.with_suffix('.sym').read_text().splitlines():
    parts=line.split(' ',1)
    if len(parts)!=2 or ':' not in parts[0]:continue
    bank,addr=parts[0].split(':');symbols[parts[1]]=(int(bank,16),int(addr,16))
def read(name,size):
    bank,addr=symbols[name];offset=bank*0x4000+(addr%0x4000)
    return rom[offset:offset+size]
def pointer(name):return symbols[name][1].to_bytes(2,'little')
header=read('MapGroup_NewBark',14*9)[13*9:]
assert header[0]==symbols['NewBarkCave_MapAttributes'][0]
assert header[2]==4, 'CAVE environment'
assert header[3:5]==pointer('NewBarkCave_MapAttributes')
assert header[7]&15==1, 'PALETTE_DAY, no Flash'
attr=read('NewBarkCave_MapAttributes',12)
assert attr[:3]==bytes([1,8,10])
assert attr[3]==symbols['NewBarkCave_Blocks'][0]
assert attr[4:6]==pointer('NewBarkCave_Blocks')
assert attr[6]==symbols['NewBarkCave_MapScripts'][0]
assert attr[7:9]==pointer('NewBarkCave_MapScripts')
assert attr[9:11]==pointer('NewBarkCave_MapEvents')
assert attr[11]==0, 'no outside map connections'
assert read('NewBarkCave_MapScripts',2)==bytes([0,0]), 'no scenes/callbacks'
shop='CaveSupplyMart_MapScripts' in symbols
events=read('NewBarkCave_MapEvents',8)
village='CaveLodge_MapScripts' in symbols
wide_exit=shop and read('NewBarkCave_MapEvents',3)[2]>=3
assert events[:3]==bytes([0,0,5 if village else 3 if wide_exit else 2 if shop else 1])
if wide_exit:assert read('NewBarkCave_MapEvents',18)[13:18]==bytes([15,8,2,24,3])
assert events[3:8]==bytes([15,9,2,24,3]), 'original cave exit preserved'
if not shop:assert read('NewBarkCave_MapEvents',11)==bytes([0,0,1,15,9,2,24,3,0,0,0])
route=read('Route29_MapEvents',13)
assert route[:3]==bytes([0,0,2])
assert route[3:8]==bytes([1,27,3,24,13]), 'original gate warp preserved'
assert route[8:13]==bytes([5,52,1,24,14]), 'new entrance is warp 2'
blocks=read('NewBarkCave_Blocks',80)
coll=read('TilesetCaveTownColl' if shop else 'TilesetCaveColl',256*4)
# Use the actual compiled known floor/exit blocks so decoding stays
# anchored to the ROM collision table.
floor=coll[2*4]
exit_collision=coll[0x24*4+3]
if wide_exit:assert coll[0x24*4+2]==exit_collision, "both exit tiles must warp south"
grid={(x,y):coll[blocks[y//2*10+x//2]*4+y%2*2+x%2] for y in range(16) for x in range(20)}
walkable={p for p,c in grid.items() if c in (floor,exit_collision,coll[3*4])}
seen={(9,15)};queue=deque(seen)
while queue:
    x,y=queue.popleft()
    for p in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
        if p in walkable and p not in seen:seen.add(p);queue.append(p)
assert walkable==seen and len(seen)>(170 if village else 210)
for p in [(1,1),(18,1),(1,14),(18,14)]:assert p in seen
wild=read('JohtoGrassWildMons',0x4000-(symbols['JohtoGrassWildMons'][1]%0x4000))
for i in range(0,len(wild),47):
    if wild[i]==255:break
    assert wild[i:i+2]!=bytes([24,14]), 'cave has no wild encounters'
else:raise AssertionError('Encounter table terminator not found')
print('Compiled New Bark Cave: lit, connected floor, paired warps and original gate preserved'+(' with northwest shop' if shop else ', empty'))
