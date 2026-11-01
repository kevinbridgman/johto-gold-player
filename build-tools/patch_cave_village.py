#!/usr/bin/env python3
"""Add Lantern Hollow's healing lodge, friendly dojo, and lantern garden quest."""
import argparse
from pathlib import Path
from patch_cave_shop import once, literal_lz, palette

FLAGS=('EVENT_CAVE_LANTERN_HOME','EVENT_CAVE_LANTERN_HOPE','EVENT_CAVE_LANTERN_COURAGE','EVENT_CAVE_LUCKY_EGG')
PLOTS=((12,2,16,6,13,6),(12,8,16,12,13,12))
NPCS=((4,10),(7,7),(2,7),(17,7),(6,12),(3,11))

def text(label,paragraphs):
 s=label+':\n'
 for n,lines in enumerate(paragraphs):
  if isinstance(lines,str):lines=(lines,)
  for j,line in enumerate(lines):
   if len(line.replace('#','POKé'))>18:raise ValueError((label,line))
   s+='\t'+('text' if n==j==0 else 'para' if j==0 else 'line' if j==1 else 'cont')+' "'+line+'"\n'
 return s+'\tdone\n\n'

LODGE='''\tobject_const_def
\tconst CAVELODGE_NURSE
\tconst CAVELODGE_TRAVELER

CaveLodge_MapScripts:
\tdef_scene_scripts
\tdef_callbacks

CaveLodgeNurse:
\tfaceplayer
\topentext
\twritetext CaveLodgeWelcome
\tyesorno
\tiffalse .Goodbye
\tclosetext
\tspecial FadeOutToBlack
\tspecial ReloadSpritesNoPalettes
\tplaymusic MUSIC_HEAL
\tspecial HealParty
\tpause 60
\tspecial FadeInFromBlack
\tspecial RestartMapMusic
\topentext
\twritetext CaveLodgeRested
.Goodbye:
\twaitbutton
\tclosetext
\tend

CaveLodgeTraveler:
\tjumptextfaceplayer CaveLodgeTravelerText

CaveLodge_MapEvents:
\tdb 0, 0
\tdef_warp_events
\twarp_event 3, 7, NEW_BARK_CAVE, 4
\twarp_event 4, 7, NEW_BARK_CAVE, 4
\tdef_coord_events
\tdef_bg_events
\tdef_object_events
\tobject_event 3, 1, SPRITE_NURSE, SPRITEMOVEDATA_STANDING_DOWN, 0, 0, -1, -1, PAL_NPC_RED, OBJECTTYPE_SCRIPT, 0, CaveLodgeNurse, -1
\tobject_event 7, 5, SPRITE_SAILOR, SPRITEMOVEDATA_STANDING_LEFT, 0, 0, -1, -1, PAL_NPC_BLUE, OBJECTTYPE_SCRIPT, 0, CaveLodgeTraveler, -1

'''
LODGE+=text('CaveLodgeWelcome',[("Welcome, traveler!","Rest your #MON?"),("Beds are free.","So is the snoring!")])
LODGE+=text('CaveLodgeRested',[("All rested! HP, PP","and status healed."),("The PC by the wall","holds your other","travel companions.")])
LODGE+=text('CaveLodgeTravelerText',[("I sailed all day","to find a quiet","place to sleep."),("Now I live under","a mountain. Best","decision ever.")])

