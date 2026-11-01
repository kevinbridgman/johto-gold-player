#!/usr/bin/env python3
"""Give the existing cave HM clerk all 50 TMs in five safe-sized catalogs."""
import argparse
from pathlib import Path
import re

RANGES=tuple((n,n+9) for n in range(1,51,10))

def once(s,old,new):
    if s.count(old)!=1:raise ValueError('Unexpected source: '+repr(old[:80]))
    return s.replace(old,new,1)


def tm_items(source):
    names=re.findall(r'^\s*add_tm\s+(\w+)',source,re.M)
    if len(names)!=50 or len(set(names))!=50:raise ValueError('Expected 50 unique original Gold TMs')
    return tuple('TM_'+name for name in names)


def menus():
    s='''CaveSupplyMartHMClerk:
\tfaceplayer
\topentext
\twritetext CaveSupplyMartMachineIntro
\twaitbutton
.Catalog:
\twritetext CaveSupplyMartCatalogText
\tloadmenu .CatalogHeader
\tverticalmenu
\tclosewindow
\tifequal 1, .HMs
\tifequal 2, .TMs
\tclosetext
\tend
.HMs:
\twritetext CaveSupplyMartHMIntro
\twaitbutton
\tpokemart MARTTYPE_STANDARD, MART_CAVE_HMS
\tsjump .Catalog
.TMs:
\twritetext CaveSupplyMartTMText
\tloadmenu .TMHeader
\tverticalmenu
\tclosewindow
'''
    for index,(first,last) in enumerate(RANGES,1):s+=f'\tifequal {index}, .TM{first:02d}\n'
    s+='\tsjump .Catalog\n'
    for first,last in RANGES:
        s+=f'.TM{first:02d}:\n\tpokemart MARTTYPE_STANDARD, MART_CAVE_TMS_{first}_{last}\n\tsjump .TMs\n'
    s+='''.CatalogHeader:
\tdb MENU_BACKUP_TILES
\tmenu_coords 0, 0, 12, 7
\tdw .CatalogData
\tdb 1
.CatalogData:
\tdb STATICMENU_CURSOR
\tdb 3
\tdb "HMs@", "TMs@", "CANCEL@"
.TMHeader:
\tdb MENU_BACKUP_TILES
\tmenu_coords 0, 0, 16, 13
\tdw .TMData
\tdb 1
.TMData:
\tdb STATICMENU_CURSOR
\tdb 6
'''
    for first,last in RANGES:s+=f'\tdb "TM{first:02d}-{last:02d}@"\n'
    s+='''\tdb "BACK@"

CaveSupplyMartMachineIntro:
\ttext "All TMs and HMs"
\tline "are free here!"
\tdone

CaveSupplyMartCatalogText:
\ttext "Choose a catalog."
\tdone

CaveSupplyMartTMText:
\ttext "TMs are used once."
\tline "Choose TM numbers."
\tdone

'''
    return s


def apply(repo,dry_run=False):
    source=(repo/'maps/CaveSupplyMart.asm').read_text()
    if 'CaveSupplyMartMachineIntro:' in source:raise ValueError('TM catalogs already applied')
    start=source.index('CaveSupplyMartHMClerk:\n');end=source.index('CaveSupplyMartGearClerk:\n')
    expected='''CaveSupplyMartHMClerk:
\tfaceplayer
\topentext
\twritetext CaveSupplyMartHMIntro
\twaitbutton
\tpokemart MARTTYPE_STANDARD, MART_CAVE_HMS
\tclosetext
\tend

'''
    if source[start:end]!=expected:raise ValueError('Unexpected existing HM clerk')
    items=tm_items((repo/'constants/item_constants.asm').read_text())
    changes={'maps/CaveSupplyMart.asm':source[:start]+menus()+source[end:]}
    constants=(repo/'constants/mart_constants.asm').read_text()
    new_constants=''.join(f'\tconst MART_CAVE_TMS_{first}_{last}\n' for first,last in RANGES)
    changes['constants/mart_constants.asm']=once(constants,'DEF NUM_MARTS EQU const_value',new_constants+'DEF NUM_MARTS EQU const_value')
    stock=(repo/'data/items/marts.asm').read_text()
    pointers=''.join(f'\tdw MartCaveTMs{first:02d}\n' for first,last in RANGES)
    stock=once(stock,'\tassert_table_length NUM_MARTS',pointers+'\tassert_table_length NUM_MARTS')
    for first,last in RANGES:
        stock+=f'\nMartCaveTMs{first:02d}:\n\tdb 10\n'
        stock+=''.join('\tdb '+item+'\n' for item in items[first-1:last])+'\tdb -1\n'
    changes['data/items/marts.asm']=stock
    scripts=(repo/'data/maps/scripts.asm').read_text()
    scripts=once(scripts,'\tld a, [wMapNumber]\n\tcp MAP_NEW_BARK_CAVE\n\tret nz',
        '\tld a, [wMapNumber]\n\tcp MAP_CAVE_SUPPLY_MART\n\tjr z, .RefreshClerks\n\tcp MAP_NEW_BARK_CAVE\n\tret nz')
    scripts=once(scripts,'\tfarcall RefreshPlayerCoords\n\tret\nENDSECTION',
        '\tfarcall RefreshPlayerCoords\n\tret\n.RefreshClerks:\n'
        '\tld hl, wMap2Object + MAPOBJECT_SCRIPT_POINTER\n\tld de, CaveSupplyMartHMClerk\n'
        '\tld [hl], e\n\tinc hl\n\tld [hl], d\n'
        '\tld hl, wMap3Object + MAPOBJECT_SCRIPT_POINTER\n\tld de, CaveSupplyMartGearClerk\n'
        '\tld [hl], e\n\tinc hl\n\tld [hl], d\n\tret\nENDSECTION')
    changes['data/maps/scripts.asm']=scripts
    for relative,text in changes.items():
        if dry_run:print(relative,len(text),'characters')
        else:(repo/relative).write_text(text)
    return changes

if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('repo',type=Path);parser.add_argument('--dry-run',action='store_true')
    args=parser.parse_args();apply(args.repo,args.dry_run)
