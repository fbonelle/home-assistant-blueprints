# Contributing

[Français](CONTRIBUTING.md) · **English**

Each new blueprint needs its own folder under `blueprints/automation/` or `blueprints/script/`, French and English guides, examples and tests. Shared configuration files belong in `packages/`.

- Use standard Home Assistant features and document the files needed for installation.
- Prefer familiar terms: monitored entities, retries, history, reload and recovery. Put technical details on a separate page.
- Update both languages and their navigation links together.
- Use fictional examples only; do not publish production identifiers, secrets or personal logs.
- Preserve attribution and licenses for reused work.
- Edit sources under `src/` or `tools/`, regenerate YAML files and include the generated files in the change.
- Run tests in an isolated Home Assistant instance without contacting providers or a production installation.

```sh
.venv/bin/python tools/build.py
.venv/bin/python -m pytest -q
```

Each blueprint defines its version in `src/<name>/VERSION`. The generator uses it in the blueprint name and, where applicable, shared-file headers. Documentation and the changelog must match. The first version is **1.0.0**; changing display names must not rename internal identifiers used by automations.
