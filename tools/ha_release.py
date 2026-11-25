# SPDX-License-Identifier: GPL-3.0-only
"""Follow the public Home Assistant releases (workflow « Follow Home Assistant releases »).

    python tools/ha_release.py check                     # latest public release newer than the tested one?
    python tools/ha_release.py apply 2026.12.0           # move the project to that release
    python tools/ha_release.py sync-requirements         # pin what the installed release requires
    python tools/ha_release.py integration-requirements  # print it, for « pip install »

« check » reads PyPI and ignores beta and release-candidate builds. In GitHub Actions it
writes « new », « version » and « python » to the step outputs.

« apply » writes the new release everywhere: the homeassistant pin of requirements-test.txt,
the Python version of the validation workflow, the version of every family
(<release>.0, see tools/versioning.py) and one entry in both changelogs. It does not build
nor test: the workflow (or the contributor) then runs tools/build.py and the test suite,
and nothing is committed unless both succeed.

« sync-requirements » runs once Home Assistant is installed: the integrations loaded by the
tests (TEST_INTEGRATIONS) carry their own requirements in their manifests, and the tests
refuse to install anything themselves (tests/conftest.py). Their pins in
requirements-test.txt are rewritten to the versions of the installed release.

Standard library only: « check » runs before any dependency is installed.
"""
from datetime import date
import importlib.util
import json
import os
from pathlib import Path
import re
import sys
import tempfile
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
# Family names in the changelog, the same in both languages, listed in alphabetical order.
LABELS = {
    'battery_watch': 'Battery watch',
    'integration_watchdog': 'Integration watchdog',
    'lighting': 'Lighting remotes and automatic switch-off',
    'notification_system': 'Notification system',
}
assert set(LABELS) == set(versioning.FAMILIES)
# Integrations with requirements that the tests load (local_todo: memory of the battery watch).
# A missing entry makes the tests fail and name the requirement (tests/conftest.py).
TEST_INTEGRATIONS = ['local_todo']


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
    print(f'Tested Home Assistant: {tested}; latest public release: {version} (Python {python})')
    output = os.environ.get('GITHUB_OUTPUT')
    if output:
        with open(output, 'a') as handle:
            handle.write(f'new={"true" if new else "false"}\nversion={version}\npython={python}\n')


def replace_once(path, pattern, replacement):
    text = path.read_text()
    text, count = re.subn(pattern, replacement, text, flags=re.M)
    assert count == 1, (path, pattern)
    path.write_text(text)


def changelog_entry(root, release, versions, today):
    """One entry per release, in both languages, placed above the previous entries."""
    fr_date = f'{today.day} {MONTHS_FR[today.month - 1]} {today.year}'
    en_date = f'{today.day} {MONTHS_EN[today.month - 1]} {today.year}'
    fr = [f'## Home Assistant {release} — {fr_date}', '',
          f'- Tous les tests réussissent avec Home Assistant {release} : nouvelles versions des blueprints.']
    en = [f'## Home Assistant {release} — {en_date}', '',
          f'- The whole test suite passes with Home Assistant {release}: new blueprint versions.']
    for family in sorted(versions, key=lambda f: LABELS[f].casefold()):
        old, new = versions[family]
        fr.append(f'- {LABELS[family]} : {new} (précédemment {old}).')
        en.append(f'- {LABELS[family]}: {new} (previously {old}).')
    for name, lines in [('CHANGELOG.md', fr), ('CHANGELOG.en.md', en)]:
        path = root / name
        text = path.read_text()
        # The entries start after the title and the language links.
        head, sep, rest = text.partition('\n## ')
        assert sep, name
        path.write_text(head.rstrip('\n') + '\n\n' + '\n'.join(lines) + '\n\n## ' + rest)


