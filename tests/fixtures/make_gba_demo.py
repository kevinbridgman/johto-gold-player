"""Self-authored GBA test ROM: L/R change color and persist a byte in SRAM."""
from pathlib import Path
import struct,sys
base=0xc0;code=[];labels={};fixups=[];literals=[]
def emit(v):code.append(v)
def label(n):labels[n]=base+len(code)*4
def load(reg,value,cond=14):
 fixups.append((len(code),reg,value,cond));emit(0)
def branch(name,cond=14):
 fixups.append((len(code),'branch',name,cond));emit(0)
def imm(v):
 for rot in range(16):
  x=((v<<(2*rot))|(v>>(32-2*rot if rot else 32)))&0xffffffff
  if x<256:return (rot<<8)|x
 raise ValueError(v)
load(0,0x04000000);load(1,0x0403);emit(0xe1c010b0)
label('main');load(3,0x0e000000);emit(0xe5d31000);load(4,0x03e0)
emit(0xe351004c);load(4,0x7c00,0);emit(0xe3510052);load(4,0x001f,0)
load(0,0x04000130);emit(0xe1d010b0)
emit(0xe3110000|imm(0x200));emit(0x03a0204c);emit(0x05c32000)
emit(0xe3110000|imm(0x100));emit(0x03a02052);emit(0x05c32000)
load(0,0x06000000);load(2,38400);label('draw')
emit(0xe0c040b2);emit(0xe2522001);branch('draw',1);branch('main')
for i,reg,val,cond in fixups:
 if reg=='branch':code[i]=(cond<<28)|0x0a000000|(((labels[val]-(base+i*4+8))//4)&0xffffff)
 else:
  pos=base+len(code)*4;offset=pos-(base+i*4+8);assert 0<=offset<4096
  code[i]=(cond<<28)|0x059f0000|(reg<<12)|offset;code.append(val)
rom=bytearray(32768);struct.pack_into('<I',rom,0,0xea00002e)
rom[0xa0:0xac]=b'GBA SELFTEST ';rom[0xac:0xb0]=b'TEST';rom[0xb0:0xb2]=b'00';rom[0xb2]=0x96
rom[0xbd]=(-sum(rom[0xa0:0xbd])-0x19)&255
for i,v in enumerate(code):struct.pack_into('<I',rom,base+i*4,v)
rom[0x400:0x409]=b'SRAM_V113'
Path(sys.argv[1] if len(sys.argv)>1 else 'selftest.gba').write_bytes(rom)
print('Created original 32 KiB GBA validation ROM')
