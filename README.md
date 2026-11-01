# Johto Gold Player

Browser player for Pokémon Gold using EmulatorJS, with optional versioned IPS modifications.

[Play in your browser](https://kevinbridgman.github.io/johto-gold-player/). Open in Chrome on Android, select your own compatible Gold ROM, choose a modification/version, and tap **Start game**. You can also play unmodified or select a local IPS. No game ROM is distributed; this page reads and patches your ROM in memory without uploading or changing the original file.

## Available modifications

**Lantern Hollow Village v1.8** turns the lit cave into a small settlement, keeping the northwest free shop and the central north–south path. Three additions are ready to explore:

1. **Lantern Lodge, northeast:** a nurse offers free rest, restoring HP, PP and status. The standard working PC provides Pokémon and item storage. A traveling sailor has found his favorite quiet bed. The unused upstairs/link stairs are removed.
2. **Brin's Training Hall, southeast:** choose ROOKIE (two level-5 Pokémon), REGULAR (three level-15 Pokémon), or EXPERT (three level-30 Pokémon). Confirm before battle; Cancel does nothing. Matches are repeatable, award normal battle EXP/money, and respect your EXP option. Your party heals before and after; losing uses Gold's original CANLOSE battle type and returns you to the hall without blackout or money loss. A student explains the tiers.
3. **Lantern Garden, southwest:** meet Mira, her warm Growlithe, and a village guide. Explore to relight three golden lanterns (HOME by the mart, HOPE along the east wall, COURAGE by the garden). Return to Mira for one Lucky Egg per save; if your item pocket is full, she keeps the reward until you have room. She also offers a free Berry, Gold Berry, or MysteryBerry per visit, with repeat visits allowed. Lanterns can be found in any order, even before speaking to her. Progress persists in the normal save.

The cave exit remains the two marked south stairs. The original shop, TM/HM move-name listings, six starters and EXP setting remain. Space remains along the central street and at the edges for future additions. New map IDs 24:16 and 24:17 and YOUNGSTER trainer IDs 13–15 are appended. Four formerly unused persistent event bits (185–188) hold the lanterns and reward; every previously named event/map/trainer ID and save layout is preserved.

**Upgrading:** back up your normal cartridge save, choose v1.8, and use CONTINUE. Continuing inside the village reloads current NPC scripts and the current map blocks, preventing an older save's floor snapshot from hiding new buildings. Saves in new building footprints or on new residents move to a clear nearby tile. Outside village maps, original object/screen restoration remains. A save inside the lodge or hall needs v1.8 or later; leave and save outside before reverting. Numbered emulator states remain tied to their exact ROM. Older IPS releases remain immutable.

Validation for v1.8: all 37 source/release checks pass, including preservation of old event, map and trainer IDs. Clean application of all source scripts with RGBDS 1.0.4 builds a byte-identical ROM. Compiled checks cover all cave save positions, all village destinations and interaction approaches, paired doors, PC/counter collision, staircase exits, the three trainer teams, font safety, and the existing 67 free stocks/57 move labels. Native gameplay continued a v1.4 cave save, entered the lodge, restored damaged HP/exhausted PP/status, opened Bill's PC menu, found all lanterns and claimed the reward. A normal save inside the hall reopened with six starters and all quest flags retained. Native practice tests used a controlled test party: a rookie win awarded EXP and healed afterward; a regular loss returned to the hall healed with money unchanged; expert selection loaded its level-30 team. Repeat reward rejection, a full item pocket and successful reward retry were exercised. Full playthrough remains unverified.

**New Bark Cave + Named TM/HM Shop v1.7** shows each machine's **move name** in the cave shop's buy list, with its **TM/HM number and ¥0 price underneath**. This applies to all 50 TMs and seven HMs from the left clerk. The five TM catalogs and unlimited free stock remain; supplies and other marts retain their existing item listings.

The cave's south opening now has **two visible downward stair tiles**. Walk onto either tile at the bottom center, then keep pressing **Down** to return to Route 29. Previously only the unmarked right-hand tile triggered the exit. Both sides now work. The original cave exit remains warp 1, the shop remains warp 2, and the second exit tile is appended as warp 3. Map IDs and save layout remain unchanged. Use **CONTINUE** from a normal cartridge save after changing patch versions; back it up first. Numbered states remain tied to the exact ROM.

Validation for v1.7: all 34 source/release tests pass. RGBDS 1.0.4 builds the release. Compiled PyBoy checks render all 57 correct move names and machine numbers within their two rows, verify ordinary item names and names outside the shop are unchanged, and retain the stock/pricing, saved-clerk, cave recovery, geometry and font checks. Native gameplay purchased a TM using the new listing, continued an older cave save, walked out through each exit tile to Route 29 and re-entered successfully. Complete playthrough remains unverified.

**New Bark Cave + Free TM/HM Shop v1.6** adds **all 50 original Gold TMs** to the same left-hand clerk who supplies the seven HMs. Talk over his counter, choose **TMs**, then choose **TM01–10**, **TM11–20**, **TM21–30**, **TM31–40**, or **TM41–50**. Choose **HMs** for the original HM stock. Every machine costs **¥0**, with unlimited restocking and normal quantity/bag limits. TMs retain their original single-use behavior; HMs remain reusable with the original field badge requirements. The right-hand supplies clerk, shop building and cave layout remain unchanged.

Use a normal in-game SAVE and **CONTINUE** when upgrading. The existing save layout and map IDs are preserved; continuing a save inside the shop refreshes both clerks' script references for the new build. The earlier cave-footprint recovery remains active. Back up your cartridge save first; numbered emulator states remain tied to their exact ROM. Older immutable patches remain selectable.

Validation for v1.6: all 34 source/release tests pass, and clean application of all source scripts builds a byte-identical ROM with RGBDS 1.0.4. Compiled validation checks all 67 free stock entries, normal pricing elsewhere, all 320 old cave save positions, shop clerk script references, counter geometry and font protection. Native gameplay continued a v1.5 save inside the shop, bought each of the 50 TMs with money still zero, retained all seven HMs, and opened both the HM and supplies stocks. Complete playthrough remains unverified.

**New Bark Cave + Free Shop v1.5** adds a compact shop in the cave's **northwest corner**, leaving the center, east side and southern area open for future town buildings. Enter through the storefront door; the return door leads back to the cave. The lit cave and its Route 29 entrance remain.

Two stationary clerks stand behind the counter. **Left clerk:** all seven HMs (Cut, Fly, Surf, Strength, Flash, Whirlpool, Waterfall), free and reusable. Badge requirements for field use remain original. **Right clerk:** Potion, Super Potion, Hyper Potion, Full Restore, Revive, Full Heal, Poké Ball, Great Ball, Ultra Ball and Master Ball. Every listed item costs **¥0**, with the normal quantity selector and stack/bag limits. Only this shop has free pricing; other marts keep their original prices. Shop stock is unlimited. Existing story HM gifts and quest flags are unchanged.

The exterior adds one 4×4-tile building plot and a readable MART sign. It uses original Gold shop art in a cave-specific tileset; existing cave floor/walls and other maps' art are retained. Both merchants have separate scripts and inventories. The interior has a closed staff area and two reachable counter positions.

All previous map IDs, the cave's original exit, save layout, six-starter tracking, EXP options, and player features are preserved. The shop map and tilesets are appended. A v1.4 save made where the new building now stands is moved to the clear tile in front of the door on CONTINUE; other saved positions stay unchanged. Back up your normal cartridge save before changing patches. Saves inside the shop require v1.5 or newer; leave and save outside before reverting. Numbered states remain specific to their exact ROM.

Validation for v1.5: 29 source/release checks pass. A clean reapplication of the source scripts builds a byte-identical ROM with RGBDS 1.0.4. Compiled validation checks all 17 free stock entries, normal Potion pricing in other maps, all 320 possible previous cave save positions, both counter approaches and the inaccessible staff area, and protection of map font slots. Native gameplay bought all seven HMs, filled Potions to 99, rejected an extra full-stack purchase, bought a Master Ball, and returned to the cave with money still zero. A normal save inside the shop survived full emulator close/reopen with the purchased items retained. An actual v1.4 save at (3,3) loaded safely at (3,6) in front of the new building and allowed movement. Complete playthrough remains unverified.

**New Bark Cave v1.4** adds a single empty, fully lit chamber at the **east end of Route 29, immediately west of New Bark Town**. From town's west exit, walk a short way west, then north to the cave opening in the trees. It is reachable as soon as the original story lets you leave town after choosing your first starter. No Flash, badges, or HMs are needed. Enter northward and leave through the south entrance. The cave uses Route 29's Town Map location.

This is an empty test shell: **no wild encounters, trainers, NPCs, items, puzzles, or quest content**. It uses original cave graphics, a connected open floor and a single return warp. All six-starter and EXP-option features from v1.3 remain; browser controls, saves, speed settings and controller boost are unchanged.

Existing map IDs, the Route 29 gate warp, save layout and progress flags are preserved. The new map is appended to the New Bark map group; the only outdoor block change replaces previously impassable trees at its entrance. Normal v1.1–v1.3 cartridge saves are expected to work, with v1.3 tested. Back up your normal save before switching patches. **A save made inside the cave needs v1.4 or a later version containing that map**: leave the cave and save outside, or restore an older backup, before reverting to an older patch. Numbered emulator save states remain tied to their exact ROM.

Publication: v1.4 uses the successful private validation build's IPS, verified byte-for-byte against the native-tested local build, after the public build stalled during dependency installation. The standard immutable publisher generated its catalog entry. Static deployment now also watches `patches/**`.

Validation: RGBDS 1.0.4 compiled the release. Twenty-three source/release checks passed, including preservation of every old map ID, entrance-only outdoor changes, warp pairing, and a connected floor. A compiled ROM validator checks actual map pointers, daylight, original gate/paired cave warps, empty event tables and absent encounters. In native PyBoy gameplay from a v1.3 save with zero badges, the player walked from Elm's lab through New Bark to the cave, explored the room and its boundaries, exited to Route 29, saved inside, fully closed/reopened and returned to the same lit room with all six party members and the EXP setting retained. Full playthrough remains unverified.

**All Six Starters + EXP Options v1.3** adds **EXP GAIN** to the game's **START → OPTION** menu. Use Left/Right on that row to select **1x–10x**; the default is **1x**. The choice is stored with the normal game options and survives an in-game SAVE/reopen. It changes battle experience for eligible party members, including the existing EXP SHARE award path. It applies after the original trainer, traded-Pokémon, and Lucky Egg bonuses. Stat experience, fainted/link exclusions, and the level-100 cap keep their original behavior. It does not change browser gameplay speed or speed boost.

All v1.2 starter features remain. Existing save layout, option-block size, and previously named flags stay unchanged: the setting uses one formerly unused options byte, with zero meaning 1x. Old v1.1/v1.2 cartridge saves default to 1x; keep a downloaded backup before upgrading. Use CONTINUE from a normal cartridge save, not a numbered state from an older ROM. v1.0 migration remains unsupported. Older patches stay selectable.

Experience awards, their message, and the EXP bar now carry a full 24-bit amount, so large combined bonuses do not wrap at 65,535. The existing printer setting is retained; FRAME and EXP GAIN use compact rows to fit the added option. Complete playthrough remains unverified.

Validation for v1.3: RGBDS 1.0.4 builds successfully. Seventeen source/release checks pass. Compiled PyBoy validation checks 299 arithmetic cases, option cycling/wrap/invalid values, 32 trainer/traded/Lucky Egg combinations (including awards above 65,535), the common EXP SHARE path, fainted/link exclusions, and unchanged stat EXP. A native wild battle at 3x awarded 48 EXP instead of 16, increased the saved party member's experience from 135 to 183, and completed its level-up to 6. A v1.2 cartridge save opened with 1x; changing to 3x, saving in-game, fully closing and reopening retained 3x and all six starters.

**Collect All Six Starters v1.2** lets you return to Professor Elm to receive every Kanto and Johto starter once. The first choice and its dialogue follow v1.1. Afterward, speak to Elm again: his original quest/reward conversation runs first, then he asks how your Pokémon is doing and offers another companion. The menu contains only unclaimed species and shrinks after each successful gift. Remaining Poké Balls also open the repeat offer. Each gift is level 5 and holds a Berry. A full party leaves the gift available for later; canceling or declining consumes nothing. After all six, Elm confirms that you have them all.

Permanent event flags track gifts independently of your party and Pokédex, so evolving, depositing, releasing, or trading away a gift never makes it available again. Only the first choice sets the rival's original Johto counter type; later gifts do not change the rival, lab scene, or quest flags. Elm's original rewards and Mystery Egg hand-in remain available before the optional offer.

For an existing **v1.1** cartridge save, v1.2 initializes its claim flags from the Pokédex's permanent caught records the first time you use the starter menu/return offer. This conservatively removes any previously owned starter species, including trades, so an evolved or traded-away first partner cannot be claimed again. Existing event IDs and the SRAM layout are unchanged. Download a cartridge-save backup before switching patch versions. Numbered emulator states are tied to the exact ROM and are separate; do not transfer v1.1 save states to v1.2. Upgrading v1.0 is not supported.


Validation for v1.2: RGBDS 1.0.4 builds successfully. Thirteen automated source/release tests cover every collection order and remaining-menu row mapping, cancellation, full parties, migration, and unchanged event IDs. Native gameplay in PyBoy confirmed the first-starter story, menus shrinking from six to one, and exactly Bulbasaur, Charmander, Squirtle, Chikorita, Cyndaquil, and Totodile in the final party. A normal in-game SAVE survived a full emulator close and reopen with the unmodified release build; the party and all seven gift-tracking bits persisted. No ROM is distributed. Complete playthrough remains unverified.

**Kanto + Johto Six Starters v1.1** remains available as the one-starter release. Start a new game and interact with any of Elm's three Poké Balls to open a menu containing **Bulbasaur, Charmander, Squirtle, Chikorita, Cyndaquil, and Totodile**. Each choice has a picture, cry, and confirmation. B cancels; declining lets you inspect a different choice. You receive exactly one level-5 partner holding a Berry.

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

## Normal gameplay speed

Use **Player settings → Normal gameplay speed** to choose **1×–10×** in whole-number steps. The default is **1×**. This target is remembered separately from the existing **Speed boost (Space / toggle)** target. For example, normal **2×** and boost **8×** runs at 2× until Space is held or the mobile toggle is switched on, then runs at an absolute 8×; release/switch off to return to 2×. Changing normal speed during a boost takes effect when the boost ends. The boost target, keyboard hold behavior, mobile latch, focus/hide reset, and native input guards remain unchanged.

Normal speeds above 1× use the same native scheduler timing correction as the existing boost, and the status indicator reports target and measured speed. Hardware can limit the achieved rate. Switching normal speed back to 1× disables native fast-forward and restores the user's normal vsync preference. Normal speed is restored on startup; the boost On state is never remembered. No game-save or cloud behavior is added.

The speed regression suite covers both targets independently, all normal values, default/invalid saved settings, keyboard/touch transitions, normal-setting changes during a boost, rapid taps, focus/hide release, and returning to 1×. Existing boost tests continue to run.


Browser validation with stable EmulatorJS/legacy Gambatte: default ~60.3 fps; normal 2× ~119.0 fps; Space boost at an 8× target ~438.4 fps; release ~119.3 fps. The touch toggle reached ~457.7 fps, remained boosted while changing normal to 3×, then returned to ~178.8 fps when switched off. Reload remembered normal 3× and boost target 8× with boost Off; returning normal to 1× measured ~59.9 fps. Twenty speed regression tests pass; the existing boost activation function is unchanged.

## Space speed controls

Use **Player settings → Speed boost (Space / toggle)** to choose a target from 2× to 10×. Hold Space with the game focused; release it, move focus away, or hide the page to return to the selected normal gameplay speed. Your browser remembers the target. The indicator beneath the game reports both the target and the measured emulated-frame rate while held. Measured speed depends on device/browser capacity and can fall below the target.

The player resets the emulator's persisted fast-forward/slow-motion toggle modes at startup, hides the duplicate native speed settings, and ignores native speed hotkeys/gamepad inputs so they cannot conflict with Space. Other game and save controls remain available. The stable legacy core resets display scheduling on the frame after a speed toggle; Space applies its scheduler correction after that reset, then returns to the selected normal gameplay target on release (restoring the normal vsync preference at 1×). Pending transitions are canceled on release and focus loss so they cannot re-enable speed afterward.

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

## Keep the game in place

Held arrow keys are prevented from scrolling the page while the game has keyboard focus, including repeated keydown events that the stable emulator skips. Input still reaches the emulator. Outside the game, and in settings/form controls, browser navigation remains available. Touch gestures on the canvas and virtual controls stay with the game instead of panning the page; the surrounding page remains scrollable.

Browser validation with stable EmulatorJS/Gambatte reproduced 190 pixels of page scrolling while holding Down before this fix. The same held input after the fix kept the document position unchanged and delivered both direction press and release to the core. A real touchscreen drag through Chromium's input protocol also kept the document in place; arrow navigation outside the game still scrolled normally. Existing save, speed, numbered-state, and touch checks passed.

## Controller button for speed boost

Under **Player settings → Controller speed boost**, select **Assign controller button**, release all controller buttons, then press the paddle/button you want. Connect your controller and press a button first if the browser has not detected it. Assignment can be made before or after starting a game. Hold the assigned button to use the existing boost target and release to return to the chosen normal gameplay speed. The binding is remembered in this browser, independently of the normal/boost multipliers.

Some 8BitDo back paddles mirror other buttons instead of appearing as independent browser inputs. If the paddle is not detected, use your controller's supported 8BitDo remapping software to assign it an unused button, such as a stick click, then bind that input in the player. A mirrored paddle and its original button share the assignment. The player reserves that input for boost so it does not also press A/B or another emulator action. Other buttons and axes continue to work normally. **Clear controller assignment** restores normal input handling; **Cancel assignment** keeps the old binding.

Space, the mobile toggle, and controller hold share the same proven boost scheduler. Releasing one held source leaves another active source running. The toggle can turn an active boost off. Blur, hiding, pause/settings/form focus, or a controller disconnect releases the controller hold; it must be released physically before a new press can enable it again. Assignment also waits for release, so the binding press does not start boosting. Only the selected binding is saved, never its held state. Browser/game saves and no-save-on-hide/unload behavior are unchanged.

Validation: seven controller-model checks plus 23 speed checks cover assignment, storage, reconnects with changed device indices, identity matching, cancellation/timeouts, native input reservation, source ownership, and speed restoration. In Chromium with a simulated Gamepad API device and actual stable EmulatorJS/legacy Gambatte, assignment to button 19 held the 5× boost at ~291.3 fps, release restored normal 2× at ~120.3 fps, the assigned native A action was suppressed, another button still reached the core, blur/disconnect required a fresh press, and reload restored the binding with boost Off. A physical 8BitDo controller was not available for validation; paddle visibility depends on the model, mode, and firmware.
