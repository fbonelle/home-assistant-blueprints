# Changelog

[Français](CHANGELOG.md) · **English**

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
