# Home Assistant blueprints

[Français](README.md) · **English**

A collection of blueprints built with standard Home Assistant features. Each blueprint has its own guide, examples and tests.

## Available

| Blueprint | Purpose | Version | Requirements |
|---|---|---|---|
| [Battery watch](docs/battery_watch.en.md) | Report each battery to replace or silent device as soon as it is detected, then send a summary at a fixed time. | **2026.11.3.0** | Home Assistant 2026.10 or later |
| [Integration watchdog](docs/integration_watchdog.en.md) | Detect a problem using selected entities, try reloading the integration and notify you when intervention is needed. | **2026.11.3.0** | Home Assistant 2026.10 or later |
| [Lighting remotes and automatic switch-off](docs/lighting.en.md) | One chosen action for each gesture of Aqara, eWeLink, Hue Dimmer, Hue Tap Dial, IKEA 5-button, IKEA on/off and IKEA STYRBAR remotes; switch-off after an on time. | **2026.11.3.0** | Home Assistant 2026.10 or later, ZHA; optional helper |
| [Notification system](docs/notification_system.en.md) | One entry point: channels by level (mobile, ntfy, e-mail), duplicate filter, night time, fallback, text-to-speech and persistent notification relay. | **2026.11.3.0** | Home Assistant 2026.10 or later, four blueprints |

Each version is the Home Assistant release the blueprint was validated against, followed by a counter of the project's own changes: **2026.11.3.0** passed the whole test suite with Home Assistant 2026.11.3. With each new public Home Assistant release, the tests run again automatically; when they pass, every blueprint moves to the new version. The prerequisite gives the minimum version actually required.

## Battery watch

A standalone blueprint and a Local To-do list with no size limit: each battery dropping below the threshold, each device silent for several hours and each “low battery” alert is reported once, as soon as it is detected, and added to the list; checking an item removes it from the summary until replacement. A summary is sent at the selected time and days. Phones, watches, computers and UPS units are excluded by default; exclusions can be extended by integration, manufacturer, entity, device or label.

[Installation and settings](docs/battery_watch.en.md) · [Import the blueprint](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fbattery_watch%2Fbattery_watch.yaml) · [Examples](examples/battery_watch/automations.yaml)

## Integration watchdog

1. [Import the blueprint](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fintegration_watchdog%2Fintegration_watchdog.yaml).
2. Create a Text helper, then select the integration and entities to monitor in the blueprint form.

[Installation guide](docs/integration_watchdog.en.md) · [How it works, tests and limitations](docs/integration_watchdog_robustness.en.md)

You can configure delays, retry limits, exclusions, notifications and logging. Add another integration through the form without copying scripts.

**The blueprint is the only file to install.** No configuration file, script, custom integration or restart is needed.

The Netatmo, TaHoma and Cozytouch examples use fictional identifiers and must be adapted before use.

## Lighting remotes and automatic switch-off

One blueprint per ZHA remote model (Aqara and eWeLink buttons, Philips Hue Dimmer and Tap Dial, IKEA 5-button and STYRBAR remotes, IKEA on/off switch), with the same actions and settings everywhere: toggle, fixed levels, alternate, single-step or continuous dimming, white temperature, a 44-preset palette, recall colour, custom action. Continuous changes stop on release or after a maximum duration. An optional Text helper adds the double press on IKEA remotes, the exact palette position and the freeze at the level reached. A last blueprint switches lights off after an on time, with or without a Timer helper.

[Actions, settings and moving from the former blueprints](docs/lighting.en.md) · [Examples](examples/lighting/automations.yaml) · Import: [Aqara](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flighting%2Faqara_button.yaml), [eWeLink](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flighting%2Fewelink_button.yaml), [Hue Dimmer](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flighting%2Fhue_dimmer_remote.yaml), [Hue Tap Dial](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flighting%2Fhue_tap_dial_remote.yaml), [IKEA 5-button](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flighting%2Fikea_5_button_remote.yaml), [IKEA on/off](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flighting%2Fikea_on_off_switch.yaml), [IKEA STYRBAR](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flighting%2Fikea_styrbar_remote.yaml), [Lighting automatic switch-off](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flighting%2Fauto_off.yaml)

## Notification system

Four blueprints working together: a **Dispatcher**, the entry point every automation calls, a **Channel sender** that isolates each channel to detect its failures, a queued **Text-to-speech** script and a **Mobile relay** that sends persistent notifications to the phone and clears them from it. Every address, device, schedule and rule is set in the forms; only two helpers need creating.

[Installation and behaviour](docs/notification_system.en.md) · [Example package](examples/notification_system/package.yaml) · Import: [Channel sender](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fscript%2Fnotification_system%2Fchannel_sender.yaml), [Dispatcher](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fscript%2Fnotification_system%2Fdispatcher.yaml), [Mobile relay](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fnotification_system%2Fmobile_relay.yaml), [Text-to-speech](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fscript%2Fnotification_system%2Ftext_to_speech.yaml)

## Development

Blueprints are in `blueprints/`, examples in `examples/` and guides in `docs/`.

To generate the files and run the tests with Python 3.14:

```sh
python3.14 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python tools/build.py
.venv/bin/python -m pytest -q
```

The suite runs on two Home Assistant releases: the tested release, which starts the blueprint version number, and the stated minimum release (latest patch release of that month). It covers all blueprints with its native schemas, automations and services. Providers and radio are simulated; no production credentials are needed. Home Assistant installs no package during the tests. GitHub Actions also checks generated files. Each blueprint keeps its own version in `src/<name>/VERSION`.

[Contributing](CONTRIBUTING.en.md) · [Changelog](CHANGELOG.en.md) · [Attribution and license](NOTICE.en.md)
