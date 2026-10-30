#!/usr/bin/env python3
"""Apply a three-starter experiment to pret/pokegold/maps/ElmsLab.asm."""
import argparse
from pathlib import Path
import re

SPECIES = {
    "Cyndaquil": ("CYNDAQUIL", "MAREEP", "electric"),
    "Totodile": ("TOTODILE", "HOUNDOUR", "dark"),
    "Chikorita": ("CHIKORITA", "LARVITAR", "rock"),
}

def patch(src: str) -> str:
    out = src
    for key, (old, new, typ) in SPECIES.items():
        start = key + "PokeBallScript:"
        after = {"Cyndaquil":"TotodilePokeBallScript:", "Totodile":"ChikoritaPokeBallScript:", "Chikorita":"DidntChooseStarterScript:"}[key]
        if out.count(start) != 1 or out.count(after) != 1:
            raise ValueError("Missing or duplicate script boundary: " + key)
        pre, tail = out.split(start, 1)
        section, post = tail.split(after, 1)
        for opcode in ("pokepic", "cry"):
            a = "\t" + opcode + " " + old
            if section.count(a) != 1: raise ValueError("Expected exactly one: " + a)
            section = section.replace(a, "\t" + opcode + " " + new, 1)
        for a, b in (
            ("\tgetmonname STRING_BUFFER_3, " + old, "\tgetmonname STRING_BUFFER_3, " + new),
            ("\tgivepoke " + old + ", 5, BERRY", "\tgivepoke " + new + ", 5, BERRY")
        ):
            if section.count(a) != 1: raise ValueError("Expected exactly one: " + a)
            section = section.replace(a, b, 1)
        if "EVENT_GOT_" + old + "_FROM_ELM" not in section:
            raise ValueError("Expected original starter flag missing: " + old)
        out = pre + start + section + after + post
    prompts = {"Cyndaquil":"CYNDAQUIL, the", "Totodile":"TOTODILE, the", "Chikorita":"CHIKORITA, the"}
    for key, expected in prompts.items():
        old, new, typ = SPECIES[key]
        label = "Take" + key + "Text:"
        expr = r"(" + re.escape(label) + r"\n)(.*?)(?=\tdone\n)"
        matches = list(re.finditer(expr, out, re.S))
        if len(matches) != 1: raise ValueError("Prompt label missing or duplicated: " + label)
        m = matches[0]
        if '\tline "' + expected + '"' not in m.group(2):
            raise ValueError("Prompt unexpected: " + label)
        newlines = '\ttext "ELM: Do you want"\n\tline "' + new + ', the"\n\tcont "' + typ + ' #MON?"\n'
        out = out[:m.start(2)] + newlines + out[m.end(2):]
    return out

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("repo", type=Path)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    path = args.repo / "maps" / "ElmsLab.asm"
    if not path.exists(): raise SystemExit("Not found: " + str(path))
    original = path.read_text()
    modified = patch(original)
    if args.dry_run:
        import difflib
        print("".join(difflib.unified_diff(original.splitlines(True),modified.splitlines(True),
              fromfile="a/maps/ElmsLab.asm",tofile="b/maps/ElmsLab.asm")))
    else:
        path.write_text(modified)
        print("Patched " + str(path))

if __name__ == "__main__": main()
