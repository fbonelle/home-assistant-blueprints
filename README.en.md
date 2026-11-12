# Home Assistant blueprints

[Français](README.md) · **English**

A collection of blueprints built with standard Home Assistant features. Each blueprint has its own guide, examples and tests.

## Available

| Blueprint | Purpose | Version | Requirements |
|---|---|---|---|
| [Integration monitoring and reload](docs/integration_watchdog.en.md) | Detect a problem using selected entities, try reloading the integration and notify you when intervention is needed. | **1.0.1** | Home Assistant 2026.10 or later |
| [Light with IKEA STYRBAR remote](docs/ikea_styrbar_light.en.md) | On/off, fast brightness and color holds, capability checks, configurable recall. | **1.2.0** | Home Assistant 2026.10, ZHA, color light, shared script |
| [Battery monitoring](docs/battery_watch.en.md) | Report each battery to replace or silent device as soon as it is detected, then send a summary at a fixed time. | **1.0.0** | Home Assistant 2026.10 or later |

**1.0.0 is the first published version.** Numbers used during development do not represent project releases.

## Integration monitoring and reload

1. Install the [shared configuration file](packages/integration_watchdog.yaml) once.
2. [Import the blueprint](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fintegration_watchdog%2Fsurveillance_integrations.yaml).
3. Create a Text helper, then select the integration and entities to monitor in the blueprint form.

[Installation guide](docs/integration_watchdog.en.md) · [How it works, tests and limitations](docs/robustesse_integration_watchdog.en.md)

You can configure delays, retry limits, exclusions, notifications and logging. Add another integration through the form without copying scripts.

**The initial installation requires two files: the blueprint and its shared configuration file.** The latter is a Home Assistant *package*: a YAML file containing the scripts and automations used by the blueprint. No custom integration or Python code needs to be installed in Home Assistant.

The blueprint form currently uses French labels; the English guide includes the labels needed during setup. The Netatmo, TaHoma and Cozytouch examples use fictional identifiers and must be adapted before use.

## Light with IKEA STYRBAR remote

One blueprint per light, with a dedicated Text helper and a [small shared script](packages/ikea_styrbar_light.yaml) installed once for fast holds. The form offers three reference Home Assistant whites, 20 historical IKEA presets and independent brightness and color speeds. Lateral holds cycle the palette; double up recalls the default when the firmware sends two events. A lateral hold can optionally be reserved for recall.

**Menu → Run actions** shows the capability diagnostic without commanding the light. Holds use native fades and freeze at the estimated intermediate level when released.

[Installation and buttons](docs/ikea_styrbar_light.en.md) · [Blueprint](blueprints/automation/ikea_styrbar_light/lampe_styrbar.yaml) · [Examples](examples/ikea_styrbar_light/automations.yaml)

## Battery monitoring

A standalone blueprint and a Text helper: each battery dropping below the threshold, each device silent for several hours and each “battery low” alert is reported once, as soon as it is detected. A summary is sent at the selected time and days. Phones, watches, computers and UPS units are excluded by default; exclusions can be extended by integration, manufacturer, entity, device or label. The form and messages use French labels; the English guide lists them.

[Installation and settings](docs/battery_watch.en.md) · [Import the blueprint](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fbattery_watch%2Fsurveillance_piles.yaml) · [Examples](examples/battery_watch/automations.yaml)

## Development

Blueprints are in `blueprints/`, shared files in `packages/`, examples in `examples/` and guides in `docs/`.

To generate the files and run the tests with Python 3.14:

```sh
python3.14 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python tools/build.py
.venv/bin/python -m pytest -q
```

The suite uses Home Assistant 2026.10.4 and covers the three blueprints with its native schemas, automations and services. Providers and radio are simulated; no production credentials are needed. GitHub Actions also checks generated files. Each blueprint keeps its own version in `src/<name>/VERSION`.

[Contributing](CONTRIBUTING.en.md) · [Changelog](CHANGELOG.en.md) · [Attribution and license](NOTICE.en.md)
