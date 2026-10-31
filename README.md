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

## Space speed controls

Use **Player settings → Speed boost (Space / toggle)** to choose a target from 2× to 10×. Hold Space with the game focused; release it, move focus away, or hide the page to return to normal speed. Your browser remembers the target. The indicator beneath the game reports both the target and the measured emulated-frame rate while held. Measured speed depends on device/browser capacity and can fall below the target.

The player resets the emulator's persisted fast-forward/slow-motion toggle modes at startup, hides the duplicate native speed settings, and ignores native speed hotkeys/gamepad inputs so they cannot conflict with Space. Other game and save controls remain available. The stable legacy core resets display scheduling on the frame after a speed toggle; Space applies its scheduler correction after that reset, then restores the normal vsync preference on release. Pending transitions are canceled on release and focus loss so they cannot re-enable speed afterward.

Run speed regression checks with `node tests/test_player_speed.cjs`. These cover saved native modes, all nine targets, the delayed correction, quick taps, focus loss, settings/form guards, changing targets, and measured-rate reporting. No save-on-hide/unload behavior is introduced by this change.

Browser validation with the stable EmulatorJS legacy Gambatte core and a locally compiled Gold ROM: the old control measured about 2× for both 2× and 10× requests. The updated actual Space-event path measured ~119.5, ~300.2, and ~542.7 emulated frames/second for 2×, 5×, and 10× targets; release returned to ~60.3 fps. The 10× target achieved roughly 9× in that run, so the live measured value is reported separately from the requested rate. Faster runs approached 600 fps; no device-independent 10× guarantee is made.

## Save-state screenshot gallery

Open **Player settings → Save states** after starting a game. Slots **1–9** show a screenshot and save time when occupied, or a black preview labeled **empty save state** when unused. Select a slot by clicking its preview, then use **Save** or **Load**. Load is disabled for empty slots. The emulator's numbered-slot setting stays synchronized; its default keys remain **1** to save, **2** to load, and **3** to cycle slots. The native Quick Save/Quick Load menu uses these same slots.

A numbered save captures the emulator state and a native PNG screenshot, then stores both in one IndexedDB transaction. Failed writes or captures keep the previous saved state and thumbnail. These slots survive reopening this site in the same browser profile. Their namespace includes a fingerprint of the final ROM bytes and the legacy Gambatte core family, so changing a ROM or patch gives a separate gallery. They are local, with no uploads. Clearing browser site data removes them; state compatibility with future core versions is unverified.

This is separate from Pokémon's normal cartridge SAVE and from importing/exporting a standalone state file. The old numbered quick saves were held only in the emulator's in-memory filesystem; already-lost states cannot be reconstructed. A thumbnail is captured when saving a numbered slot with the updated player. Starting the game loads the gallery; opening settings, hiding, and leaving the page do not create save states.

Run `node tests/test_player_slots.cjs` for slot isolation, persistence through reopening a model, per-slot overwrite, image/state atomicity, failed captures/writes, concurrent operations, and invalid records. The player deployment runs these alongside the cartridge-save and Space-speed checks.

Browser validation: created slots 1 and 2 with distinct native screenshots using actual stable EmulatorJS/Gambatte and a locally compiled Gold ROM; confirmed seven black empty previews, native slot cycling, screenshot/state persistence after fully closing and reopening Chromium, and successful loading of slot 1 through the gallery.

## Mobile touch controls

Touch controls default to **Auto** in **Player settings → Touch controls**. Auto enables the on-screen D-pad, A, B, Start, and Select when touch hardware, a coarse pointer, or the emulator's mobile detection is present. Select **On** to force them visible or **Off** to hide them. This preference is stored separately from legacy emulator settings.

Automatic startup does not involve tapping the emulator's own start button, so the stable emulator can leave its internal touch flag false. Its resize workaround can also schedule a delayed hide after startup. The player now sets the touch state at ready/start, overrides stale native visibility settings, and keeps the controller visible through that delayed hide. On touch devices it closes the startup menu so the menu does not cover the controls, and scrolls the game into view. Short landscape viewports get a bounded game height. Native Fast/Slow buttons are hidden because those conflicting speed inputs are disabled; keyboard Space speed controls remain unchanged.

The native virtual-gamepad visibility setting is replaced by the player selector. Left-handed positioning and other native controls remain available. Cartridge-save, save-state, and no-save-on-hide/unload behavior are unchanged.

Validation: Chromium with Android user agent, touch input, and a 390×844 viewport, deliberately seeded with legacy virtual-gamepad visibility disabled. Verified visible native controls after automatic startup and the delayed hide, closed startup menu, D-pad right press/release (input 7), Start (3), A (8), B (0), and the player Off/On toggle. Existing speed, cartridge-save, and numbered-state checks also passed.

## Mobile speed toggle

The **Speed boost: Off/On** button below the game uses the same remembered 2×–10× target as the keyboard Space shortcut. Tap once to keep speed boost on while using the touch D-pad/buttons, and tap again to return to normal. The button shows the selected multiplier and its current On/Off state; the measured-speed indicator remains below it.

Change the multiplier in **Player settings → Speed boost (Space / toggle)**. Changing it while the toggle is on updates the active target. Space still works as a hold shortcut, and releasing Space does not cancel a separately latched boost. Hiding the page, switching apps, loading/saving a numbered state, or restarting resets speed boost to Off. Only the target multiplier is remembered; the On state is not restored after reopening. No save-on-hide/unload behavior is added.

Mobile browser validation (390×844, Android user agent and touch): tapping the button enabled a latched 5× boost, remained active during a touch A-button press, and measured about 299.6 emulated fps. A second tap returned the button to Off and the game to normal speed. The toggle is visible directly below the game viewport.
