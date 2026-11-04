# Light with IKEA STYRBAR remote — ZHA

[Français](ikea_styrbar_light.md) · **English** · [Home](../README.en.md)

Version **1.1.0**. One blueprint per light replaces the controller + hook pair. It uses standard Home Assistant features, with no custom integration or shared scripts to install. The blueprint form uses French labels; key labels are included below.

## Installation

1. Use Home Assistant **2026.10 or later**, a **ZHA** STYRBAR remote (`Remote Control N2`) and a color-capable light. This blueprint does not support Zigbee2MQTT or deCONZ.
2. [Import the blueprint](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fikea_styrbar_light%2Flampe_styrbar.yaml).
3. Under **Settings → Devices & services → Helpers**, create a **Text** helper with minimum length **0** and maximum **255**. Reserve it for this automation. Each additional remote requires a separate helper.
4. Create an automation from the blueprint. Select the remote (**Télécommande STYRBAR**), light (**Lampe couleur à piloter**) and helper (**Assistant Texte réservé à cette télécommande**). Choose the palette and recall color.
5. Before enabling the new automation, disable the old controller and hook automations for this remote. Also check for direct Zigbee bindings or other automations controlling the same light.

The [automation examples](../examples/ikea_styrbar_light/automations.yaml) and [YAML helper examples](../examples/ikea_styrbar_light/helpers.yaml) contain fictional identifiers only. Helpers created in the UI are sufficient: the YAML helper file is optional. Adapt the blueprint path if Home Assistant offers a different filename during import.

## Checking capabilities during setup

The standard blueprint form cannot run a test when selecting a bulb or reject saving based on its attributes. Checks run after activation/reload, before commands, and when the light's capabilities or availability change. An incompatibility blocks commands and creates a Home Assistant notification for that automation. An unavailable light is reported as pending verification, not as incompatible.

To see a positive result too, use the automation's **Menu → Run actions** (**Exécuter les actions**). This displays a diagnostic only: connectivity, dimming, colors, palette whites, a separate white channel, native color-temperature mode and its Kelvin range when available, and transitions. It does not command the light or interrupt a valid hold. Problem notifications are dismissed after a successful automatic recheck.

An IKEA bulb declaring only `xy` can produce palette whites in color mode. Missing `color_temp` therefore does not make it incompatible. A tunable-white bulb with no color mode is rejected by this blueprint because its palette and recall use RGB/xy. Transition support is optional: without it, dimming uses steps and no transition parameter is sent.

These checks use integration metadata. They do not verify physical output or radio reliability; a group's aggregate capabilities do not certify each member. Saving never sends a lighting test automatically.

## Buttons

| Gesture | Result |
|---|---|
| Short up press | Turn on, retaining the light's remembered color and brightness. A fixed turn-on brightness is optional. |
| Short down press | Turn off. |
| Hold up | Increase brightness; when off, start at the configured minimum. |
| Hold down | Decrease to the configured minimum without switching off. Does not wake an off light. |
| Short left / right press | Previous / next palette entry, wrapping around the list. |
| Double up press | Recall the configured color without imposing brightness. |
| Hold right | Same recall by default. This additional gesture can be moved to the left or disabled. |
| Release or another recognized button | Stop the ongoing dimming gesture. |

The first up press acts immediately. The second recalls the color if received within the configured window. With a fixed turn-on brightness, the first press applies it before the recall; the recall does not impose it again. **Les flèches de couleur peuvent allumer la lampe** and **Le rappel de couleur peut allumer la lampe** independently allow palette changes and recall to turn on an off light.

