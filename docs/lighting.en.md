# Lighting remotes and automatic switch-off

[Français](lighting.md) · **English**

A family of blueprints that drive lamps the same way whatever the ZHA remote, plus an automatic switch-off blueprint. The forms are in French.

| Blueprint | Devices | Gestures |
|---|---|---|
| [Philips Hue Dimmer remote](../blueprints/automation/lighting/telecommande_hue_dimmer.yaml) | RWL022 | On/Off, Up, Down, Hue: short press and hold |
| [Philips Hue Tap Dial remote](../blueprints/automation/lighting/telecommande_hue_tap_dial.yaml) | RDM002 | 4 buttons (one lamp each): short press and hold; dial |
| [IKEA TRÅDFRI on/off switch](../blueprints/automation/lighting/telecommande_ikea_marche_arret.yaml) | TRADFRI on/off switch | I and O: short press, double press, hold |
| [IKEA TRÅDFRI 5-button remote](../blueprints/automation/lighting/telecommande_ikea_5_boutons.yaml) | TRADFRI remote control | Centre, Up, Down, Left, Right: short press, double press, hold |
| [IKEA STYRBAR remote](../blueprints/automation/lighting/telecommande_ikea_styrbar.yaml) | Remote Control N2 | Up, Down, Left, Right: short press, double press, hold |
| [eWeLink / SONOFF button](../blueprints/automation/lighting/bouton_ewelink.yaml) | WB01, SNZB-01P, CK-TLSR8656-SS5-01 | Single, double and long press |
| [Aqara wireless button](../blueprints/automation/lighting/bouton_aqara.yaml) | lumi.remote.b1acn01 (WXKG11LM) | Single press, double press, hold |
| [Automatic lighting switch-off](../blueprints/automation/lighting/extinction_automatique.yaml) | Lights, switches, plugs | — |

The STYRBAR blueprint keeps every feature and every default of this collection's former STYRBAR blueprint, which it replaces.

## Installation

1. Import the blueprints you need:
   [Hue Dimmer](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flighting%2Ftelecommande_hue_dimmer.yaml) ·
   [Hue Tap Dial](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flighting%2Ftelecommande_hue_tap_dial.yaml) ·
   [IKEA on/off](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flighting%2Ftelecommande_ikea_marche_arret.yaml) ·
   [IKEA 5 buttons](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flighting%2Ftelecommande_ikea_5_boutons.yaml) ·
   [IKEA STYRBAR](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flighting%2Ftelecommande_ikea_styrbar.yaml) ·
   [eWeLink](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flighting%2Fbouton_ewelink.yaml) ·
   [Aqara](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flighting%2Fbouton_aqara.yaml) ·
   [Automatic switch-off](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flighting%2Fextinction_automatique.yaml).
2. Create one automation per remote: pick the remote, the lamp, then the action of each gesture.
3. Optional: pick a **memory helper** (see below).
4. Check with **Menu → Run actions**: a notification describes the lamp, the memory and any problem, without commanding the lamp.

The [example](../examples/lighting/automations.yaml) shows a typical setup of each blueprint.

## Memory helper (optional)

A **Text helper** with a maximum length of 255, used by one automation only.

| | Without helper | With helper |
|---|---|---|
| Every action, bounded holds, filters, diagnostic | yes | yes |
| Double press (IKEA) | no | yes |
| Palette position | preset closest to the displayed colour | exact position, resynchronised if the colour was changed elsewhere |
| Hold release | the change stops, the lamp finishes its last fade | the lamp is frozen at the level actually reached |
| Radio duplicate | any gesture too close to the previous one is dropped | only an identical gesture is dropped |
| Hold repeated by the remote | ignored while the change runs | ignored; a hold in the other direction takes over at once |
| Out-of-order event | — | dropped |

The helper is written at the start of every gesture. Excluding it from the `recorder` avoids storing it at each press.

An unreadable helper, or one already used by another automation, is never modified. A notification reports it and the remote works without memory. To reuse it, clear it while the automation is disabled.

## Actions available for each gesture

