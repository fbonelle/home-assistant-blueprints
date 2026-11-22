# SPDX-License-Identifier: GPL-3.0-only
"""Follow the public Home Assistant releases (workflow « Suivi des versions de Home Assistant »).

    python tools/ha_release.py check            # latest public release newer than the tested one?
    python tools/ha_release.py apply 2026.12.0  # move the project to that release

« check » reads PyPI and ignores beta and release-candidate builds. In GitHub Actions it
writes « new », « version » and « python » to the step outputs.

« apply » writes the new release everywhere: the homeassistant pin of requirements-test.txt,
the Python version of the validation workflow, the version of every family
(<release>.0, see tools/versioning.py) and one entry in both changelogs. It does not build
nor test: the workflow (or the contributor) then runs tools/build.py and the test suite,
and nothing is committed unless both succeed.

Standard library only: « check » runs before any dependency is installed.
"""
from datetime import date
import json
import os
from pathlib import Path
import re
import sys
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parent))
import versioning  # noqa: E402

ROOT = versioning.ROOT
PYPI = 'https://pypi.org/pypi/homeassistant/json'
PUBLIC = re.compile(r'(\d+)\.(\d+)\.(\d+)')  # Beta (b) and release-candidate (rc) builds never match.
MONTHS_FR = ['janvier', 'février', 'mars', 'avril', 'mai', 'juin', 'juillet', 'août', 'septembre',
             'octobre', 'novembre', 'décembre']
MONTHS_EN = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September',
             'October', 'November', 'December']
LABELS = {
    'integration_watchdog': ('Surveillance et relance des intégrations', 'Integration monitoring and reload'),
    'battery_watch': ('Surveillance des piles et batteries', 'Battery monitoring'),
    'notification_system': ('Système de notifications', 'Notification system'),
    'lighting': ('Télécommandes d’éclairage', 'Lighting remotes'),
}
assert set(LABELS) == set(versioning.FAMILIES)


def key(version):
    return tuple(int(part) for part in version.split('.'))


def latest_public():
    """The newest public release on PyPI with at least one file not withdrawn (yanked),
    and the Python minor version it requires (« >=3.14.2 » gives « 3.14 »)."""
    with urllib.request.urlopen(PYPI, timeout=30) as response:
        data = json.load(response)
    public = [v for v, files in data['releases'].items()
              if PUBLIC.fullmatch(v) and any(not f.get('yanked') for f in files)]
    version = max(public, key=key)
    with urllib.request.urlopen(f'https://pypi.org/pypi/homeassistant/{version}/json', timeout=30) as response:
        requires = json.load(response)['info']['requires_python'] or ''
    python = re.search(r'>=\s*(\d+\.\d+)', requires)
    assert python, f'Unreadable Python requirement for Home Assistant {version}: {requires!r}'
    return version, python[1]


def check():
    version, python = latest_public()
    tested = versioning.tested_ha()
    new = key(version) > key(tested)
    print(f'Home Assistant testé : {tested} ; dernière version publique : {version} (Python {python})')
    output = os.environ.get('GITHUB_OUTPUT')
    if output:
        with open(output, 'a') as handle:
            handle.write(f'new={"true" if new else "false"}\nversion={version}\npython={python}\n')


def replace_once(path, pattern, replacement):
    text = path.read_text()
    text, count = re.subn(pattern, replacement, text, flags=re.M)
    assert count == 1, (path, pattern)
    path.write_text(text)


def changelog_entry(release, versions, today):
    """One entry per release, in both languages, placed above the previous entries."""
    fr_date = f'{today.day} {MONTHS_FR[today.month - 1]} {today.year}'
    en_date = f'{today.day} {MONTHS_EN[today.month - 1]} {today.year}'
    fr = [f'## Home Assistant {release} — {fr_date}', '',
          f'- Tous les tests réussissent avec Home Assistant {release} : nouvelles versions des blueprints.']
    en = [f'## Home Assistant {release} — {en_date}', '',
          f'- The whole test suite passes with Home Assistant {release}: new blueprint versions.']
    for family, (old, new) in versions.items():
        fr.append(f'- {LABELS[family][0]} : {new} (précédemment {old}).')
        en.append(f'- {LABELS[family][1]}: {new} (previously {old}).')
    for name, lines in [('CHANGELOG.md', fr), ('CHANGELOG.en.md', en)]:
        path = ROOT / name
        text = path.read_text()
        # The entries start after the title and the language links.
        head, sep, rest = text.partition('\n## ')
        assert sep, name
        path.write_text(head.rstrip('\n') + '\n\n' + '\n'.join(lines) + '\n\n## ' + rest)


def apply(release, python=None, today=None):
    assert PUBLIC.fullmatch(release), f'Not a public release: {release!r}'
    tested = versioning.tested_ha()
    assert key(release) > key(tested), f'{release} is not newer than the tested {tested}'
    replace_once(ROOT / 'requirements-test.txt', r'^homeassistant==.*$', f'homeassistant=={release}')
    if python:
        replace_once(ROOT / '.github/workflows/validate.yml', r"^(\s*python-version: )'[\d.]+'$",
                     rf"\g<1>'{python}'")
    versions = {}
    for family in versioning.FAMILIES:
        new = f'{release}.0'
        versions[family] = (versioning.set_version(family, new), new)
    changelog_entry(release, versions, today or date.today())
    return versions


if __name__ == '__main__':
    if sys.argv[1:] == ['check']:
        check()
    elif len(sys.argv) in (3, 4) and sys.argv[1] == 'apply':
        for family, (old, new) in apply(sys.argv[2], sys.argv[3] if len(sys.argv) == 4 else None).items():
            print(f'{family} : {old} → {new}')
    else:
        sys.exit(__doc__)
