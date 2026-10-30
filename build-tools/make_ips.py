#!/usr/bin/env python3
"""Create a standard IPS patch from equal-size original and modified ROMs."""
import argparse
from pathlib import Path

def make_ips(original: bytes, modified: bytes) -> bytes:
    if len(original) != len(modified):
        raise ValueError("ROM sizes differ: refusing unsafe IPS patch")
    if len(original) > 0x1000000:
        raise ValueError("IPS maximum offset exceeded")
    out = bytearray(b"PATCH")
    i = 0
    while i < len(original):
        if original[i] == modified[i]:
            i += 1
            continue
        start = i
        while (i < len(original)
               and original[i] != modified[i]
               and i - start < 65535):
            i += 1
        if start == 0x454f46:
            raise ValueError("IPS reserved EOF offset encountered")
        out.extend(start.to_bytes(3, "big"))
        out.extend((i - start).to_bytes(2, "big"))
        out.extend(modified[start:i])
    out.extend(b"EOF")
    return bytes(out)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("original", type=Path)
    p.add_argument("modified", type=Path)
    p.add_argument("output", type=Path)
    args = p.parse_args()
    result = make_ips(args.original.read_bytes(), args.modified.read_bytes())
    args.output.write_bytes(result)
    print("IPS patch created:", args.output, len(result), "bytes")

if __name__ == "__main__":
    main()