| Action (French label) | Effect |
|---|---|
| Aucune action | The gesture is ignored and never interrupts a running change. |
| Basculer marche/arrêt | Turns on (brightness remembered by the lamp) or off. |
| Basculer, en allumant au niveau d’allumage | Turns off, or turns on at the **on level**. |
| Allumer · Éteindre | Turn on · turn off. |
| Allumer au niveau d’allumage | Turn on at the on level. |
| Pleine luminosité | 100 %, colour unchanged. |
| Pleine luminosité et couleur de référence | 100 % and the first palette preset; for a white-only lamp, the **reference white**. |
| Couleur de rappel | The chosen **recall colour**, brightness kept. |
| Alterner entre niveau d’allumage et niveau haut | Off → on level; on below the high level → high level; at the high level → on level. |
| Augmenter / Baisser la luminosité d’un pas | Lamp off: Up turns it on, Down does nothing. Dimming stops at the minimum brightness and never turns off. |
| … en continu *(holds)* | Change until release, end stop or maximum duration. Up on a lamp that is off starts at the minimum brightness. |
| Blanc plus froid / plus chaud | Colour temperature in kelvin, bounded by the lamp limits; one step or continuous. |
| Préréglage de couleur suivant / précédent | See the memory helper for the position. Lamp off: first preset. One step or continuous. |
| Action personnalisée | Runs the actions entered under the gesture; the `gesture` variable holds the gesture name. |

Continuous actions are offered for holds only. **Double press** on IKEA remotes needs the memory helper, because their firmware does not report it: the first press acts at once, the second runs the double-press action. The eWeLink and Aqara buttons report their double press themselves, with no helper.

## Common settings

In the collapsed section **Réglages de variation et de couleur**. Values in brackets are model-specific defaults.

