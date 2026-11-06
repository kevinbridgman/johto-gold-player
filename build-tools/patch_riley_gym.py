#!/usr/bin/env python3
"""Add Riley's accessible placeholder gym to the north of Lantern Hollow."""
import argparse
from pathlib import Path
from patch_cave_shop import once,literal_lz,palette

ROOM=bytes([0,5,5,5,0, 8,2,2,2,10, 8,2,1,2,10,
            8,2,1,2,10, 8,0x1e,1,0x1d,10, 0,0x18,3,0x18,0])
SCRIPT='''\tobject_const_def
\tconst CAVERILEYGYM_RILEY
\tconst CAVERILEYGYM_GUIDE

CaveRileyGym_MapScripts:
\tdef_scene_scripts
\tdef_callbacks

CaveRileyGymLeader:
\tjumptextfaceplayer CaveRileyGymLeaderText

CaveRileyGymGuide:
\tjumptextfaceplayer CaveRileyGymGuideText

CaveRileyGymStatue:
\tjumptext CaveRileyGymStatueText

CaveRileyGymLeaderText:
\ttext "I'm RILEY, this"
\tline "GYM's LEADER!"
\tpara "I'm getting things"
\tline "ready. Come visit"
\tcont "me again soon!"
\tdone

CaveRileyGymGuideText:
\ttext "Welcome to LANTERN"
\tline "HOLLOW's new GYM!"
\tpara "RILEY is getting"
\tline "everything ready."
\tpara "For now, come in"
\tline "and say hello!"
\tdone

CaveRileyGymStatueText:
\ttext "LANTERN HOLLOW GYM"
\tline "LEADER: RILEY"
\tdone

CaveRileyGym_MapEvents:
\tdb 0, 0
\tdef_warp_events
\twarp_event 4, 11, NEW_BARK_CAVE, 6
\twarp_event 5, 11, NEW_BARK_CAVE, 6
\tdef_coord_events
\tdef_bg_events
\tbg_event 3, 9, BGEVENT_READ, CaveRileyGymStatue
\tbg_event 6, 9, BGEVENT_READ, CaveRileyGymStatue
\tdef_object_events
\tobject_event 4, 3, SPRITE_COOLTRAINER_F, SPRITEMOVEDATA_STANDING_DOWN, 0, 0, -1, -1, PAL_NPC_RED, OBJECTTYPE_SCRIPT, 0, CaveRileyGymLeader, -1
\tobject_event 2, 7, SPRITE_GYM_GUIDE, SPRITEMOVEDATA_STANDING_RIGHT, 0, 0, -1, -1, PAL_NPC_BLUE, OBJECTTYPE_SCRIPT, 0, CaveRileyGymGuide, -1
'''
SIGN='''
CaveRileyGymSign:
\tjumptext CaveRileyGymSignText
CaveRileyGymSignText:
\ttext "LANTERN HOLLOW GYM"
\tline "LEADER: RILEY"
\tpara "Visitors welcome!"
\tdone
'''
MIGRATE='''\tld a, [wXCoord]
\tcp 6
\tjr c, .RileySign
\tcp 12
\tjr nc, .RileySign
\tld a, [wYCoord]
\tcp 4
\tjr nc, .RileySign
\tjr .RileyMove
.RileySign:
\tld a, [wXCoord]
\tcp 7
\tjr nz, .RileyClear
\tld a, [wYCoord]
\tcp 5
\tjr nz, .RileyClear
.RileyMove:
\tld a, 8
\tld [wXCoord], a
\tld a, 4
\tld [wYCoord], a
\tjp .Moved
.RileyClear:
'''

