#!/usr/bin/env python3
"""Give only Lantern Hollow's Coach Brin original overworld/battle artwork."""
import argparse,json
from pathlib import Path
from patch_cave_shop import once,literal_lz

CHECK='''\tld a, [wMapGroup]
\tcp GROUP_CAVE_TRAINING_HALL
\tjr nz, .Ordinary
\tld a, [wMapNumber]
\tcp MAP_CAVE_TRAINING_HALL
\tjr nz, .Ordinary
\tld a, [wOtherTrainerID]
\tcp CAVE_COACH_ROOKIE
\tjr c, .Ordinary
\tcp CAVE_COACH_EXPERT + 1
\tjr nc, .Ordinary
'''

def apply(repo,dry_run=False):
 if (repo/'gfx/sprites/cave_brin.2bpp').exists():raise ValueError('Brin art already applied')
 art=json.loads((Path(__file__).with_name('brin_art.json')).read_text())
 ow=bytes(art['overworld']);pic=bytes(art['portrait'])
 if len(ow)!=384 or len(pic)!=784:raise ValueError('Unexpected native sprite dimensions')
 changes={'gfx/sprites/cave_brin.2bpp':ow,'gfx/trainers/cave_brin.2bpp.lz':literal_lz(pic)}
 def edit(path,fn):changes[path]=fn((repo/path).read_text()).encode()
 edit('constants/sprite_constants.asm',lambda s:once(s,'DEF NUM_OVERWORLD_SPRITES EQU const_value - 1','\tconst SPRITE_CAVE_BRIN ; appended, existing sprite IDs unchanged\nDEF NUM_OVERWORLD_SPRITES EQU const_value - 1'))
 edit('data/sprites/sprites.asm',lambda s:once(s,'\tassert_table_length NUM_OVERWORLD_SPRITES','\toverworld_sprite CaveBrinSpriteGFX, 12, WALKING_SPRITE, PAL_OW_BLUE\n\tassert_table_length NUM_OVERWORLD_SPRITES'))
 edit('gfx/sprites.asm',lambda s:s+'''\nSECTION "Coach Brin Original Graphics", ROMX, BANK[$7e]
CaveBrinSpriteGFX::
\tINCBIN "gfx/sprites/cave_brin.2bpp"
CaveBrinPic::
\tINCBIN "gfx/trainers/cave_brin.2bpp.lz"
''')
 edit('maps/CaveTrainingHall.asm',lambda s:once(s,'object_event 4, 3, SPRITE_YOUNGSTER, SPRITEMOVEDATA_STANDING_DOWN, 0, 0, -1, -1, PAL_NPC_RED,','object_event 4, 3, SPRITE_CAVE_BRIN, SPRITEMOVEDATA_STANDING_DOWN, 0, 0, -1, -1, PAL_NPC_BLUE,'))
 edit('data/trainers/pic_pointers.asm',lambda s:s+'\nCaveBrinPicPointer::\n\tdba_pic CaveBrinPic\n')
 def pics(s):
  old='''\tpush de
\tld hl, TrainerPicPointers
\tld a, [wTrainerClass]
\tdec a
\tld bc, 3
\tcall AddNTimes
\tld a, BANK(TrainerPicPointers)'''
  s=once(s,old,'\tpush de\n\tcall .GetPicPointer\n\tld a, BANK(TrainerPicPointers)')
  helper=''' .GetPicPointer:
'''.lstrip()+CHECK+'''\tld a, [wTrainerClass]
\tcp YOUNGSTER
\tjr nz, .Ordinary
\tld hl, CaveBrinPicPointer
\tret
.Ordinary:
\tld hl, TrainerPicPointers
\tld a, [wTrainerClass]
\tdec a
\tld bc, 3
\tjp AddNTimes

'''
  return once(s,'DecompressGet2bpp:\n',helper+'DecompressGet2bpp:\n')
 edit('engine/gfx/load_pics.asm',pics)
 edit('data/trainers/palettes.asm',lambda s:s+'\nCaveBrinPalette::\n\tRGB 25, 22, 17\n\tRGB 6, 12, 18\n')
 def palette(s):
  guard='GetTrainerPalettePointer:\n\tpush af\n'+CHECK+'''\tpop af
\tcp YOUNGSTER
\tjr nz, .Normal
\tld hl, CaveBrinPalette
\tret
.Ordinary:
\tpop af
.Normal:
'''
  return once(s,'GetTrainerPalettePointer:\n',guard)
 edit('engine/gfx/color.asm',palette)
 def title(s):
  intro='GetTrainerClassName:\n'+CHECK+'''\tld a, c
\tcp YOUNGSTER
\tjr nz, .Ordinary
\tld hl, .Coach
\tld de, wStringBuffer1
\tld bc, 6
\tcall CopyBytes
\tld de, wStringBuffer1
\tret
.Coach:
\tdb "COACH@"
.Ordinary:
'''
  s=once(s,'GetTrainerClassName:\n',intro)
  old='''\tld [wCurSpecies], a
\tld a, TRAINER_NAME
\tld [wNamedObjectType], a
\tcall GetName
\tld hl, wStringBuffer1'''
  return once(s,old,'\tcall GetTrainerClassName\n\tld hl, wStringBuffer1')
 edit('engine/battle/read_trainer_attributes.asm',title)
 for path,data in changes.items():
  if not dry_run:(repo/path).write_bytes(data)
 return changes
if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('repo',type=Path);ap.add_argument('--dry-run',action='store_true');a=ap.parse_args();apply(a.repo,a.dry_run)