| Setting | Default | Purpose |
|---|---|---|
| Brightness step | 10 % (IKEA 5 buttons: 20 %) | Single-step presses. |
| Speed while holding | 0 (STYRBAR: 35 %/s) | In %/s; 0 uses the step while holding. |
| Step while holding | 10 % | Used when the speed is 0. |
| Brightness interval | 0.5 s (STYRBAR: 0.3 s; IKEA on/off: 1 s) | Interval of brightness commands while holding. |
| Colour and white interval | 0.5 s (STYRBAR: 0.4 s) | Interval of presets or temperature steps while holding. |
| Maximum hold duration | 10 s (STYRBAR: 15 s) | Stops if the radio release is lost. |
| Smooth dimming | yes | Each step fades until the next one. |
| Minimum · maximum brightness | 1 % · 100 % | End stops. |
| On level · High level | 50 % · 100 % (eWeLink: 25 % · 100 %) | Fixed-level switch-on and alternate. |
| Brightness fade | 0 s (Tap Dial, IKEA on/off: 1 s; IKEA 5 buttons: 0.5 s) | Switch-on, switch-off, single steps. |
| Colour fade | 0 s (STYRBAR: 0.3 s; IKEA 5 buttons: 0.5 s) | Colours, whites, recall. |
| Temperature step · Reference white | 250 K · 2,500 K | — |
| Colour presets | 21 presets (STYRBAR: the former blueprint's 16) | Cycling order among 44; the first is the reference colour. |
| Recall colour | RGB 255, 192, 140 | — |
| Colours may switch on · Recall may switch on | yes · yes | Otherwise no effect on a lamp that is off. |
| Double press delay | 800 ms | Memory helper required. |
| Ignore events too close together | 0 (STYRBAR: 50 ms; Tap Dial: 100 ms) | Must stay below the double press delay. |
| Logging | no | INFO level, `lighting_remote` logger. The automation sets this level itself: no configuration is needed. |

On the Tap Dial, the dial sends an amount that grows with rotation speed: about 3 % for a slow notch, up to 80 % for a fast spin. **Sensibilité de la molette** scales it (1 by default). The 100 ms filter drops presses received twice and contradictory rotation reports a few milliseconds apart. Without a memory helper, it measures the gap from the start of the previous gesture’s processing: when Home Assistant is heavily loaded, a real gesture that follows the previous one very closely may also be dropped.

An inconsistent configuration (minimum above maximum, unknown preset, black recall colour, filter longer than the double press delay, helper too short) blocks every command. It is reported by a notification and in the log.

## Behaviour

- **A release stops the change.** The automations run in *restart* mode: a release or another recognised gesture stops the running change. Events with no action are filtered out before starting and never interrupt anything: release of a short press, state report, Tap Dial duplicate scene event, event older than 5 seconds.
- **Philips remotes repeat the hold event.** Each repetition makes one step. IKEA remotes send only a start and an end, so the change runs at the configured interval.
- **The lamp state is read again at every step.** A lamp switched off during a hold is not switched back on by it. A lamp that becomes unavailable ends the change. A change made elsewhere is respected and the release does not overwrite it.
- **Colours stop a running effect** (colorloop) when the lamp allows it.
- **The Tap Dial dial** drives the lamp switched on most recently among the four; if all are off, the lamp switched most recently; an unavailable lamp is never chosen. When lamps follow one another, such as a group and its members, the lamp the remote commanded wins: a member’s button then the dial drives that member alone, the group’s button then the dial drives the group. A lamp switched on otherwise more than 2 seconds later still comes first.
- **The eWeLink button** is read from its commands (single, double, long). `attribute_updated` state reports are ignored: the button can send them with no press.
- **The Aqara button** reports single press, double press, and the start and end of a hold itself. It does not repeat the hold: dimming runs at the set rate until release, or until the maximum duration if the radio release is lost. By default only the single press has an action (toggle).

## Automatic switch-off

- Pick the lights, the duration and, optionally, a dedicated **Timer helper**.
- Any switch-on, by any means, restarts the countdown. Switching every light off by hand cancels it. When the countdown ends, lights still on are switched off.
- When Home Assistant starts, a light left on with no active countdown starts the countdown again.
- With a Timer helper, the remaining time is visible. Enable its *Restore* option so it survives a restart.
- Without a helper, the automation waits by itself. A restart interrupts the wait, which resumes at the next start.

## Moving from the former blueprints

| Former setup | New setup |
|---|---|
| Hue Dimmer: Power → `light.toggle` · Up/Down → `brightness_increase`/`decrease` · Hue → 100 % | Hue Dimmer defaults. Hue button with no action: short press = *Aucune action*. |
| Tap Dial: 4 lamps, `input_text` current-lamp helper, scale | The 4 lamps and the dial sensitivity. The helper is no longer used. |
| IKEA on/off: 1 s fade, hold of 10 × 10 % per second | 1 s fade, 1 s interval, 10 % step, 10 s maximum. |
| IKEA 5 buttons “presets” + `input_select` | Defaults; the palette replaces the `input_select`. |
| IKEA 5 buttons “whites” | Left: warmer, Right: cooler (press and hold), reference white 2,500 K. The former blueprint used the `color_temp` parameter in mireds, which Home Assistant 2026.10 no longer accepts. |
| STYRBAR: Text helper, `styrbar_maintiens` script | Same defaults. Keep the same helper for the double press: its former content is replaced at the first gesture. Disable the former automation first. The script is no longer needed. *Recall on right / left hold*: pick *Couleur de rappel* for that hold. *Brightness forced on Up*: action *Allumer au niveau d’allumage*. |
| Aqara automation on the “single press” device trigger | Aqara blueprint defaults; carry the former transition over to *Fondu de la luminosité*. |
| eWeLink automation on `attribute_updated` | Single press: toggle at a 25 % on level; double press: alternate 25 % / 100 %. |
| Lighting timer (manual light) | Automatic switch-off with the same Timer helper and duration. |

## Limits

- Event formats come from the zha-quirks profiles (release 2.4.1 for the Philips, IKEA and eWeLink remotes; the SwitchAQ3B profile, unchanged since, for the Aqara button) and from the house’s traces. A different firmware may name a gesture differently: the gesture is then ignored, never misread.
- Without a memory helper, the palette position is deduced from the displayed colour. A bulb that renders a colour poorly may show it closer to a neighbouring preset; the next arrow would then skip a preset. Trying the whole palette on the lamp shows it; the memory helper removes this risk.
- Without a memory helper, a new hold is ignored while the previous one is still running, for example after a lost radio release. A short press on a button that has an action stops it.
- The level frozen on release is estimated from the requested fade; each bulb’s actual rendering may differ slightly.
- Tests simulate the radio. Real lamp rendering and hold repetition rates are not certified.
