#!/usr/bin/env python3
"""Build a northwest cave mart with two clerks and locally free HM/supply stock."""
import argparse
import difflib
from pathlib import Path
import re

HMS=('HM_CUT','HM_FLY','HM_SURF','HM_STRENGTH','HM_FLASH','HM_WHIRLPOOL','HM_WATERFALL')
GEAR=('POTION','SUPER_POTION','HYPER_POTION','FULL_RESTORE','REVIVE','FULL_HEAL','POKE_BALL','GREAT_BALL','ULTRA_BALL','MASTER_BALL')
PLOTS=(2,2,6,6) # half-open walking-tile footprint: northwest only


def once(s,a,b):
    if s.count(a)!=1:raise ValueError('Unexpected source: '+repr(a[:90]))
    return s.replace(a,b,1)


def literal_lz(data):
    return b''.join(bytes([len(data[i:i+32])-1])+data[i:i+32] for i in range(0,len(data),32))+b'\xff'


def palette(s):
    names=[]
    for line in s.splitlines():
        if 'tilepal ' in line:names+=line.split('tilepal ',1)[1].split(', ')[1:]
    return names


def assets(repo):
    room=bytearray((repo/'maps/NewBarkCave.blk').read_bytes())
    cm=(repo/'data/tilesets/cave_metatiles.bin').read_bytes()
    jm=(repo/'data/tilesets/johto_metatiles.bin').read_bytes()
    cg=bytearray((repo/'gfx/tilesets/cave.2bpp').read_bytes())
    jg=bytearray((repo/'gfx/tilesets/johto.2bpp').read_bytes())
    jg[0x0a*16:0x13*16]=(repo/'gfx/tilesets/roofs/new_bark.2bpp').read_bytes()
    cp=palette((repo/'gfx/tilesets/cave_palette_map.asm').read_text())
    jp=palette((repo/'gfx/tilesets/johto_palette_map.asm').read_text())
    blocks=(0x18,0x19,0x1a,0x17) # original Johto mart roof / door / MART sign
    used={t for b in set(room)|{1} for t in cm[b*16:b*16+16]}|{0x14,0x40}
    free=[t for t in range(96) if t not in used]
    incoming=sorted({t for b in blocks for t in jm[b*16:b*16+16]})
    if len(incoming)>len(free):raise ValueError('Not enough safe graphics tiles')
    remap=dict(zip(incoming,free))
    for old,new in remap.items():
        cg[new*16:new*16+16]=jg[old*16:old*16+16]
        cp[new]='BROWN' if jp[old]=='GREEN' else jp[old]
    assert len(cg)==96*16 # NEVER use font slots 0x60-0x7f for map art
    meta=cm+b''.join(bytes(remap[t] for t in jm[b*16:b*16+16]) for b in blocks)
    coll=[l for l in (repo/'data/tilesets/johto_collision.asm').read_text().splitlines() if 'tilecoll ' in l]
    collision=(repo/'data/tilesets/cave_collision.asm').read_text().rstrip()+'\n'
    collision+='\n'.join(coll[b].split(';')[0].rstrip() for b in blocks)+'\n'
    for (x,y),block in zip(((1,1),(2,1),(1,2),(2,2)),range(0x40,0x44)):room[y*10+x]=block
    pal='\n'.join('\ttilepal 0, '+', '.join(cp[i:i+8]) for i in range(0,96,8))+'\n'
    interior=bytes([0x00,0x03,0x03,0x03,0x03,0x00,
                    0x00,0x0d,0x0d,0x0d,0x0d,0x00,
                    0x07,0x04,0x04,0x04,0x04,0x20,
                    0x07,0x2a,0x04,0x04,0x04,0x20])
    return {'maps/NewBarkCave.blk':bytes(room),'maps/CaveSupplyMart.blk':interior,
            'gfx/tilesets/cave_town.lz':literal_lz(bytes(cg)),
            'data/tilesets/cave_town_metatiles.bin':meta,
            'data/tilesets/cave_mart_metatiles.bin':(repo/'data/tilesets/mart_metatiles.bin').read_bytes().replace(bytes([1]),bytes([72])),
            'data/tilesets/cave_town_collision.asm':collision.encode(),
            'gfx/tilesets/cave_town_palette_map.asm':pal.encode()}


