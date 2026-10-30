# Johto Gold Player

Browser player for Pokémon Gold using EmulatorJS, with optional versioned IPS modifications.

[Play in your browser](https://kevinbridgman.github.io/johto-gold-player/). Open in Chrome on Android, select your own compatible Gold ROM, choose a modification/version, and tap **Start game**. You can also play unmodified or select a local IPS. No game ROM is distributed; this page reads and patches your ROM in memory without uploading or changing the original file.

## Available modification

**Johto Custom Starters + Rival v1.0** replaces Chikorita's line with Larvitar/Pupitar/Tyranitar, Cyndaquil's with Mareep/Flaaffy/Ampharos, and Totodile's with Houndour/Houndoom. All 21 rival party variants use the corresponding replacements. The world, story, graphics, and music remain intact. Balance, dialogue, complete progression, and long-term save compatibility remain experimental.

The player checks the original ROM SHA-1 and downloaded patch SHA-256 before applying a published patch. Older releases stay in the modification dropdown; the most recently published release appears first and is selected by default.

## Publishing a new release

1. Develop and test modifications in the private `johto-gold-mod` repository.
2. Copy changed patch scripts into this repository's `build-tools/`. Synchronization is manual.
3. Edit `release.json`: bump `version` (for example, `1.0` to `1.1`) and update the description/notes. Keep `id` as the stable modification family.
4. Push the scripts and metadata together to `main`, or run **Build and publish Johto IPS patch** manually.
5. Verify Actions succeeds and the new release appears in the live player.

The workflow compiles baseline and modified Gold using RGBDS 1.0.4, generates a temporary IPS, then runs `build-tools/publish_release.py`. This creates a file such as `patches/johto-starters-rival-v1.1.ips` and prepends its unique release entry to `patches/catalog.json`, preserving all existing releases. Each entry contains its own description, version, base ROM SHA-1, and patch SHA-256.

An identical rerun is a no-op. Reusing an existing version with different bytes, base ROM, or metadata fails without replacing the release. Bump the version to publish a change. New versions are ordered by publication time, so publish them in ascending version order. These guards apply to the publishing workflow; direct repository edits can still change files.

The original v1.0 patch is preserved as `patches/johto-starters-rival-v1.0.ips`. The old unversioned `patches/johto-starters-rival.ips` remains a frozen compatibility download, not a latest-version alias. Do not overwrite it.

Run release tests with:

```bash
python3 -m unittest discover -s tests -v
```

The publishing workflow tests releases before building. The separate `deploy.yml` deploys the static player. Upstream `pret/pokegold` is still fetched at HEAD; a changed upstream build may require a new release version.

## Saves

EmulatorJS may persist saves/states in browser storage. Save persistence after closing/reopening, explicit backup/restore, and compatibility across patch versions are not fully verified. Keep backups and use the same patch version when resuming an existing game. Clearing site data or changing browsers/devices can lose saves. EmulatorJS loads from its official CDN and initially needs internet.
