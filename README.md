# Johto Gold Player

Browser player for Pokémon Gold using EmulatorJS, with optional versioned IPS modifications.

[Play in your browser](https://kevinbridgman.github.io/johto-gold-player/). Open in Chrome on Android, select your own compatible Gold ROM, choose a modification/version, and tap **Start game**. You can also play unmodified or select a local IPS. No game ROM is distributed; this page reads and patches your ROM in memory without uploading or changing the original file.

## Available modifications

**Kanto + Johto Six Starters v1.1** is the newest release. Start a new game and interact with any of Elm's three Poké Balls to open a menu containing **Bulbasaur, Charmander, Squirtle, Chikorita, Cyndaquil, and Totodile**. Each choice has a picture, cry, and confirmation. B cancels; declining lets you inspect a different choice. You receive exactly one level-5 partner holding a Berry.

The lab layout and story remain original. Gold's type-selection flags are preserved, and the rival retains the original Johto parties: Cyndaquil against Bulbasaur/Chikorita, Totodile against Charmander/Cyndaquil, Chikorita against Squirtle/Totodile. No additional rival species or custom moves are applied in v1.1. `build-tools/patch_six_starters.py` is the source transformation used by current publishing; the older scripts remain available for the previous release.

Source-flow tests cover all six choices from each ball, cancel/decline, original story flags, and prevention of a second starter. Full emulator playthrough and cross-version save compatibility remain unverified. Keep existing saves on their original patch version.


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

Use Pokémon Gold's normal **SAVE** menu. The player flushes cartridge SRAM to the emulator save file every second while the page is visible, then explicitly waits for the IndexedDB write before showing **Game save stored in this browser** below the game. Wait for this confirmation after the in-game save completes before closing the tab. Hiding, leaving, closing, or restarting the page does not trigger a final save. The periodic timer skips hidden pages. The stable emulator’s built-in save-on-unload handler is suppressed; hiding/leaving can finish an already-started browser write but does not start a new save.

The previous stable emulator default was a five-minute system-save interval, with another attempt on page unload. A normal Pokémon save could remain only in memory when the browser closed. The player now manages the frequent flush itself, independently of saved emulator interval settings. Page-hide and unload save attempts were subsequently disabled at the user’s request. It keeps the existing gameName and save path so old successfully persisted files remain discoverable.

Validation: in Chromium with the actual stable EmulatorJS loader and legacy Gambatte core, a locally compiled matching Gold ROM was started from NEW GAME, saved using the in-game SAVE menu, and the entire browser was closed. Reopening with the same browser profile and ROM showed CONTINUE. Five regression tests cover committed-write confirmation, changed SRAM, storage failures/retry, forced writes while a save is pending, visible-page periodic saving, suppression of hide/unload saves, and absent saves. Deployment runs them with `node tests/test_player_saves.cjs`.

Saves remain local to this site and browser profile. Clearing site data, private browsing, or changing devices can remove or hide them. Download backups through the emulator menu. Quick save states are separate from cartridge saves. Save compatibility between patch versions remains unverified; resume with the same ROM and patch. The existing shared emulator save identity is retained in this fix; isolation between different games/patches remains a separate task. A save that the old player never wrote to storage cannot be recovered by this update.