HALL='''\tobject_const_def
\tconst CAVETRAININGHALL_COACH
\tconst CAVETRAININGHALL_STUDENT

CaveTrainingHall_MapScripts:
\tdef_scene_scripts
\tdef_callbacks

CaveTrainingCoach:
\tfaceplayer
\topentext
\twritetext CaveCoachWelcome
\tloadmenu .Header
\tverticalmenu
\tclosewindow
\tifequal 1, .Rookie
\tifequal 2, .Regular
\tifequal 3, .Expert
\tclosetext
\tend
.Rookie:
\tloadtrainer YOUNGSTER, CAVE_COACH_ROOKIE
\tsjump .Battle
.Regular:
\tloadtrainer YOUNGSTER, CAVE_COACH_REGULAR
\tsjump .Battle
.Expert:
\tloadtrainer YOUNGSTER, CAVE_COACH_EXPERT
.Battle:
\twritetext CaveCoachReady
\tyesorno
\tiffalse .Cancel
\tclosetext
\tspecial HealParty
\twinlosstext CaveCoachWon, CaveCoachLost
\tloadvar VAR_BATTLETYPE, BATTLETYPE_CANLOSE
\tstartbattle
\treloadmap
\tspecial HealParty
\topentext
\twritetext CaveCoachAfter
\twaitbutton
.Cancel:
\tclosetext
\tend
.Header:
\tdb MENU_BACKUP_TILES
\tmenu_coords 0, 0, 17, 9
\tdw .Data
\tdb 1
.Data:
\tdb STATICMENU_CURSOR
\tdb 4
\tdb "ROOKIE L5@", "REGULAR L15@", "EXPERT L30@", "CANCEL@"

CaveTrainingStudent:
\tjumptextfaceplayer CaveStudentText

CaveTrainingHall_MapEvents:
\tdb 0, 0
\tdef_warp_events
\twarp_event 4, 11, NEW_BARK_CAVE, 5
\twarp_event 5, 11, NEW_BARK_CAVE, 5
\tdef_coord_events
\tdef_bg_events
\tdef_object_events
\tobject_event 4, 3, SPRITE_YOUNGSTER, SPRITEMOVEDATA_STANDING_DOWN, 0, 0, -1, -1, PAL_NPC_RED, OBJECTTYPE_SCRIPT, 0, CaveTrainingCoach, -1
\tobject_event 7, 8, SPRITE_BLACK_BELT, SPRITEMOVEDATA_STANDING_LEFT, 0, 0, -1, -1, PAL_NPC_BLUE, OBJECTTYPE_SCRIPT, 0, CaveTrainingStudent, -1

'''
HALL+=text('CaveCoachWelcome',[("I'm Coach BRIN!","Pick a practice","team to battle."),("Train anytime!","Losing is safe.")])
HALL+=text('CaveCoachReady',[("I heal your team","before and after."),("Ready to practice?")])
HALL+=text('CaveCoachWon',[("Nice teamwork!","You earned that!")])
HALL+=text('CaveCoachLost',[("No worries! Every","loss is a lesson!")])
HALL+=text('CaveCoachAfter',[("Your team is well.","Real EXP, and no","blackout if lost!"),("Come back anytime.","We'll train again!")])
HALL+=text('CaveStudentText',[("ROOKIE: two at L5.","REGULAR: three L15","EXPERT: three L30."),("BRIN's tough, but","he always helps us","back on our feet.")])