SHOP='''\tobject_const_def
\tconst CAVESUPPLYMART_HM_CLERK
\tconst CAVESUPPLYMART_GEAR_CLERK

CaveSupplyMart_MapScripts:
\tdef_scene_scripts
\tdef_callbacks

CaveSupplyMartHMClerk:
\tfaceplayer
\topentext
\twritetext CaveSupplyMartHMIntro
\twaitbutton
\tpokemart MARTTYPE_STANDARD, MART_CAVE_HMS
\tclosetext
\tend

CaveSupplyMartGearClerk:
\tfaceplayer
\topentext
\twritetext CaveSupplyMartGearIntro
\twaitbutton
\tpokemart MARTTYPE_STANDARD, MART_CAVE_GEAR
\tclosetext
\tend

CaveSupplyMartHMIntro:
\ttext "All seven HMs are"
\tline "free here!"
\tpara "HMs are reusable."
\tline "One of each is"
\tcont "enough!"
\tpara "You still need the"
\tline "right BADGES to"
\tcont "use them outside"
\tcont "battle."
\tdone

CaveSupplyMartGearIntro:
\ttext "Welcome to our"
\tline "new cave shop!"
\tpara "POTIONS and BALLS"
\tline "are all free."
\tpara "Take what you need"
\tline "for your journey!"
\tdone

CaveSupplyMart_MapEvents:
\tdb 0, 0
\tdef_warp_events
\twarp_event 2, 7, NEW_BARK_CAVE, 2
\twarp_event 3, 7, NEW_BARK_CAVE, 2
\tdef_coord_events
\tdef_bg_events
\tdef_object_events
\tobject_event 3, 1, SPRITE_CLERK, SPRITEMOVEDATA_STANDING_DOWN, 0, 0, -1, -1, PAL_NPC_BLUE, OBJECTTYPE_SCRIPT, 0, CaveSupplyMartHMClerk, -1
\tobject_event 8, 1, SPRITE_CLERK, SPRITEMOVEDATA_STANDING_DOWN, 0, 0, -1, -1, PAL_NPC_RED, OBJECTTYPE_SCRIPT, 0, CaveSupplyMartGearClerk, -1
'''
SAFE='''
SECTION "Cave Shop Save Migration", ROMX
CaveShopSafeContinue::
\tld a, [wMapGroup]
\tcp GROUP_NEW_BARK_CAVE
\tret nz
\tld a, [wMapNumber]
\tcp MAP_NEW_BARK_CAVE
\tret nz
\tld a, [wXCoord]
\tcp 2
\tret c
\tcp 6
\tret nc
\tld a, [wYCoord]
\tcp 2
\tret c
\tcp 6
\tret nc
\tld a, 3
\tld [wXCoord], a
\tld a, 6
\tld [wYCoord], a
\tfarcall RefreshPlayerCoords
\tret
ENDSECTION
'''