def apply(release, python=None, today=None):
    # Prepare the release on copies so a late validation error leaves a retryable checkout.
    paths = [ROOT / name for name in [*versioning.READMES, 'CHANGELOG.md', 'CHANGELOG.en.md',
                                      'requirements-test.txt', '.github/workflows/validate.yml']]
    paths.extend(ROOT.glob('docs/*.md'))
    paths.extend(ROOT / 'src' / family / 'VERSION' for family in versioning.FAMILIES)
    with tempfile.TemporaryDirectory() as directory:
        stage = Path(directory)
        copies = {path: stage / path.relative_to(ROOT) for path in paths}
        for path, staged in copies.items():
            staged.parent.mkdir(parents=True, exist_ok=True)
            staged.write_bytes(path.read_bytes())
        versions = _apply(stage, release, python, today)
        # Commit the version pin last so validation failures never advance the baseline.
        for path in sorted(paths, key=lambda path: path.name == 'requirements-test.txt'):
            data = copies[path].read_bytes()
            if path.read_bytes() != data:
                path.write_bytes(data)
    return versions


def _apply(root, release, python, today):
    assert PUBLIC.fullmatch(release), f'Not a public release: {release!r}'
    tested = versioning.tested_ha(root)
    assert key(release) > key(tested), f'{release} is not newer than the tested {tested}'
    replace_once(root / 'requirements-test.txt', r'^homeassistant==.*$', f'homeassistant=={release}')
    if python:
        replace_once(root / '.github/workflows/validate.yml', r"^(\s*python-version: )'[\d.]+'$",
                     rf"\g<1>'{python}'")
    versions = {}
    for family in versioning.FAMILIES:
        new = f'{release}.0'
        versions[family] = (versioning.set_version(family, new, root), new)
    # Family versions update table rows and guides; the README explanation also quotes
    # the tested release and an example blueprint version outside those rows.
    for readme in versioning.READMES:
        path = root / readme
        text = path.read_text()
        pattern = rf'(?<![\d.]){re.escape(tested)}(?P<counter>\.\d+)?(?!\d|\.\d)'
        text = re.sub(pattern, lambda match: release + ('.0' if match['counter'] else ''), text)
        path.write_text(text)
    versioning.sync_minimum_docs(root)
    changelog_entry(root, release, versions, today or date.today())
    return versions


def integration_requirements():
    """Requirements of TEST_INTEGRATIONS in the installed Home Assistant, from their manifests."""
    spec = importlib.util.find_spec('homeassistant')
    assert spec and spec.submodule_search_locations, 'Home Assistant is not installed'
    components = Path(list(spec.submodule_search_locations)[0]) / 'components'
    found = []
    for domain in TEST_INTEGRATIONS:
        manifest = json.loads((components / domain / 'manifest.json').read_text())
        for req in manifest.get('requirements', []):
            assert re.fullmatch(r'[A-Za-z0-9_.\-]+==[\w.]+', req), (domain, req)
            if req not in found:
                found.append(req)
    return found


def sync_requirements():
    """Write the requirements of TEST_INTEGRATIONS into requirements-test.txt."""
    path = ROOT / 'requirements-test.txt'
    text = path.read_text()
    for req in integration_requirements():
        name = req.split('==')[0]
        line = re.compile(rf'^{re.escape(name)}==.*$', flags=re.M | re.I)
        if line.search(text):
            text = line.sub(req, text, count=1)
        else:
            text = text.rstrip('\n') + f'\n# Requirement of an integration loaded by the tests.\n{req}\n'
    path.write_text(text)
    return integration_requirements()


if __name__ == '__main__':
    if sys.argv[1:] == ['check']:
        check()
    elif sys.argv[1:] == ['sync-requirements']:
        print('\n'.join(sync_requirements()))
    elif sys.argv[1:] == ['integration-requirements']:
        print(' '.join(integration_requirements()))
    elif len(sys.argv) in (3, 4) and sys.argv[1] == 'apply':
        for family, (old, new) in apply(sys.argv[2], sys.argv[3] if len(sys.argv) == 4 else None).items():
            print(f'{family} : {old} → {new}')
    else:
        sys.exit(__doc__)