GARDEN='''CaveVillageGuide:
\tjumptextfaceplayer CaveVillageGuideText

CaveGardenPet:
\topentext
\twritetext CaveGardenPetText
\tcry GROWLITHE
\twaitsfx
\twaitbutton
\tclosetext
\tend

CaveBerryKeeper:
\tfaceplayer
\topentext
\tcheckevent EVENT_CAVE_LUCKY_EGG
\tiftrue .Berries
\tcheckevent EVENT_CAVE_LANTERN_HOME
\tiffalse .Quest
\tcheckevent EVENT_CAVE_LANTERN_HOPE
\tiffalse .Quest
\tcheckevent EVENT_CAVE_LANTERN_COURAGE
\tiffalse .Quest
\twritetext CaveGardenComplete
\tpromptbutton
\tverbosegiveitem LUCKY_EGG
\tiffalse .NoRoom
\tsetevent EVENT_CAVE_LUCKY_EGG
\twritetext CaveGardenReward
\tpromptbutton
\tsjump .Berries
.Quest:
\twritetext CaveGardenQuest
\tpromptbutton
.Berries:
\twritetext CaveGardenBerries
\tloadmenu .Header
\tverticalmenu
\tclosewindow
\tifequal 1, .Berry
\tifequal 2, .Gold
\tifequal 3, .Mystery
\tclosetext
\tend
.Berry:
\tverbosegiveitem BERRY
\tsjump .Done
.Gold:
\tverbosegiveitem GOLD_BERRY
\tsjump .Done
.Mystery:
\tverbosegiveitem MYSTERYBERRY
.Done:
\twaitbutton
\tclosetext
\tend
.NoRoom:
\twritetext CaveGardenFull
\twaitbutton
\tclosetext
\tend
.Header:
\tdb MENU_BACKUP_TILES
\tmenu_coords 0, 0, 17, 9
\tdw .Data
\tdb 1
.Data:
\tdb STATICMENU_CURSOR
\tdb 4
\tdb "BERRY@", "GOLD BERRY@", "MYSTERYBERRY@", "CANCEL@"

'''
GARDEN+=text('CaveVillageGuideText',[("LANTERN HOLLOW!","A small town with","a big, rocky roof."),("NW: the free MART.","NE: healing LODGE.","SE: TRAINING HALL."),("SW: LANTERN GARDEN","MIRA grows berries","under warm lamps."),("Leave by the two","southern stairs.")])
GARDEN+=text('CaveGardenPetText',[("GROWLITHE: Arf!","Its fur is warm","as a little stove.")])
GARDEN+=text('CaveGardenQuest',[("I'm MIRA! Berries","need light, even","under a mountain."),("Relight our three","golden lanterns.","They're scattered","about the village."),("One by the MART,","one in the east,","one by our garden."),("Find all three and","I have a special","thank-you for you!")])
GARDEN+=text('CaveGardenComplete',[("All three are lit!","Our little garden","is glowing again."),("This is for you.","May your partners","grow strong!")])
GARDEN+=text('CaveGardenReward',[("A held LUCKY EGG","boosts earned EXP."),("One keepsake for","one kind traveler.","Thank you!")])
GARDEN+=text('CaveGardenBerries',[("Pick a free berry!","Come back whenever","you need another.")])
GARDEN+=text('CaveGardenFull',[("Your bag is full.","I will hold it","safe until you","have room for it.")])
for index,word in enumerate(('Home','Hope','Courage')):
 flag=FLAGS[index]
 GARDEN+=f'''CaveLantern{word}:
\topentext
\tcheckevent {flag}
\tiftrue .Already
\tsetevent {flag}
\tplaysound SFX_ITEM
\twaitsfx
\twritetext CaveLantern{word}Lit
\twaitbutton
\tclosetext
\tend
.Already:
\twritetext CaveLantern{word}Steady
\twaitbutton
\tclosetext
\tend

'''
 GARDEN+=text('CaveLantern'+word+'Lit',[("You relight the","lantern: "+word.upper()+"!"),("Its golden glow","warms the stone.")])
 GARDEN+=text('CaveLantern'+word+'Steady',[(word.upper()+" lantern","shines steadily.","You lit this one.")])
for label,lines in [('CaveLodgeSign',[("LANTERN LODGE","Free rest and PC.")]),('CaveHallSign',[("BRIN'S TRAINING","All are welcome.")])]:
 GARDEN+=label+':\n\tjumptext '+label+'Text\n\n'+text(label+'Text',lines)

MIGRATE='''CaveShopSafeContinue::
\tld a, [wMapGroup]
\tcp GROUP_NEW_BARK_CAVE
\tret nz
\tld a, [wMapNumber]
\tcp MAP_CAVE_SUPPLY_MART
\tjp z, .RefreshClerks
\tcp MAP_NEW_BARK_CAVE
\tret nz
'''
for x1,y1,x2,y2,tx,ty in [(2,2,6,6,3,6),*PLOTS]:
 tag=f'Plot{x1}_{y1}'
 MIGRATE+=f'''\tld a, [wXCoord]
\tcp {x1}
\tjr c, .{tag}
\tcp {x2}
\tjr nc, .{tag}
\tld a, [wYCoord]
\tcp {y1}
\tjr c, .{tag}
\tcp {y2}
\tjr nc, .{tag}
\tld a, {tx}
\tld [wXCoord], a
\tld a, {ty}
\tld [wYCoord], a
\tjp .Moved
.{tag}:
'''
for i,(x,y) in enumerate(NPCS):
 MIGRATE+=f'''\tld a, [wXCoord]
\tcp {x}
\tjr nz, .NPC{i}
\tld a, [wYCoord]
\tcp {y}
\tjr nz, .NPC{i}
\tld a, 8
\tld [wXCoord], a
\tld a, 12
\tld [wYCoord], a
\tjp .Moved
.NPC{i}:
'''
MIGRATE+='''\tret
.Moved:
\tfarcall RefreshPlayerCoords
\tret
.RefreshClerks:
\tld hl, wMap2Object + MAPOBJECT_SCRIPT_POINTER
\tld de, CaveSupplyMartHMClerk
\tld [hl], e
\tinc hl
\tld [hl], d
\tld hl, wMap3Object + MAPOBJECT_SCRIPT_POINTER
\tld de, CaveSupplyMartGearClerk
\tld [hl], e
\tinc hl
\tld [hl], d
\tret
'''
CONTINUE='''
SECTION "Cave Village Continue Objects", ROMX
CaveVillageContinueBlocks::
\tld a, [wMapGroup]
\tcp GROUP_NEW_BARK_CAVE
\tjr nz, .Original
\tld a, [wMapNumber]
\tcp MAP_NEW_BARK_CAVE
\tjr c, .Original
\tcp MAP_CAVE_TRAINING_HALL + 1
\tret c ; fresh layouts, never the old saved screen's blocks
.Original:
\tjp LoadConnectionBlockData
CaveVillageSkipObjects::
\tld a, [wMapGroup]
\tcp GROUP_NEW_BARK_CAVE
\tjr nz, .Keep
\tld a, [wMapNumber]
\tcp MAP_NEW_BARK_CAVE
\tjr c, .Keep
\tcp MAP_CAVE_TRAINING_HALL + 1
\tjr nc, .Keep
\txor a
\tret
.Keep:
\tld a, TRUE
\tret
CaveVillageContinueObjects::
\tld a, [wMapGroup]
\tcp GROUP_NEW_BARK_CAVE
\tret nz
\tld a, [wMapNumber]
\tcp MAP_NEW_BARK_CAVE
\tret c
\tcp MAP_CAVE_TRAINING_HALL + 1
\tret nc
\tfarcall LoadObjectMasks
\tfarcall InitializeVisibleSprites
\tret
ENDSECTION
'''

