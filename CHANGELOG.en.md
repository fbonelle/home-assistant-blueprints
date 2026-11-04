# Changelog

[Français](CHANGELOG.md) · **English**

## 1.0.0 — 4 November 2026

First published version of **Integration monitoring and reload**.

- Setup through the Home Assistant form, with a Text helper to retain history.
- Up to 50 simultaneous reloads; requests wait without consuming a retry when all slots are busy.
- Configurable retry counts and delays, notifications, logging, exclusions and observation mode.
- Protection against duplicate reloads and retained results after interruption.
- Fictional Netatmo, TaHoma and Cozytouch examples.
- French and English documentation, 88 tests and automated GitHub Actions checks.

Each blueprint’s version is stored in `src/<name>/VERSION`. Development revisions do not represent published releases.
