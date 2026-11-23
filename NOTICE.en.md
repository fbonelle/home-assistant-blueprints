# Attribution and license

[Français](NOTICE.md) · **English**

## Battery watch

A separate implementation, released under this collection's GPL-3.0 license. Its fixed-time summary, weekday selection and persistent notification follow ideas from the **Low Battery Notifications & Actions** blueprint by **Blackshome**. No code was copied from it: that blueprint is published without a stated license.

- [Original blueprint](https://gist.github.com/Blackshome/4010fb83bb8c19b5fa1425526c6ff0e2)

Silent-device detection, alert memory, the recovery margin and exclusions by integration and manufacturer are specific to this collection. Examples use fictional identifiers.

## Integration watchdog

Work on this blueprint started from **Reload Integrations Automatically**, by **danimart1991**:

- [Original project](https://github.com/danimart1991/home-assistant-blueprints)
- [Original blueprint](https://github.com/danimart1991/home-assistant-blueprints/blob/main/automation/reload-integrations/reload-integrations.en.yaml)
- License: GNU General Public License, version 3, retained in [LICENSE](LICENSE).

This implementation has been extensively reworked and is maintained separately. Its changes must not be attributed to the original project’s author.

**Version 1.0.0** is the first version published in this collection, on 4 November 2026. Examples use fictional identifiers and do not configure a real installation.

## Lighting remotes and automatic switch-off

Original implementation in this collection, published under GPL-3.0. It replaces third-party blueprints used before; none of their code was reused. The ideas of per-model remotes and hold dimming come from these blueprints:

- [IKEA 5 buttons, whites and presets](https://github.com/niro1987/homeassistant-config/tree/main/blueprints/automation/niro1987), by **niro1987**;
- [Philips Hue Tap Dial](https://github.com/apollo1220/blueprints/blob/main/philips_zigbee_dial.yaml), by **apollo1220**;
- [IKEA on/off switch](https://community.home-assistant.io/t/zha-ikea-tradfri-on-off-switch-incl-dimmer/255412) and [Philips Hue Dimmer RWL022](https://community.home-assistant.io/t/zha-philips-hue-v2-smart-dimmer-switch-and-remote-rwl022/353143), posted on the Home Assistant forum.

The idea of a switch-off timer comes from the [**Manual Light**](https://gist.github.com/Blackshome/9f9785d7aa0ba7978fa6515a2d73d192) blueprint by **Blackshome**, published with no stated licence.

Event formats are those of the [zha-quirks](https://github.com/zigpy/zha-device-handlers) profiles (Apache 2.0 licence), read for compatibility; none of their code is reused. In the palette, 21 colours are the values of a personal helper by the author. Three others are the Home Assistant reference whites, in RGB, taken from a screenshot supplied by the author, with no kelvin estimate. The numerical coordinates of the 20 TRÅDFRI presets come from [node-tradfri-client's recording of the app presets](https://github.com/AlCalzone/node-tradfri-client/blob/master/src/lib/predefined-colors.ts), an MIT-licensed project by AlCalzone; only these colour values are reused.

Philips Hue, IKEA, TRÅDFRI, STYRBAR, eWeLink, SONOFF and Aqara identify compatible devices; this project is not affiliated with any of these manufacturers. Examples use fictitious identifiers.

## Notification system

Original implementation in this collection, published under GPL-3.0. It turns an existing personal notification system by the same author into blueprints. Examples use fictitious identifiers.