def village_art(repo,room):
 meta=bytearray((repo/'data/tilesets/cave_town_metatiles.bin').read_bytes())
 encoded=(repo/'gfx/tilesets/cave_town.lz').read_bytes();gfx=bytearray();i=0
 while encoded[i]!=255:
  count=encoded[i]+1
  if count>32:raise ValueError('Expected generated literal cave art')
  gfx.extend(encoded[i+1:i+1+count]);i+=count+1
 colors=palette((repo/'gfx/tilesets/cave_town_palette_map.asm').read_text())
 used={t for b in set(room)|{1} for t in meta[b*16:b*16+16]}|{0x14,0x40}
 free=[t for t in range(96) if t not in used]
 jm=(repo/'data/tilesets/johto_metatiles.bin').read_bytes()
 jg=bytearray((repo/'gfx/tilesets/johto.2bpp').read_bytes())
 jg[0x0a*16:0x13*16]=(repo/'gfx/tilesets/roofs/new_bark.2bpp').read_bytes()
 jp=palette((repo/'gfx/tilesets/johto_palette_map.asm').read_text())
 blocks=(0x24,0x25,0x14,0x15,0x1b)
 incoming=sorted({t for b in blocks for t in jm[b*16:b*16+16]})
 if len(incoming)+1>len(free):raise ValueError('Village art would collide with font slots')
 remap=dict(zip(incoming,free))
 for old,new in remap.items():
  gfx[new*16:new*16+16]=jg[old*16:old*16+16]
  colors[new]='BROWN' if jp[old]=='GREEN' else jp[old]
 for block in blocks:meta.extend(bytes(remap[t] for t in jm[block*16:block*16+16]))
 # Restore original cave moss through a reserved slot, never overwrite shop art.
 grass=free[len(incoming)]
 original=(repo/'gfx/tilesets/cave.2bpp').read_bytes()
 gfx[grass*16:grass*16+16]=original[4*16:5*16]
 colors[grass]=palette((repo/'gfx/tilesets/cave_palette_map.asm').read_text())[4]
 meta[3*16:4*16]=bytes([grass])*16
 coll=(repo/'data/tilesets/cave_town_collision.asm').read_text()
 jc=[l for l in (repo/'data/tilesets/johto_collision.asm').read_text().splitlines() if 'tilecoll ' in l]
 coll+='\n'.join(jc[b].split(';')[0].rstrip() for b in blocks)+'\n'
 # PC sign on the lodge; a distinct broad roof on the training hall.
 room[2*10+7]=0x48
 for (dx,dy),block in zip(((0,0),(1,0),(0,1),(1,1)),range(0x44,0x48)):room[(4+dy)*10+6+dx]=block
 return {'data/tilesets/cave_town_metatiles.bin':bytes(meta),
         'data/tilesets/cave_town_collision.asm':coll.encode(),
         'gfx/tilesets/cave_town.lz':literal_lz(bytes(gfx)),
         'gfx/tilesets/cave_town_palette_map.asm':('\n'.join('\ttilepal 0, '+', '.join(colors[i:i+8]) for i in range(0,96,8))+'\n').encode()}

