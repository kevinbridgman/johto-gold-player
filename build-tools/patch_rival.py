#!/usr/bin/env python3
"""Update both rival trainer groups for the three custom starters."""
import argparse
from pathlib import Path
import re

# Preserve the story's starter selection flags and trainer-party ordering.
REPLACEMENTS = {
    "CHIKORITA": ("LARVITAR", ("BITE", "LEER", "SANDSTORM", "ROCK_SLIDE")),
    "BAYLEEF": ("PUPITAR", ("BITE", "ROCK_SLIDE", "SCREECH", "THRASH")),
    "MEGANIUM": ("TYRANITAR", ("ROCK_SLIDE", "BITE", "THRASH", "SCREECH")),
    "CYNDAQUIL": ("MAREEP", ("TACKLE", "GROWL", "THUNDERSHOCK", "THUNDER_WAVE")),
    "QUILAVA": ("FLAAFFY", ("THUNDERSHOCK", "THUNDER_WAVE", "COTTON_SPORE", "TACKLE")),
    "TYPHLOSION": ("AMPHAROS", ("THUNDERPUNCH", "THUNDER_WAVE", "LIGHT_SCREEN", "SWIFT")),
    "TOTODILE": ("HOUNDOUR", ("EMBER", "LEER", "ROAR", "BITE")),
    "CROCONAW": ("HOUNDOOM", ("EMBER", "BITE", "ROAR", "SMOG")),
    "FERALIGATR": ("HOUNDOOM", ("FLAMETHROWER", "BITE", "ROAR", "CRUNCH")),
}
GROUPS = {"Rival1Group": 15, "Rival2Group": 6}

def patch(src: str) -> str:
    result = src
    for group, expected_count in GROUPS.items():
        m = re.search(r"(?m)^" + group + r":[ \t]*$", result)
        if not m:
            raise ValueError("Missing trainer group: " + group)
        following = re.search(r"(?m)^[A-Za-z_][A-Za-z_0-9]*Group:[ \t]*$", result[m.end():])
        if not following:
            raise ValueError("Missing next trainer group: " + group)
        start, end = m.end(), m.end() + following.start()
        blocks = re.split(r"(?m)(?=^[ \t]*; RIVAL[12] \(\d+\)[ \t]*$)", result[start:end])
        if len(blocks) != expected_count + 1:
            raise ValueError(group + ": wrong number of variants")
        for i in range(1, len(blocks)):
            block = blocks[i]
            head = re.search(r"; RIVAL[12] \((\d+)\)", block)
            if not head or int(head.group(1)) != i:
                raise ValueError(group + ": unexpected rival variant")
            pattern = (r"(?m)^([ \t]*db[ \t]+\d+,[ \t]*)(" +
                       "|".join(REPLACEMENTS) +
                       r")([ \t]*(?:,[ \t]*[^\n;]+)?)([ \t]*(?:;[^\n]*)?)$")
            found = list(re.finditer(pattern, block))
            if len(found) != 1:
                raise ValueError(f"{group} ({i}): expected one starter party member")
            hit = found[0]
            species, moves = REPLACEMENTS[hit.group(2)]
            is_moves = "TRAINERTYPE_MOVES" in block
            if not is_moves and "TRAINERTYPE_NORMAL" not in block:
                raise ValueError("Unsupported trainer type")
            if is_moves and len(hit.group(3).strip().lstrip(",").split(",")) != 4:
                raise ValueError("Expected four moves")
            if not is_moves and hit.group(3).strip():
                raise ValueError("Unexpected moves")
            replacement = hit.group(1) + species
            if is_moves:
                replacement += ", " + ", ".join(moves)
            replacement += hit.group(4)
            blocks[i] = block[:hit.start()] + replacement + block[hit.end():]
        result = result[:start] + "".join(blocks) + result[end:]
    return result

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("repo", type=Path)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    path = args.repo / "data/trainers/parties.asm"
    old = path.read_text()
    new = patch(old)
    if args.dry_run:
        import difflib
        print("".join(difflib.unified_diff(
            old.splitlines(True), new.splitlines(True),
            fromfile="a/data/trainers/parties.asm",
            tofile="b/data/trainers/parties.asm")))
    else:
        path.write_text(new)
        print("Updated all 21 rival starter variants")

if __name__ == "__main__":
    main()
