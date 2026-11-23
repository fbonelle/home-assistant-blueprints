# Contributing

[Français](CONTRIBUTING.md) · **English**

Each new blueprint needs its own folder under `blueprints/automation/` or `blueprints/script/`, French and English guides, examples and tests. A blueprint must install on its own: no configuration file to copy into Home Assistant.

- Use standard Home Assistant features and document the files needed for installation.
- Prefer familiar terms: monitored entities, retries, history, reload and recovery. Put technical details on a separate page.
- Update both languages and their navigation links together.
- Write the code, comments, identifiers, file names, blueprint names, forms, messages, text-to-speech and logs in English. The guides stay in French and English and quote the English labels as they appear.
- Sort tables that list items (blueprints, families, former setups) alphabetically; tables of actions and settings follow the form order.
- Use fictional examples only; do not publish production identifiers, secrets or personal logs.
- Preserve attribution and licenses for reused work.
- Edit sources under `src/` or `tools/`, regenerate YAML files and include the generated files in the change.
- Run tests in an isolated Home Assistant instance without contacting providers or a production installation. Home Assistant installs no package during the tests (`tests/conftest.py`): an integration requirement that is missing or at another version fails the test that loads it. `.venv/bin/python tools/ha_release.py sync-requirements` then rewrites these requirements in `requirements-test.txt` from the installed Home Assistant release.

```sh
.venv/bin/python tools/build.py
.venv/bin/python -m pytest -q
```

The CI also runs the suite on the minimum release (`homeassistant~=` followed by `python tools/versioning.py min`, then `pip install $(python tools/ha_release.py integration-requirements)`).

Each family defines its version in `src/<name>/VERSION`, as `<Home Assistant release>.<counter>` (for example `2026.11.2.0`); `tools/versioning.py` is the only reference. The Home Assistant release is the one pinned in `requirements-test.txt`, with which the whole test suite passes. After changing a family, `.venv/bin/python tools/versioning.py bump <name>` increments the counter in `VERSION`, the READMEs and the guides; the changelog then describes the change. The “Follow Home Assistant releases” workflow (`tools/ha_release.py`) checks the public Home Assistant releases every day; when a newer release passes the build and the whole test suite, it pins that release, moves every family to `<release>.0`, adds a changelog entry and publishes to `main`. On failure, it opens an issue and changes nothing. `homeassistant.min_version` stays the minimum version actually required. Changing display names must not rename internal identifiers used by automations.