def apply(repo,dry_run=False):
 if (repo/'maps/CaveLodge.asm').exists():raise ValueError('Village already applied')
 changes={}
 def edit(path,fn):changes[path]=fn((repo/path).read_text()).encode()
 edit('constants/map_constants.asm',lambda s:once(s,'\tmap_const CAVE_SUPPLY_MART,                            6,  4 ; 15\n\tendgroup','\tmap_const CAVE_SUPPLY_MART,                            6,  4 ; 15\n\tmap_const CAVE_LODGE,                                  5,  4 ; 16\n\tmap_const CAVE_TRAINING_HALL,                          5,  6 ; 17\n\tendgroup'))
 edit('data/maps/maps.asm',lambda s:once(s,'\tassert_table_length NUM_NEW_BARK_MAPS','\tmap CaveLodge, TILESET_POKECENTER, INDOOR, LANDMARK_ROUTE_29, MUSIC_POKEMON_CENTER, FALSE, PALETTE_DAY, FISHGROUP_SHORE\n\tmap CaveTrainingHall, TILESET_TRAIN_STATION, INDOOR, LANDMARK_ROUTE_29, MUSIC_VIRIDIAN_CITY, FALSE, PALETTE_DAY, FISHGROUP_SHORE\n\tassert_table_length NUM_NEW_BARK_MAPS'))
 edit('data/maps/attributes.asm',lambda s:s+'\n\tmap_attributes CaveLodge, CAVE_LODGE, $00\n\tmap_attributes CaveTrainingHall, CAVE_TRAINING_HALL, $00\n')
 edit('data/maps/blocks.asm',lambda s:s+'''\nSECTION "Cave Village Interiors", ROMX
CaveLodge_Blocks:
\tINCBIN "maps/CaveLodge.blk"
CaveTrainingHall_Blocks:
\tINCBIN "maps/CaveTrainingHall.blk"
ENDSECTION
''')
 def scripts(s):
  start=s.index('CaveShopSafeContinue::');end=s.index('ENDSECTION',start)
  return s[:start]+MIGRATE+s[end:]+'''\nSECTION "Cave Lodge Scripts", ROMX
INCLUDE "maps/CaveLodge.asm"
ENDSECTION
SECTION "Cave Training Hall Scripts", ROMX
INCLUDE "maps/CaveTrainingHall.asm"
ENDSECTION
'''+CONTINUE
 edit('data/maps/scripts.asm',scripts)
 def home(s):
  old='\tld a, TRUE ; skip object events\n\tcall ReadMapEvents\n\tfarcall CaveShopSafeContinue\n\tret'
  new='''\tfarcall CaveVillageSkipObjects
\tcall ReadMapEvents
\tfarcall CaveShopSafeContinue
\tfarcall CaveVillageContinueObjects
\tret'''
  return once(s,old,new)
 edit('home/map.asm',home)
 edit('data/maps/setup_script_pointers.asm',lambda s:s+'\n\tadd_mapsetup CaveVillageContinueBlocks\n')
 def setup(s):
  a=s.index('MapSetupScript_Continue:');b=s.index('MapSetupScript_Submenu:',a)
  return s[:a]+once(s[a:b],'\tmapsetup LoadConnectionBlockData','\tmapsetup CaveVillageContinueBlocks')+s[b:]
 edit('data/maps/setup_scripts.asm',setup)
 edit('engine/overworld/player_object.asm',lambda s:once(s,'InitializeVisibleSprites:','InitializeVisibleSprites::'))
 edit('engine/overworld/map_objects_2.asm',lambda s:once(s,'LoadObjectMasks:','LoadObjectMasks::'))
 edit('constants/event_flags.asm',lambda s:once(s,'; Unused: next 15 events\n','; Lantern Hollow: four formerly unused persistent bits\n'+''.join('\tconst '+f+'\n' for f in FLAGS)+'; Unused: next 11 events\n'))
 edit('constants/trainer_constants.asm',lambda s:once(s,'\tconst JASON\n\n\ttrainerclass SCHOOLBOY','\tconst JASON\n\tconst CAVE_COACH_ROOKIE\n\tconst CAVE_COACH_REGULAR\n\tconst CAVE_COACH_EXPERT\n\n\ttrainerclass SCHOOLBOY'))
 teams='\nCaveCoachTeams:\n'
 for team in [((5,'RATTATA'),(5,'PIDGEY')),((15,'SANDSHREW'),(15,'MAREEP'),(15,'WOOPER')),((30,'GRAVELER'),(30,'HAUNTER'),(30,'GOLBAT'))]:
  teams+='\tdb "BRIN@", TRAINERTYPE_NORMAL\n'+''.join(f'\tdb {level}, {species}\n' for level,species in team)+'\tdb -1\n'
 edit('data/trainers/parties.asm',lambda s:once(s,'\nSchoolboyGroup:',teams+'\nSchoolboyGroup:'))
 def cave(s):
  s=once(s,'\twarp_event 8, 15, ROUTE_29, 2','\twarp_event 8, 15, ROUTE_29, 2\n\twarp_event 13, 5, CAVE_LODGE, 1\n\twarp_event 13, 11, CAVE_TRAINING_HALL, 1')
  s=once(s,'\tbg_event 4, 5, BGEVENT_READ, CaveSupplyMartSign','\tbg_event 4, 5, BGEVENT_READ, CaveSupplyMartSign\n\tbg_event 14, 5, BGEVENT_READ, CaveLodgeSign\n\tbg_event 14, 11, BGEVENT_READ, CaveHallSign')
  objects='''\tobject_event 4, 10, SPRITE_GRANNY, SPRITEMOVEDATA_STANDING_DOWN, 0, 0, -1, -1, PAL_NPC_GREEN, OBJECTTYPE_SCRIPT, 0, CaveBerryKeeper, -1
\tobject_event 7, 7, SPRITE_SUPER_NERD, SPRITEMOVEDATA_STANDING_DOWN, 0, 0, -1, -1, PAL_NPC_BLUE, OBJECTTYPE_SCRIPT, 0, CaveVillageGuide, -1
\tobject_event 2, 7, SPRITE_GOLD_TROPHY, SPRITEMOVEDATA_STILL, 0, 0, -1, -1, PAL_NPC_RED, OBJECTTYPE_SCRIPT, 0, CaveLanternHome, -1
\tobject_event 17, 7, SPRITE_GOLD_TROPHY, SPRITEMOVEDATA_STILL, 0, 0, -1, -1, PAL_NPC_BLUE, OBJECTTYPE_SCRIPT, 0, CaveLanternHope, -1
\tobject_event 6, 12, SPRITE_GOLD_TROPHY, SPRITEMOVEDATA_STILL, 0, 0, -1, -1, PAL_NPC_GREEN, OBJECTTYPE_SCRIPT, 0, CaveLanternCourage, -1
\tobject_event 3, 11, SPRITE_GROWLITHE, SPRITEMOVEDATA_STANDING_DOWN, 0, 0, -1, -1, PAL_NPC_RED, OBJECTTYPE_SCRIPT, 0, CaveGardenPet, -1
'''
  return once(s,'\tdef_object_events\n','\tdef_object_events\n'+objects)+'\n'+GARDEN
 edit('maps/NewBarkCave.asm',cave)
 room=bytearray((repo/'maps/NewBarkCave.blk').read_bytes())
 for bx,by in [(6,1),(6,4)]:
  for (dx,dy),block in zip(((0,0),(1,0),(0,1),(1,1)),range(0x40,0x44)):room[(by+dy)*10+bx+dx]=block
 # Garden beds reuse native cave moss/grass art; the cave has no encounters.
 for x,y in [(1,4),(2,4),(1,6),(2,6)]:room[y*10+x]=3
 changes.update(village_art(repo,room))
 changes['maps/NewBarkCave.blk']=bytes(room)
 lodge=bytearray((repo/'maps/Pokecenter1F.blk').read_bytes());lodge[15]=4 # no upstairs/link stairs
 changes['maps/CaveLodge.blk']=bytes(lodge)
 changes['maps/CaveTrainingHall.blk']=(repo/'maps/FightingDojo.blk').read_bytes()
 changes['maps/CaveLodge.asm']=LODGE.encode();changes['maps/CaveTrainingHall.asm']=HALL.encode()
 for path,data in changes.items():
  if not dry_run:(repo/path).write_bytes(data)
 return changes

if __name__=='__main__':
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('repo',type=Path);p.add_argument('--dry-run',action='store_true');a=p.parse_args();apply(a.repo,a.dry_run)