**Double up depends on the remote firmware.** Some STYRBAR versions filter rapid ON/OFF presses before transmission. If ZHA receives only one `on` event, no blueprint can distinguish two presses. Hold right provides recall without that dependency. The [STYRBAR documentation](https://www.zigbee2mqtt.io/devices/E2001_E2002_E2313.html#action-mapping) describes this device-level filtering; this ZHA blueprint does not use its MQTT action names.

Some firmware also emits `on` during a lateral hold. This may turn the light on before the hold event arrives. Avoid that gesture if an off light must never be awakened: this radio command is indistinguishable from a real ON press.

## Palette and recall color

There are **23 choices**: the three Home Assistant screenshot reference whites plus 20 historical IKEA presets (seven whites and thirteen colors). The initial palette contains the three reference whites and thirteen IKEA colors. Select the additional IKEA whites in the form if wanted.

| Reference swatch | RGB sent to Home Assistant |
|---|---|
| Left — default | `255, 192, 140` |
| Middle | `255, 228, 206` |
| Right | `255, 254, 250` |

These values reproduce the solid swatches of the supplied reference screenshot. They are not inferred Kelvin values or an automatic reading of your favorites. Home Assistant favorites depend on the light's capabilities and user customization. Editing them does not change this blueprint's palette.

**Couleur de rappel** accepts any RGB color independently of the palette. IKEA presets are sent using their recorded **xy** coordinates, rather than their decorative RGB swatches. [Reference coordinates](https://github.com/AlCalzone/node-tradfri-client/blob/master/src/lib/predefined-colors.ts) · [IKEA palette documentation](https://www.ikea.com/jp/en/manuals/tradfri-starter-kit-smart-wireless-dimmable-colour-and-white-spectrum__AA-2302838-3-100.pdf).

A palette change or recall stops `colorloop` when the light exposes an `off` effect command. A black recall color is rejected because it could turn the light off.

The saved selection order defines cycling order. Reorder the `palette` list directly in YAML if needed. Empty lists, unknown presets and duplicates are rejected. After an external color change, cycling continues from the closest actual color in the configured palette. Without available color information, right starts at the beginning and left at the end. Physical output still depends on the bulb and its color gamut.

## Settings and logging

Brightness steps, dimming bounds, fixed turn-on brightness, step interval, maximum hold duration, transition, double-press window and duplicate filtering are configurable. Dimming bounds apply to dimming gestures; they do not restrict changes from the app or the fixed turn-on brightness.

**Lisser la variation pendant un maintien** enables smooth dimming by default. A target is sent at most once per second, or more slowly with a larger interval, while the bulb performs a native fade over that interval. The gesture starts immediately, then follows clock boundaries to avoid two-second pauses caused by the initial press offset. Speed is the step divided by the interval, approximately ten brightness percentage points per second by default. Fade duration is capped at the remaining hold time.

At release or direction reversal, Home Assistant often already advertises the target while the bulb is still fading towards it. The blueprint estimates the intermediate level from the last fade and, on release, sends it with a zero transition. This assumes linear fading: it improves stopping but does not measure physical output. An identifiable external change invalidates that estimate to avoid overwriting it. Smoothing can be disabled. **Durée de transition des changements de couleur** controls color changes independently.

**Journaliser les boutons et les actions** adds INFO messages to `ikea_styrbar_light`. To see them in the full log, merge this into your existing logger configuration:

```yaml
logger:
  logs:
    ikea_styrbar_light: info
```

Configuration errors are reported on use or reload. Command failures remain reported by Home Assistant even with optional logging disabled. Invalid periodic ticks do not flood the log. This blueprint does not create repeated notifications.

## Resilience and limitations

- Each remote's commands are serialized (`queued`, maximum 30 runs). Different lights remain independent. At most one light call is in progress per automation.
- Release stops dimming. A maximum hold duration also stops it if the release packet is lost. Repeated hold packets do not accelerate steps or extend that deadline. If release is lost, briefly press another button before starting an identical hold again.
- The hold is disarmed before every light call. A failed or interrupted call cannot leave further automatic steps armed.
- An unavailable light cancels the gesture. Reconnection does not replay a command. Buttons queued for more than five seconds are discarded; a late release can still stop a gesture. Out-of-order events are ignored.
- Switching off from the app also stops a hold; the periodic check does not turn the light back on.
- Startup, reload, re-enabling the automation and backward clock corrections do not resume old holds. An external app change invalidates the stored palette cursor.
- Unknown events and battery updates do not cancel a hold. Numeric and textual `MoveMode.Up/Down` variants are supported.
- A hold reaching a brightness bound remains identifiable until its last fade finishes, so release can still stop it partway through. Command failure always disarms subsequent steps.
- Memory is associated with the automation, remote and light. Corrupt or differently owned data blocks commands without being overwritten. To change this association, stop the automation, clear its dedicated helper and re-enable it. Never share a helper: the ownership check is not a distributed lock for two brand-new automations starting simultaneously.
- Home Assistant is not a real-time system. A slow radio call can delay release handling until the integration finishes or times out. The hold deadline blocks subsequent steps; it cannot revoke a command already sent to a bulb.

Tests run this blueprint in an **isolated Home Assistant 2026.10.4**, with actual automations, native light services and Text helpers. Radio and rendering are simulated, using a linear fade model independent of blueprint memory. Coverage includes different capability modes, diagnostics without commands, mid-fade release, direction reversal, cadence, double presses, brightness bounds, repeated or delayed packets, missing release, command failures, external changes and independent remotes. These tests do not prove physical radio reception or bulb color output. Publishing this repository does not modify a real installation's automations.

Updating from 1.0.0 preserves existing inputs and the Text helper. Last-fade information is added automatically. Reloading cancels the current gesture without changing the light.
