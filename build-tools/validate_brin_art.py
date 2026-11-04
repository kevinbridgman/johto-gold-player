#!/usr/bin/env python3
"""Check compiled native art and guard its use to Coach Brin's three teams."""
from pathlib import Path
import argparse,io,json
from pyboy import PyBoy
ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('rom',type=Path);args=ap.parse_args();rom=args.rom.read_bytes();sym={}
for line in args.rom.with_suffix('.sym').read_text().splitlines():
 q=line.split(' ',1)
 if len(q)!=2 or ':' not in q[0]:continue
 b,a=q[0].split(':');sym[q[1]]=(int(b,16),int(a,16))
def raw(name,n):
 b,a=sym[name];off=b*0x4000+a%0x4000;return rom[off:off+n]
art=json.loads(Path(__file__).with_name('brin_art.json').read_text())
assert raw('CaveBrinSpriteGFX',384)==bytes(art['overworld'])
encoded=raw('CaveBrinPic',900);decoded=bytearray();i=0
while encoded[i]!=255:
 n=encoded[i]+1;assert n<=32;decoded.extend(encoded[i+1:i+1+n]);i+=n+1
assert decoded==bytes(art['portrait']) and len(decoded)==56*56//4
assert sym['CaveBrinPic'][0]==0x7e,'safe physical pic bank, no alias fixups'
entry=raw('OverworldSprites',96*6)[95*6:96*6]
assert entry[:2]==sym['CaveBrinSpriteGFX'][1].to_bytes(2,'little')
assert entry[3]==sym['CaveBrinSpriteGFX'][0]
p=PyBoy(str(args.rom),window='null',sound_emulated=False,ram_file=io.BytesIO(bytes(32768)))
p.set_emulation_speed(0);p.tick(500,False);p.memory[0xff70]=1

def write(name,v):p.memory[sym[name][1]]=v
def call(name):
 bank,addr=sym[name];write('hROMBank',bank)
 stub=[0xf3,0xf5,0x3e,bank,0xea,0,0x20,0xf1,0xcd,addr&255,addr>>8,0x3e,0xa5,0xea,0,0xc0,0x18,0xfe]
 for i,b in enumerate(stub):p.memory[0,0x3f00+i]=b
 p.memory[0xc000]=0;p.memory[0xffff]=0;p.memory[0xff0f]=0
 p.register_file.SP=0xdff0;p.register_file.PC=0x3f00
 for _ in range(20):
  p.tick(1,False)
  if p.memory[0xc000]==0xa5:break
 assert p.memory[0xc000]==0xa5,name

def hl():return p.register_file.HL
cases=0
for group,number in [(24,17),(24,16),(24,14),(26,3)]:
 for trainerid in [1,12,13,14,15,16]:
  for cls in [1,22,23]:
   write('wMapGroup',group);write('wMapNumber',number);write('wOtherTrainerID',trainerid);write('wTrainerClass',cls)
   brin=(group,number)==(24,17) and cls==22 and 13<=trainerid<=15
   call('GetTrainerPic.GetPicPointer')
   expected=sym['CaveBrinPicPointer'][1] if brin else sym['TrainerPicPointers'][1]+(cls-1)*3
   assert hl()==expected,('portrait guard',group,number,trainerid,cls,hl(),expected)
   p.register_file.A=cls;call('GetTrainerPalettePointer')
   expected=sym['CaveBrinPalette'][1] if brin else sym['TrainerPalettes'][1]+cls*4
   assert hl()==expected,('palette guard',group,number,trainerid,cls)
   p.register_file.C=cls;call('GetTrainerClassName')
   a=sym['wStringBuffer1'][1];name=list(p.memory[a:a+6])
   assert (name==[0x82,0x8e,0x80,0x82,0x87,0x50])==brin,('title guard',group,number,trainerid,cls,name)
   expected_name=name[:name.index(0x50)] if 0x50 in name else None
   # The battle introduction uses GetOTName's class buffer, not only GetTrainerClassName.
   a=sym['wStringBuffer1'][1];full=list(p.memory[a:a+20]);expected_name=full[:full.index(0x50)]
   p.register_file.C=cls;call('GetOTName')
   a=sym['wOTClassName'][1];full=list(p.memory[a:a+20])
   assert full[:full.index(0x50)]==expected_name, 'battle class title'
   cases+=1
# Player palette remains unchanged even with a recent Brin encounter.
write('wMapGroup',24);write('wMapNumber',17);write('wOtherTrainerID',13);p.register_file.A=0;call('GetTrainerPalettePointer')
assert hl()==sym['TrainerPalettes'][1]
p.stop(save=False)
print(f'Native Brin art: 16x16 six-frame sprite, 56x56 portrait, palette/title and {cases} scope cases passed; player/other trainers unchanged')