def apply(repo,dry_run=False):
    if (repo/'maps/CaveSupplyMart.asm').exists():raise ValueError('Shop already applied')
    updates=assets(repo)
    def edit(path,fn):updates[path]=fn((repo/path).read_text()).encode()
    edit('constants/map_constants.asm',lambda s:once(s,'\tmap_const NEW_BARK_CAVE,                              10,  8 ; 14\n\tendgroup','\tmap_const NEW_BARK_CAVE,                              10,  8 ; 14\n\tmap_const CAVE_SUPPLY_MART,                            6,  4 ; 15\n\tendgroup'))
    edit('constants/tileset_constants.asm',lambda s:once(s,'DEF NUM_TILESETS EQU const_value - 1','\tconst TILESET_CAVE_TOWN\n\tconst TILESET_CAVE_MART\nDEF NUM_TILESETS EQU const_value - 1'))
    edit('data/tilesets.asm',lambda s:once(s,'\tassert_table_length NUM_TILESETS + 1','\ttileset TilesetCaveTown\n\ttileset TilesetCaveMart\n\tassert_table_length NUM_TILESETS + 1'))
    edit('data/tileset_anims.asm',lambda s:once(s,'TilesetHouseAnim:', 'TilesetCaveMartAnim:\nTilesetCaveTownAnim:\nTilesetHouseAnim:'))
    edit('gfx/tileset_palette_maps.asm',lambda s:once(s,'TilesetMartPalMap:', 'TilesetCaveMartPalMap:\nTilesetMartPalMap:')+'\nTilesetCaveTownPalMap:\nINCLUDE "gfx/tilesets/cave_town_palette_map.asm"\n')
    edit('gfx/tilesets.asm',lambda s:once(once(s,'TilesetMartGFX::', 'TilesetCaveMartGFX::\nTilesetMartGFX::'),'TilesetMartColl::','TilesetCaveMartColl::\nTilesetMartColl::')+'''\nSECTION "Cave Town Graphics", ROMX
TilesetCaveTownGFX::
\tINCBIN "gfx/tilesets/cave_town.lz"
TilesetCaveTownMeta::
\tINCBIN "data/tilesets/cave_town_metatiles.bin"
TilesetCaveTownColl::
\tINCLUDE "data/tilesets/cave_town_collision.asm"
TilesetCaveMartMeta::
\tINCBIN "data/tilesets/cave_mart_metatiles.bin"
''')
    edit('data/maps/maps.asm',lambda s:once(s,'\tmap NewBarkCave, TILESET_CAVE,','\tmap NewBarkCave, TILESET_CAVE_TOWN,').replace('\tassert_table_length NUM_NEW_BARK_MAPS','\tmap CaveSupplyMart, TILESET_CAVE_MART, INDOOR, LANDMARK_ROUTE_29, MUSIC_NEW_BARK_TOWN, FALSE, PALETTE_DAY, FISHGROUP_SHORE\n\tassert_table_length NUM_NEW_BARK_MAPS',1))
    edit('data/maps/attributes.asm',lambda s:s+'\n\tmap_attributes CaveSupplyMart, CAVE_SUPPLY_MART, $00\n')
    edit('data/maps/blocks.asm',lambda s:s+'\nSECTION "Cave Supply Mart Blocks", ROMX\nCaveSupplyMart_Blocks:\n\tINCBIN "maps/CaveSupplyMart.blk"\nENDSECTION\n')
    edit('data/maps/scripts.asm',lambda s:s+'\nSECTION "Cave Supply Mart Scripts", ROMX\nINCLUDE "maps/CaveSupplyMart.asm"\nENDSECTION\n'+SAFE)
    edit('maps/NewBarkCave.asm',lambda s:once(s,'\twarp_event 9, 15, ROUTE_29, 2','\twarp_event 9, 15, ROUTE_29, 2\n\twarp_event 3, 5, CAVE_SUPPLY_MART, 1').replace('\tdef_bg_events','\tdef_bg_events\n\tbg_event 4, 5, BGEVENT_READ, CaveSupplyMartSign',1)+'''\nCaveSupplyMartSign:
\tjumptext CaveSupplyMartSignText
CaveSupplyMartSignText:
\ttext "CAVE SUPPLY MART"
\tpara "HMs and supplies."
\tline "Everything FREE!"
\tdone
''')
    edit('engine/overworld/player_object.asm',lambda s:once(s,'RefreshPlayerCoords:', 'RefreshPlayerCoords::'))
    edit('home/map.asm',lambda s:once(s,'\tld a, TRUE ; skip object events\n\tcall ReadMapEvents\n\tret','\tld a, TRUE ; skip object events\n\tcall ReadMapEvents\n\tfarcall CaveShopSafeContinue\n\tret'))
    edit('engine/items/items.asm',lambda s:once(s,'GetItemPrice:\n; Return the price of wCurItem in de.\n\tpush hl\n\tpush bc','''GetItemPrice:
; Return the price of wCurItem in de. Only this cave shop is free.
\tpush hl
\tpush bc
\tld a, [wMapGroup]
\tcp GROUP_CAVE_SUPPLY_MART
\tjr nz, .NormalPrice
\tld a, [wMapNumber]
\tcp MAP_CAVE_SUPPLY_MART
\tjr nz, .NormalPrice
\tld de, 0
\tpop bc
\tpop hl
\tret
.NormalPrice:
'''.rstrip()))
    edit('constants/mart_constants.asm',lambda s:once(s,'DEF NUM_MARTS EQU const_value','\tconst MART_CAVE_HMS\n\tconst MART_CAVE_GEAR\nDEF NUM_MARTS EQU const_value'))
    stock='\n'
    for label,items in [('MartCaveHMs',HMS),('MartCaveGear',GEAR)]:stock+=label+':\n\tdb '+str(len(items))+'\n'+''.join('\tdb '+v+'\n' for v in items)+'\tdb -1\n\n'
    edit('data/items/marts.asm',lambda s:once(s,'\tassert_table_length NUM_MARTS','\tdw MartCaveHMs\n\tdw MartCaveGear\n\tassert_table_length NUM_MARTS')+stock)
    updates['maps/CaveSupplyMart.asm']=SHOP.encode()
    # Validate everything before writing any generated data or source.
    for path,data in updates.items():
        if dry_run:print(path, len(data),'bytes')
        else:(repo/path).write_bytes(data)
    return updates

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('repo',type=Path);parser.add_argument('--dry-run',action='store_true')
    args=parser.parse_args();apply(args.repo,args.dry_run)