def art(repo,room):
 meta=bytearray((repo/'data/tilesets/cave_town_metatiles.bin').read_bytes())
 if len(meta)!=73*16:raise ValueError('Unexpected existing cave metatiles')
 encoded=(repo/'gfx/tilesets/cave_town.lz').read_bytes();gfx=bytearray();i=0
 while encoded[i]!=255:
  n=encoded[i]+1
  if n>32:raise ValueError('Expected literal cave art')
  gfx.extend(encoded[i+1:i+1+n]);i+=n+1
 if len(gfx)!=96*16:raise ValueError('Unexpected cave graphics length')
 colors=palette((repo/'gfx/tilesets/cave_town_palette_map.asm').read_text())
 used={t for b in set(room)|{1} for t in meta[b*16:b*16+16]}|{0x14,0x40}
 free=[t for t in range(96) if t not in used]
 jm=(repo/'data/tilesets/johto_metatiles.bin').read_bytes()
 jg=bytearray((repo/'gfx/tilesets/johto.2bpp').read_bytes())
 jg[0x0a*16:0x13*16]=(repo/'gfx/tilesets/roofs/new_bark.2bpp').read_bytes()
 jp=palette((repo/'gfx/tilesets/johto_palette_map.asm').read_text())
 blocks=(0x18,0x1f,0x19,0x1c,0x1d,0x1e,0x47)
 incoming=sorted({t for b in blocks for t in jm[b*16:b*16+16]});remap={}
 for old in incoming:
  data=bytes(jg[old*16:old*16+16]);color='BROWN' if jp[old]=='GREEN' else jp[old]
  match=next((t for t in sorted(used) if bytes(gfx[t*16:t*16+16])==data and colors[t]==color),None)
  if match is None:
   if not free:raise ValueError('Gym graphics would overlap font slots')
   match=free.pop(0);gfx[match*16:match*16+16]=data;colors[match]=color;used.add(match)
  remap[old]=match
 for b in blocks:meta.extend(bytes(remap[t] for t in jm[b*16:b*16+16]))
 coll=(repo/'data/tilesets/cave_town_collision.asm').read_text()
 jc=[l for l in (repo/'data/tilesets/johto_collision.asm').read_text().splitlines() if 'tilecoll ' in l]
 coll+='\n'.join(jc[b].split(';')[0].rstrip() for b in blocks)+'\n'
 for y in range(2):
  for x in range(3):
   offset=y*10+3+x;expected=5 if y==0 else 2
   if room[offset]!=expected:raise ValueError('Gym building site changed')
   room[offset]=73+y*3+x
 if room[23]!=2:raise ValueError('Gym sign site changed')
 room[23]=79
 return {'data/tilesets/cave_town_metatiles.bin':bytes(meta),
         'data/tilesets/cave_town_collision.asm':coll.encode(),
         'gfx/tilesets/cave_town.lz':literal_lz(bytes(gfx)),
         'gfx/tilesets/cave_town_palette_map.asm':('\n'.join('\ttilepal 0, '+', '.join(colors[i:i+8]) for i in range(0,96,8))+'\n').encode()}

def apply(repo,dry_run=False):
 if (repo/'maps/CaveRileyGym.asm').exists():raise ValueError('Riley gym already applied')
 changes={}
 def edit(path,fn):changes[path]=fn((repo/path).read_text()).encode()
 edit('constants/map_constants.asm',lambda s:once(s,'\tmap_const CAVE_TRAINING_HALL,                          5,  6 ; 17\n\tendgroup','\tmap_const CAVE_TRAINING_HALL,                          5,  6 ; 17\n\tmap_const CAVE_RILEY_GYM,                              5,  6 ; 18\n\tendgroup'))
 edit('data/maps/maps.asm',lambda s:once(s,'\tassert_table_length NUM_NEW_BARK_MAPS','\tmap CaveRileyGym, TILESET_ELITE_FOUR_ROOM, INDOOR, LANDMARK_ROUTE_29, MUSIC_GYM, FALSE, PALETTE_DAY, FISHGROUP_SHORE\n\tassert_table_length NUM_NEW_BARK_MAPS'))
 edit('data/maps/attributes.asm',lambda s:s+'\n\tmap_attributes CaveRileyGym, CAVE_RILEY_GYM, $00\n')
 edit('data/maps/blocks.asm',lambda s:s+'\nSECTION "Riley Gym Blocks", ROMX\nCaveRileyGym_Blocks:\n\tINCBIN "maps/CaveRileyGym.blk"\nENDSECTION\n')
 def scripts(s):
  old='\tcp MAP_CAVE_TRAINING_HALL + 1'
  if s.count(old)!=3:raise ValueError('Unexpected village Continue guards')
  s=s.replace(old,'\tcp MAP_CAVE_RILEY_GYM + 1')
  s=once(s,'\tcp MAP_NEW_BARK_CAVE\n\tret nz\n','\tcp MAP_NEW_BARK_CAVE\n\tret nz\n'+MIGRATE)
  return s+'\nSECTION "Riley Gym Scripts", ROMX\nINCLUDE "maps/CaveRileyGym.asm"\nENDSECTION\n'
 edit('data/maps/scripts.asm',scripts)
 def cave(s):
  s=once(s,'\twarp_event 13, 11, CAVE_TRAINING_HALL, 1','\twarp_event 13, 11, CAVE_TRAINING_HALL, 1\n\twarp_event 8, 3, CAVE_RILEY_GYM, 1')
  s=once(s,'\tbg_event 14, 11, BGEVENT_READ, CaveHallSign','\tbg_event 14, 11, BGEVENT_READ, CaveHallSign\n\tbg_event 7, 5, BGEVENT_READ, CaveRileyGymSign')
  s=once(s,'\tpara "NW: the free MART."','\tpara "North: RILEY\'s GYM."\n\tpara "NW: the free MART."')
  return s+SIGN
 edit('maps/NewBarkCave.asm',cave)
 room=bytearray((repo/'maps/NewBarkCave.blk').read_bytes())
 changes.update(art(repo,room));changes['maps/NewBarkCave.blk']=bytes(room)
 changes['maps/CaveRileyGym.blk']=ROOM;changes['maps/CaveRileyGym.asm']=SCRIPT.encode()
 for path,data in changes.items():
  if not dry_run:(repo/path).write_bytes(data)
 return changes
if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('repo',type=Path);p.add_argument('--dry-run',action='store_true');a=p.parse_args();apply(a.repo,a.dry_run)
