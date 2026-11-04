# Attribution and license

[Français](NOTICE.md) · **English**

## Integration monitoring

Work on this blueprint started from **Reload Integrations Automatically**, by **danimart1991**:

- [Original project](https://github.com/danimart1991/home-assistant-blueprints)
- [Original blueprint](https://github.com/danimart1991/home-assistant-blueprints/blob/main/automation/reload-integrations/reload-integrations.en.yaml)
- License: GNU General Public License, version 3, retained in [LICENSE](LICENSE).

This implementation has been extensively reworked and is maintained separately. Its changes must not be attributed to the original project’s author.

**Version 1.0.0** is the first version published in this collection, on 4 November 2026. Examples use fictional identifiers and do not configure a real installation.

## Light with IKEA STYRBAR remote

A separate implementation, released under this collection's GPL-3.0 license. No code was copied from the previously used controller/hook blueprints.

Numerical coordinates for the 20 TRÅDFRI presets come from [node-tradfri-client's recording of the app presets](https://github.com/AlCalzone/node-tradfri-client/blob/master/src/lib/predefined-colors.ts), an MIT-licensed project by AlCalzone. Only numerical color values are reused. The three reference Home Assistant RGB colors match the solid swatches of the supplied screenshot; no Kelvin estimate is used.

IKEA, TRÅDFRI and STYRBAR identify compatible devices; this project is not affiliated with IKEA. Simulated tests do not certify firmware, radio behavior or physical bulb output.
