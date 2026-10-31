from pyboy import PyBoy
from pathlib import Path
import random, io
import argparse
parser=argparse.ArgumentParser(description='Validate compiled experience math and option controls in PyBoy')
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

cases=0
random.seed(7)
for setting in [*range(10),10,15,255]:
    for base in [0,1,7,49,100,255,1000,6553,6554,12291,65535,*[random.randrange(65536) for _ in range(12)]]:
        write('wExpMultiplier',setting)
        write('hProduct',[0,0,base>>8,base&255])
        p.register_file.B=0x12;p.register_file.C=0x34
        call('ApplyExpMultiplier')
        expected=base*(setting+1 if setting<10 else 1)
        assert int.from_bytes(bytes(read('hProduct',4)),'big')==expected,(setting,base,read('hProduct',4),expected)
        assert (p.register_file.B,p.register_file.C)==(0x12,0x34)
        cases+=1
print('Native multiplier cases passed:',cases,flush=True)
for setting in range(10):
    for key,expected in [(0,setting),(16,(setting+1)%10),(32,(setting-1)%10)]:
        write('wExpMultiplier',setting);write('hJoyPressed',key)
        call('Options_Experience')
        assert read('wExpMultiplier')==expected,(setting,key,read('wExpMultiplier'))
for value in [10,15,255]:
    write('wExpMultiplier',value);write('hJoyPressed',0);call('Options_Experience')
    assert read('wExpMultiplier')==0
print('Native option cycling, wrap, and invalid settings passed',flush=True)
# Suppress presentation/level-up work only for isolated award-path tests.
# The actual GiveExperiencePoints routine still calculates bonuses and writes
# the party's three experience bytes.
def override(name, data):
    bank,addr=sym[name]
    for i,b in enumerate(data):p.memory[bank,addr+i]=b
for name in ['PrintText','AnimateExpBar','ResetBattleParticipants']:
    override(name,[0xc9])
override('CalcLevel',[0x16,90,0xc9]) # LD D,90 / RET
awards=0
for setting in [0,1,4,9]:
 for trainer in [False,True]:
  for traded in [False,True]:
   for lucky in [False,True]:
    write('wExpMultiplier',setting)
    write('wPartyCount',1);write('wPartySpecies',[19,255]);write('wPartyMon1Species',19)
    write('wPartyMon1Level',90);write('wPartyMon1HP',[0,100])
    write('wPartyMon1Exp',[0,0,0]);write('wPartyMon1ID',[0x12,0x35 if traded else 0x34])
    write('wPlayerID',[0x12,0x34]);write('wPartyMon1Item',126 if lucky else 0)
    write('wBattleMode',2 if trainer else 1);write('wLinkMode',0)
    write('wBattleParticipantsNotFainted',1);write('wCurBattleMon',0)
    write('wEnemyMonBaseStats',[10,20,30,40,50]);write('wPartyMon1StatExp',bytes(10));write('wPartyMon1PokerusStatus',0)
    write('wEnemyMonBaseExp',255);write('wEnemyMonLevel',100)
    call('GiveExperiencePoints')
    expected=255*100//7
    for bonus in [traded,trainer,lucky]:
        if bonus:expected=expected+expected//2
    expected*=setting+1
    actual=int.from_bytes(bytes(read('wPartyMon1Exp',3)),'big')
    assert actual==expected,(setting,trainer,traded,lucky,actual,expected)
    assert int.from_bytes(bytes(read('wStringBuffer2',3)),'big')==expected
    assert read('wStringBuffer2',4)[3]==int(traded)
    assert read('wPartyMon1StatExp',10)==[0,10,0,20,0,30,0,40,0,50]
    awards+=1
print('Native full award path passed:',awards,'bonus combinations (including >65535 EXP)',flush=True)
# Shared recipient path: participants and EXP SHARE recipients both use this routine.
for sharing in [0,1]:
    write('wGivingExperienceToExpShareHolders',sharing)
    write('wExpMultiplier',9);write('wBattleMode',1);write('wPartyMon1Item',0)
    write('wPartyMon1ID',[0x12,0x34]);write('wEnemyMonBaseExp',63);write('wEnemyMonLevel',10)
    write('wPartyMon1Exp',[0,0,0]);write('wBattleParticipantsNotFainted',1)
    call('GiveExperiencePoints')
    assert int.from_bytes(bytes(read('wPartyMon1Exp',3)),'big')==900
# Fainted or linked Pokemon must not receive modified experience.
for linked,fainted in [(1,False),(0,True)]:
    write('wLinkMode',linked);write('wPartyMon1HP',[0,0 if fainted else 100])
    write('wPartyMon1Exp',[0,0,123]);write('wBattleParticipantsNotFainted',1)
    call('GiveExperiencePoints')
    assert read('wPartyMon1Exp',3)==[0,0,123]
print('EXP SHARE common path, fainted/link exclusions, and unchanged stat EXP passed',flush=True)
p.stop(save=False)
