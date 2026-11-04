# Changelog

[Français](CHANGELOG.md) · **English**

## STYRBAR light — 1.2.0 — 4 November 2026

- Explicit brightness speed in percentage points/second, initially 35: approximately 3 seconds across the full range.
- Continuous left/right palette cycling with an independent color interval, initially 0.4 seconds.
- A small native YAML script provides fast pulses. Install `packages/ikea_styrbar_light.yaml` before the blueprint; no custom integration.
- Stale and foreign pulses are rejected; release and timeout stop the hold. The shared script never commands a light.
- Double up retains recall. Lateral recall is optional because it replaces cycling on that side.
- Legacy step/interval settings remain in an advanced section for speed 0. Native tests cover both hold types and the actual shared script.

## STYRBAR light — 1.1.0 — 4 November 2026

- Capability checks at activation, before commands and when availability or capabilities change.
- Manual diagnostic through “Run actions”, without lighting commands: dimming, colors, palette whites, white channel, native temperature and transitions.
- IKEA `xy` lights retain palette whites; non-color lights are rejected and unavailable lights remain pending verification.
- Native hold fading, clock-aligned cadence and estimated intermediate-level stopping on release or direction reversal.
- Independent color transitions, step fallback without fade support, automatic reuse of 1.0.0 memory.
- Tests using an independent fade model and bilingual documentation of setup and measurement limits.

## STYRBAR light — 1.0.0 — 4 November 2026

First published version of **Light with IKEA STYRBAR remote — ZHA**.

- One blueprint per light, with a dedicated Text helper and no shared package.
- On/off, bounded hold dimming, 23 available presets and configurable RGB recall.
- Three Home Assistant reference whites; historical IKEA colors and whites sent as xy.
- Double up when the firmware sends two events, plus a configurable lateral hold for recall.
- Serialized commands, missing-release deadline, stale-command rejection and cancellation after failures or unavailability.
- French and English documentation, fictional examples and isolated native tests.

## Integration monitoring — 1.0.1 — 4 November 2026

- Fix script loading from a Home Assistant package: field selectors now survive configuration merging.
- Add a regression test that merges the package with an existing configuration and validates every script.

## Integration monitoring — 1.0.0 — 4 November 2026

First published version of **Integration monitoring and reload**.

- Setup through the Home Assistant form, with a Text helper to retain history.
- Up to 50 simultaneous reloads; requests wait without consuming a retry when all slots are busy.
- Configurable retry counts and delays, notifications, logging, exclusions and observation mode.
- Protection against duplicate reloads and retained results after interruption.
- Fictional Netatmo, TaHoma and Cozytouch examples.
- French and English documentation, 88 tests and automated GitHub Actions checks.

Each blueprint’s version is stored in `src/<name>/VERSION`. Development revisions do not represent published releases.
