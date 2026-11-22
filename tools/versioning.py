# SPDX-License-Identifier: GPL-3.0-only
"""Version numbers of the blueprint families: <Home Assistant version>.<counter>.

Every family carries the full version of the Home Assistant release it was last validated
against (the version pinned in requirements-test.txt), followed by a counter of the
project's own changes made since that validation: 2026.11.2.0, then 2026.11.2.1, … When a
newer public Home Assistant release passes the whole test suite, every family moves to
<new version>.0 (tools/ha_release.py, run by the « Suivi des versions de Home Assistant »
workflow).

The version appears in src/<family>/VERSION (read by the generators), in the README tables
(French and English) and in the guides listed below. This module is the only place that
knows these locations, so that the generators, the tests and the release script stay in
agreement.

Command line:
    python tools/versioning.py bump <family>   # counter + 1 after a change of the family
    python tools/versioning.py show            # versions and tested Home Assistant release
"""
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parent.parent

# Year, month (no leading zero), patch release of Home Assistant, then the project counter.
HA_VERSION = r'20\d{2}\.(?:[1-9]|1[0-2])\.(?:0|[1-9]\d*)'
VERSION = re.compile(rf'(?P<ha>{HA_VERSION})\.(?P<counter>0|[1-9]\d*)')

# Families: guides that quote the version (both languages), and the guide each README row
# links to, which identifies the row of the family in README.md and README.en.md.
FAMILIES = {
    'integration_watchdog': {
        'guides': ['docs/integration_watchdog.md', 'docs/integration_watchdog.en.md'],
        'readme_link': 'docs/integration_watchdog',
    },
    'battery_watch': {
        'guides': ['docs/battery_watch.md', 'docs/battery_watch.en.md'],
        'readme_link': 'docs/battery_watch',
    },
    'notification_system': {
        'guides': [],
        'readme_link': 'docs/notification_system',
    },
    'lighting': {
        'guides': [],
        'readme_link': 'docs/lighting',
    },
}
READMES = ['README.md', 'README.en.md']


def tested_ha():
    """The Home Assistant release the test suite runs against (requirements-test.txt)."""
    text = (ROOT / 'requirements-test.txt').read_text()
    found = re.findall(rf'^homeassistant==({HA_VERSION})$', text, flags=re.M)
    assert len(found) == 1, 'requirements-test.txt must pin exactly one homeassistant release'
    return found[0]


def check(version):
    """A family version, validated: <Home Assistant version>.<counter>."""
    assert VERSION.fullmatch(version), f'Invalid blueprint version: {version!r}'
    return version


def read(family):
    """The version of a family, as the generators write it into the blueprint names."""
    assert family in FAMILIES, family
    return check((ROOT / 'src' / family / 'VERSION').read_text().strip())


def _replace_token(text, old, new):
    """Replace every occurrence of a version number, never a part of a longer number."""
    return re.subn(rf'(?<![\d.]){re.escape(old)}(?![\d]|\.\d)', new, text)


def set_version(family, new):
    """Write a family version everywhere it is quoted: VERSION, README rows, guides.

    Every location must contain the previous version: a location that no longer quotes it
    means the documentation drifted, and the change is refused before anything is written.
    The previous version is read without validation: replacing it is what repairs it.
    """
    assert family in FAMILIES, family
    old = (ROOT / 'src' / family / 'VERSION').read_text().strip()
    check(new)
    if old == new:
        return old
    spec = FAMILIES[family]
    writes = {ROOT / 'src' / family / 'VERSION': new + '\n'}
    for readme in READMES:
        path = ROOT / readme
        lines = path.read_text().split('\n')
        rows = [i for i, line in enumerate(lines) if line.startswith('|') and spec['readme_link'] in line]
        assert len(rows) == 1, (readme, family)
        lines[rows[0]], count = _replace_token(lines[rows[0]], old, new)
        assert count == 1, (readme, family, old)
        writes[path] = '\n'.join(lines)
    for guide in spec['guides']:
        path = ROOT / guide
        text, count = _replace_token(path.read_text(), old, new)
        assert count >= 1, (guide, old)
        writes[path] = text
    for path, text in writes.items():
        path.write_text(text)
    return old


def bump(family):
    """Counter + 1, for a change of the family between two Home Assistant releases."""
    match = VERSION.fullmatch(read(family))
    new = f"{match['ha']}.{int(match['counter']) + 1}"
    set_version(family, new)
    return new


if __name__ == '__main__':
    if len(sys.argv) == 3 and sys.argv[1] == 'bump':
        print(bump(sys.argv[2]))
    elif len(sys.argv) == 2 and sys.argv[1] == 'show':
        print(f'Home Assistant testé : {tested_ha()}')
        for name in FAMILIES:
            print(f'{name} : {read(name)}')
    else:
        sys.exit(__doc__)
