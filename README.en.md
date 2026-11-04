# Home Assistant blueprints

[Français](README.md) · **English**

A collection of blueprints built with standard Home Assistant features. Each blueprint has its own guide, examples and tests.

## Available

| Blueprint | Purpose | Version | Requirements |
|---|---|---|---|
| [Integration monitoring and reload](docs/integration_watchdog.en.md) | Detect a problem using selected entities, try reloading the integration and notify you when intervention is needed. | **1.0.0** | Home Assistant 2026.10 or later |

**1.0.0 is the first published version.** Numbers used during development do not represent project releases.

## Integration monitoring and reload

1. Install the [shared configuration file](packages/integration_watchdog.yaml) once.
2. [Import the blueprint](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fintegration_watchdog%2Fsurveillance_integrations.yaml).
3. Create a Text helper, then select the integration and entities to monitor in the blueprint form.

[Installation guide](docs/integration_watchdog.en.md) · [How it works, tests and limitations](docs/robustesse_integration_watchdog.en.md)

You can configure delays, retry limits, exclusions, notifications and logging. Add another integration through the form without copying scripts.

**The initial installation requires two files: the blueprint and its shared configuration file.** The latter is a Home Assistant *package*: a YAML file containing the scripts and automations used by the blueprint. No custom integration or Python code needs to be installed in Home Assistant.

The blueprint form currently uses French labels; the English guide includes the labels needed during setup. The Netatmo, TaHoma and Cozytouch examples use fictional identifiers and must be adapted before use.

## Development

Blueprints are in `blueprints/`, shared files in `packages/`, examples in `examples/` and guides in `docs/`.

To generate the files and run the tests with Python 3.14:

```sh
python3.14 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python tools/build.py
.venv/bin/python -m pytest -q
```

The suite contains **88 tests** using Home Assistant 2026.10.4. Provider calls are simulated and no production credentials are needed. GitHub Actions also checks that generated files are up to date.

[Contributing](CONTRIBUTING.en.md) · [Changelog](CHANGELOG.en.md) · [Attribution and license](NOTICE.en.md)
