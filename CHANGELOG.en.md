# Changelog

[Français](CHANGELOG.md) · **English**

## Lighting remotes — 1.0.2 — 15 November 2026

- Fix: the Hue Tap Dial dial amount was read as a percentage, whereas the Zigbee command expresses it in brightness units (0 to 255); a fast spin jumped straight to maximum or minimum. It is now converted: about 3 % for a slow notch, up to 80 % for a fast spin.
- Tap Dial: filter for events too close together enabled by default (100 ms). It drops presses received twice and opposite-direction rotation reports a few milliseconds apart.
- Tests using values recorded on a real remote.

## Lighting remotes — 1.0.1 — 15 November 2026

- Fix: the Hue Tap Dial dial was always read in the same direction with a fixed step. ZHA sends the rotation direction and other fields as zigpy enums (`StepMode.Down`), which Home Assistant 2026.11 could not read back: every event parameter was lost. Values are now converted to numbers, booleans or text before use, for every remote.
- Test reproducing the real zigpy values.

## Lighting remotes and automatic switch-off — 1.0.0 — 15 November 2026

First published version of the **Lighting remotes** family (*Télécommandes d’éclairage*) and of the **Automatic lighting switch-off** blueprint (*Extinction automatique de l’éclairage*).

- One blueprint per ZHA model: Philips Hue Dimmer (RWL022), Philips Hue Tap Dial (RDM002), IKEA TRÅDFRI on/off switch, IKEA TRÅDFRI 5-button and STYRBAR remotes, eWeLink / SONOFF button.
- Removal of the former **Light with IKEA STYRBAR remote** blueprint, its shared script, examples and tests: the family's STYRBAR remote replaces it.
- STYRBAR: every feature and default of the former blueprint (double press, recall colour, speed in %/s, separate intervals, freeze at the level reached, duplicate filter, diagnostic), with no shared script; the former Text helper is taken over as is.
- Optional memory helper: double press on IKEA remotes, exact palette position, out-of-order events dropped, freeze at the level reached; an unreadable or shared helper is never overwritten.
- Diagnostic through “Run actions” and configuration checks for every remote.
- A shared engine built in: the same action list for every gesture, the same settings, a custom action per gesture.
- Continuous changes bounded by a maximum duration; a release or another gesture stops them; events with no action interrupt nothing.
- Dimming limited to a minimum, never switching off; white temperature in kelvin, bounded by each lamp's limits.
- 44-preset palette sent in each preset's original format; without memory, the next preset is deduced from the lamp's current colour.
- Tap Dial: the dial drives the lamp switched on most recently, with no memory helper.
- eWeLink button read from its commands, never from state reports.
- Automatic switch-off with or without a Timer helper, cancelled by a manual switch-off and resumed at start-up.
- Native Home Assistant 2026.10.4 tests with real lights, real timers and the zha-quirks event formats.

## Notification system — 1.0.0 — 15 November 2026

First published version of the **Notification system** (*Système de notifications*), in four blueprints: dispatcher, channel sender, speech and mobile relay.

- Single entry point with the title, message, level, target, entity_id, tts and data fields; configurable channels per level (mobile app, ntfy, e-mail) and logbook.
- Each channel is sent by a separate script returning “success”: fallback from ntfy to the mobile app, warning when the e-mail fails, without blocking the other channels.
- Duplicate filter over a fixed window and 10 remembered messages; a level escalation always goes through; an unreadable memory never blocks.
- Silent nights, breaking through silent mode for critical messages (iOS and Android), links and attachments adapted to each channel, sys_disp_ IDs normalised once for 1:1 clearing.
- Queued speech on labelled speakers, volume and restore for critical messages, mute switch.
- Relay of persistent notifications with the level taken from the title, loop-free, with never-relayed and automatically dismissed prefixes.
- Native Home Assistant 2026.10.4 tests with the four blueprints together.

## Battery monitoring — 1.0.0 — 12 November 2026

First published version of **Battery monitoring** (*Surveillance des piles et batteries*).

- Immediate alert, once per device: battery below the threshold, device silent beyond a delay, binary “battery low” alert.
- Memory in a Local To-do list with no size limit: no new alert when a battery keeps dropping, oscillates around the threshold or becomes unavailable during a restart. A checked item leaves the summary until replacement; manually added items are ignored.
- Summary at the selected time and days, manual sending through “Run actions”, persistent notification kept up to date.
- Default exclusion of phones, watches, computers and UPS units (mobile_app, icloud, icloud3, nut, Apple), extendable by entity, device or label.
- Free notification actions with title, message and lists provided; optional additional conditions.
- Native Home Assistant 2026.10.4 tests: real registries, memory, exclusions, summary, checked items and 80 simultaneous devices.

## STYRBAR light — 1.0.0 — 4 November 2026

First published version of **Light with IKEA STYRBAR remote — ZHA**.

- One blueprint per light, with a dedicated Text helper, plus a small native YAML script for fast pulses. Install `packages/ikea_styrbar_light.yaml` before the blueprint; no custom integration.
- On/off, 23 available presets and configurable RGB recall. Three Home Assistant reference whites; historical IKEA colors and whites sent as xy.
- Explicit brightness speed in percentage points/second, initially 35: approximately 3 seconds across the full range. Legacy step/interval settings in an advanced section for speed 0.
- Continuous left/right palette cycling with an independent color interval, initially 0.4 seconds. Double up retains recall; lateral recall is optional because it replaces cycling on that side.
- Capability checks at activation, before commands and when availability or capabilities change. Manual diagnostic through “Run actions”, without lighting commands. IKEA `xy` lights retain palette whites; non-color lights are rejected and unavailable lights remain pending verification.
- Native hold fading, clock-aligned cadence and estimated intermediate-level stopping on release or direction reversal. Independent color transitions, step fallback without fade support.
- Serialized commands, stale and foreign pulse rejection, stop on release or hold timeout, cancellation after failures or unavailability. The shared script never commands a light.
- French and English documentation, fictional examples and isolated native tests, using an independent fade model and the actual shared script.

## Integration monitoring — 1.0.0 — 4 November 2026

First published version of **Integration monitoring and reload**.

- Setup through the Home Assistant form, with a Text helper to retain history.
- Up to 50 simultaneous reloads; requests wait without consuming a retry when all slots are busy.
- Configurable retry counts and delays, notifications, logging, exclusions and observation mode.
- Protection against duplicate reloads and retained results after interruption.
- Shared scripts loaded from a Home Assistant package, with field selectors preserved after configuration merging.
- Fictional Netatmo, TaHoma and Cozytouch examples.
- French and English documentation, 89 tests and automated GitHub Actions checks.

Each blueprint’s version is stored in `src/<name>/VERSION`. Development revisions do not represent published releases.
