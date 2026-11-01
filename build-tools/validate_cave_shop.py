from pyboy import PyBoy
from pathlib import Path
import random, io
import argparse
parser=argparse.ArgumentParser(description='Validate compiled cave shop stock, prices, counters and old-save relocation')
parser.add_argument('rom',type=Path)
args=parser.parse_args()
rom=args.rom
sym={}
for line in rom.with_suffix('.sym').read_text().splitlines():
    if ':' not in line.split(' ')[0]:continue
    a,n=line.split(' ',1);b,a=a.split(':');sym[n]=(int(b,16),int(a,16))
p=PyBoy(str(rom),window='null',sound_emulated=False,ram_file=io.BytesIO(bytes(32768)))
p.set_emulation_speed(0);p.tick(500,False)
p.memory[0xff70]=1

def read(name,n=1):
    a=sym[name][1];return p.memory[a] if n==1 else list(p.memory[a:a+n])
def write(name,value):
    a=sym[name][1]
    if isinstance(value,int):p.memory[a]=value
    else:p.memory[a:a+len(value)]=value

def call(name):
    bank,addr=sym[name]
    write('hROMBank',bank)
    # Test-only CPU call stub. Interrupts are disabled while testing a routine.
    stub=[0xf3,0x3e,bank,0xea,0,0x20,0xcd,addr&255,addr>>8,0x3e,0xa5,0xea,0,0xc0,0x18,0xfe]
    for i,b in enumerate(stub):p.memory[0,0x3f00+i]=b
    p.memory[0xc000]=0
    p.memory[0xffff]=0;p.memory[0xff0f]=0
    p.register_file.SP=0xdff0;p.register_file.PC=0x3f00
    for _ in range(20):
        p.tick(1,False)
        if p.memory[0xc000]==0xa5:break
    assert p.memory[0xc000]==0xa5,(name,p.register_file.PC)

# Read exact compiled item lists and check scope of free prices.
def raw(name,n):
    bank,addr=sym[name];offset=bank*0x4000+addr%0x4000
    return args.rom.read_bytes()[offset:offset+n]
hms=raw('MartCaveHMs',9);gear=raw('MartCaveGear',12)
assert hms==bytes([7,*range(0xf3,0xfa),255])
assert gear[0]==10 and gear[-1]==255 and len(set(gear[1:-1]))==10
for item in [*hms[1:-1],*gear[1:-1]]:
    write('wMapGroup',24);write('wMapNumber',15);write('wCurItem',item)
    call('GetItemPrice');assert (p.register_file.D,p.register_file.E)==(0,0)
for group,number in [(24,14),(26,4)]:
    write('wMapGroup',group);write('wMapNumber',number);write('wCurItem',gear[1])
    call('GetItemPrice');assert p.register_file.D*256+p.register_file.E==300
print('Compiled stock: all 7 HMs and 10 supplies cost zero here; ordinary prices remain elsewhere',flush=True)
# Old cave saves can be anywhere in the formerly empty room.
for y in range(16):
 for x in range(20):
    write('wMapGroup',24);write('wMapNumber',14);write('wXCoord',x);write('wYCoord',y)
    call('CaveShopSafeContinue')
    expected=(3,6) if 2<=x<6 and 2<=y<6 else (x,y)
    assert (read('wXCoord'),read('wYCoord'))==expected,(x,y,expected)
    if expected!=(x,y):
        assert read('wPlayerMapX')==7 and read('wPlayerMapY')==10
write('wMapNumber',15);write('wXCoord',3);write('wYCoord',3);call('CaveShopSafeContinue')
assert (read('wXCoord'),read('wYCoord'))==(3,3)
print('All 320 old cave save positions migrate safely; shop saves are not moved',flush=True)
# Counter geometry: shoppers can reach both counters, but not the staff area.
from collections import deque
blocks=raw('CaveSupplyMart_Blocks',24);coll=raw('TilesetCaveMartColl',256*4)
grid={(x,y):coll[blocks[y//2*6+x//2]*4+y%2*2+x%2] for y in range(8) for x in range(12)}
floor=coll[0x2b*4];carpet=coll[0x2a*4+2]
allowed={q for q,c in grid.items() if c in (floor,carpet)}
seen={(2,7)};queue=deque(seen)
while queue:
 x,y=queue.popleft()
 for q in [(x-1,y),(x+1,y),(x,y-1),(x,y+1)]:
    if q in allowed and q not in seen:seen.add(q);queue.append(q)
assert (3,3) in seen and (8,3) in seen
assert (3,1) not in seen and (8,1) not in seen
counter=coll[0x0d*4]
assert grid[3,2]==grid[8,2]==counter and counter!=floor
# New graphics must fit below font tile 0x60; retain existing cave floor/walls.
meta=raw('TilesetCaveTownMeta',68*16)
assert max(meta[64*16:])<96
for b in [1,2,4,5,6,8,10,12,13,14,36]:
    assert meta[b*16:b*16+16]==raw('TilesetCaveMeta',64*16)[b*16:b*16+16]
print('Compiled shop counters, reusable cave art and protected font slots passed',flush=True)
p.stop(save=False)
