#!/usr/bin/env python3
"""Append a release, or verify an identical rerun; never replace a release."""
import argparse
import hashlib
import json
from pathlib import Path
import re


def publish(root, baseline, patch):
    root = Path(root)
    release = json.loads((root / 'release.json').read_text())
    for key in ('id', 'name', 'version', 'description', 'notes'):
        if not isinstance(release.get(key), str) or not release[key]:
            raise ValueError('Missing release field: ' + key)
    if not re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*', release['id']):
        raise ValueError('Invalid release id')
    if not re.fullmatch(r'\d+\.\d+(?:\.\d+)?', release['version']):
        raise ValueError('Use a numeric version such as 1.1 or 1.1.0')
    data = Path(patch).read_bytes()
    if not data.startswith(b'PATCH') or not data.endswith(b'EOF'):
        raise ValueError('Expected a standard IPS patch')
    release_id = release['id'] + '-v' + release['version']
    filename = 'patches/' + release_id + '.ips'
    entry = {**release, 'id': release_id, 'file': filename,
             'sha256': hashlib.sha256(data).hexdigest(),
             'baseSha1': hashlib.sha1(Path(baseline).read_bytes()).hexdigest()}
    catalog_path = root / 'patches/catalog.json'
    catalog = json.loads(catalog_path.read_text())
    if catalog.get('schemaVersion') != 1 or not isinstance(catalog.get('patches'), list):
        raise ValueError('Unsupported catalog')
    existing = [p for p in catalog['patches'] if p['id'] == release_id or p['file'] == filename]
    target = root / filename
    if existing:
        if existing != [entry] or not target.is_file() or target.read_bytes() != data:
            raise ValueError('Release already exists with different contents. Bump release.json version.')
        return False
    if target.exists():
        raise ValueError('Release file already exists; refusing to overwrite it')
    # All validation precedes writes. Exclusive creation also protects orphan files.
    with target.open('xb') as output:
        output.write(data)
    catalog['patches'].insert(0, entry)
    catalog_path.write_text(json.dumps(catalog, indent=2) + '\n')
    return True


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--baseline', required=True, type=Path)
    parser.add_argument('--patch', required=True, type=Path)
    args = parser.parse_args()
    print('Published new release' if publish(args.root, args.baseline, args.patch)
          else 'Identical release already published')
