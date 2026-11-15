# Home Assistant blueprints

[Français](README.md) · **English**

A collection of blueprints built with standard Home Assistant features. Each blueprint has its own guide, examples and tests.

## Available

| Blueprint | Purpose | Version | Requirements |
|---|---|---|---|
| [Integration monitoring and reload](docs/integration_watchdog.en.md) | Detect a problem using selected entities, try reloading the integration and notify you when intervention is needed. | **1.0.0** | Home Assistant 2026.10 or later |
| [Battery monitoring](docs/battery_watch.en.md) | Report each battery to replace or silent device as soon as it is detected, then send a summary at a fixed time. | **1.0.0** | Home Assistant 2026.10 or later |
| [Notification system](docs/notification_system.en.md) | One entry point: channels by level (mobile, ntfy, e-mail), duplicate filter, night time, fallback, speech and persistent notification relay. | **1.0.0** | Home Assistant 2026.10 or later, four blueprints |
| [Lighting remotes and automatic switch-off](docs/lighting.en.md) | One chosen action for each gesture of Hue Dimmer, Hue Tap Dial, IKEA on/off, IKEA 5-button, IKEA STYRBAR and eWeLink remotes; switch-off after an on time. | **1.0.3** | Home Assistant 2026.10, ZHA; optional helper |

**1.0.0 is the first published version.** Numbers used during development do not represent project releases.

## Integration monitoring and reload

1. Install the [shared configuration file](packages/integration_watchdog.yaml) once.
2. [Import the blueprint](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fintegration_watchdog%2Fsurveillance_integrations.yaml).
3. Create a Text helper, then select the integration and entities to monitor in the blueprint form.

[Installation guide](docs/integration_watchdog.en.md) · [How it works, tests and limitations](docs/robustesse_integration_watchdog.en.md)

You can configure delays, retry limits, exclusions, notifications and logging. Add another integration through the form without copying scripts.

**The initial installation requires two files: the blueprint and its shared configuration file.** The latter is a Home Assistant *package*: a YAML file containing the scripts and automations used by the blueprint. No custom integration or Python code needs to be installed in Home Assistant.

The blueprint form currently uses French labels; the English guide includes the labels needed during setup. The Netatmo, TaHoma and Cozytouch examples use fictional identifiers and must be adapted before use.

## Battery monitoring

A standalone blueprint and a Local To-do list with no size limit: each battery dropping below the threshold, each device silent for several hours and each “battery low” alert is reported once, as soon as it is detected, and added to the list; checking an item removes it from the summary until replacement. A summary is sent at the selected time and days. Phones, watches, computers and UPS units are excluded by default; exclusions can be extended by integration, manufacturer, entity, device or label. The form and messages use French labels; the English guide lists them.

[Installation and settings](docs/battery_watch.en.md) · [Import the blueprint](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fbattery_watch%2Fsurveillance_piles.yaml) · [Examples](examples/battery_watch/automations.yaml)

## Notification system

Four blueprints working together: a **dispatcher**, the entry point every automation calls, a **channel sender** that isolates each channel to detect its failures, a queued **speech** script and a **relay** that sends persistent notifications to the phone and clears them from it. Every address, device, schedule and rule is set in the forms; only two helpers need creating.

[Installation and behaviour](docs/notification_system.en.md) · [Example package](examples/notification_system/package.yaml) · Import: [dispatcher](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fscript%2Fnotification_system%2Frepartiteur.yaml), [sender](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fscript%2Fnotification_system%2Fenvoi_canal.yaml), [speech](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fscript%2Fnotification_system%2Flecture_vocale.yaml), [relay](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fnotification_system%2Frelais_mobile.yaml)

## Lighting remotes and automatic switch-off

One blueprint per ZHA remote model (Philips Hue Dimmer and Tap Dial, IKEA on/off switch, IKEA 5-button and STYRBAR remotes, eWeLink button), with the same actions and settings everywhere: toggle, fixed levels, alternate, single-step or continuous dimming, white temperature, a 44-preset palette, recall colour, custom action. Continuous changes stop on release or after a maximum duration. An optional Text helper adds the double press on IKEA remotes, the exact palette position and the freeze at the level reached. A last blueprint switches lights off after an on time, with or without a Timer helper.

[Actions, settings and moving from the former blueprints](docs/lighting.en.md) · [Examples](examples/lighting/automations.yaml) · Import: [Hue Dimmer](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flighting%2Ftelecommande_hue_dimmer.yaml), [Hue Tap Dial](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flighting%2Ftelecommande_hue_tap_dial.yaml), [IKEA on/off](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flighting%2Ftelecommande_ikea_marche_arret.yaml), [IKEA 5 buttons](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flighting%2Ftelecommande_ikea_5_boutons.yaml), [IKEA STYRBAR](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flighting%2Ftelecommande_ikea_styrbar.yaml), [eWeLink](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flighting%2Fbouton_ewelink.yaml), [automatic switch-off](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flighting%2Fextinction_automatique.yaml)

## Development

Blueprints are in `blueprints/`, shared files in `packages/`, examples in `examples/` and guides in `docs/`.

To generate the files and run the tests with Python 3.14:

```sh
python3.14 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python tools/build.py
.venv/bin/python -m pytest -q
```

The suite uses Home Assistant 2026.10.4 and covers all blueprints with its native schemas, automations and services. Providers and radio are simulated; no production credentials are needed. GitHub Actions also checks generated files. Each blueprint keeps its own version in `src/<name>/VERSION`.

[Contributing](CONTRIBUTING.en.md) · [Changelog](CHANGELOG.en.md) · [Attribution and license](NOTICE.en.md)
