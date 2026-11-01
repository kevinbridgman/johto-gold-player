#!/usr/bin/env python3
"""Show move names plus machine numbers in the cave shop's native buy list."""
import argparse
from pathlib import Path

ROUTINE='''
; Cave machines use two lines: move name, then TM/HM number beside the price.
PlaceMartMoveName:
	ld a, [wMapGroup]
	cp GROUP_CAVE_SUPPLY_MART
	jr nz, .Ordinary
	ld a, [wMapNumber]
	cp MAP_CAVE_SUPPLY_MART
	jr nz, .Ordinary
	ld a, [wMenuSelection]
	cp TM01
	jr c, .Ordinary
	cp HM_WATERFALL + 1
	jr nc, .Ordinary
	cp ITEM_C3
	jr z, .Ordinary
	cp ITEM_DC
	jr z, .Ordinary
	push de
	ld c, a
	farcall GetTMHMNumber
	ld a, c
	ld [wTempTMHM], a
	predef GetTMHMMove
	ld a, [wTempTMHM]
	ld [wNamedObjectIndex], a
	call GetMoveName
	pop hl
	push hl
	call PlaceString
	ld a, [wMenuSelection]
	ld [wNamedObjectIndex], a
	call GetItemName
	pop hl
	ld bc, SCREEN_WIDTH
	add hl, bc
	call PlaceString
	ret
.Ordinary:
	farcall PlaceMenuItemName
	ret
'''

def apply(repo,dry_run=False):
 p=repo/'engine/items/mart.asm';s=p.read_text()
 old='\tdba PlaceMenuItemName\n\tdba .PrintBCDPrices'
 if s.count(old)!=1 or '\nPlaceMartMoveName:' in s:raise ValueError('Unexpected or already modified shop renderer')
 s=s.replace(old,'\tdba PlaceMartMoveName\n\tdba .PrintBCDPrices',1)+ROUTINE
 if not dry_run:p.write_text(s)
 return s
if __name__=='__main__':
 ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('repo',type=Path);ap.add_argument('--dry-run',action='store_true');a=ap.parse_args();apply(a.repo,a.dry_run)
