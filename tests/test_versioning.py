# SPDX-License-Identifier: GPL-3.0-only
"""Version scheme <Home Assistant release>.<counter> and the release-following script.

The repository itself must be consistent: every family carries the Home Assistant release
pinned for the tests, and its version is quoted in the READMEs, the guides and the
published blueprint names. The script that follows the Home Assistant releases is run on
a copy of the repository, with PyPI replaced by fixed answers.
"""
import datetime
import shutil
import sys
from pathlib import Path

import pytest
from homeassistant.util.yaml import load_yaml

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'tools'))
import ha_release  # noqa: E402
import versioning  # noqa: E402

# Published blueprint files of each family (all of them carry the version in their name).
PUBLISHED = {
    'integration_watchdog': ['blueprints/automation/integration_watchdog'],
    'battery_watch': ['blueprints/automation/battery_watch'],
    'notification_system': ['blueprints/automation/notification_system', 'blueprints/script/notification_system'],
    'lighting': ['blueprints/automation/lighting'],
}


# ---------------------------------------------------------------- repository consistency

@pytest.mark.parametrize('family', list(versioning.FAMILIES))
def test_family_version_follows_the_tested_release(family):
    version = versioning.read(family)
    assert version.startswith(versioning.tested_ha() + '.')


@pytest.mark.parametrize('family', list(versioning.FAMILIES))
def test_version_is_quoted_in_readmes_guides_and_blueprints(family):
    version = versioning.read(family)
    spec = versioning.FAMILIES[family]
    for readme in versioning.READMES:
        rows = [line for line in (ROOT / readme).read_text().splitlines()
                if line.startswith('|') and spec['readme_link'] in line]
        assert len(rows) == 1 and f'**{version}**' in rows[0], (readme, family)
    for guide in spec['guides']:
        assert version in (ROOT / guide).read_text(), guide
    files = [f for folder in PUBLISHED[family] for f in sorted((ROOT / folder).glob('*.yaml'))]
    assert files
    for path in files:
        assert load_yaml(str(path))['blueprint']['name'].endswith(f'— {version}'), path


def test_scheme_accepts_only_release_and_counter():
    for good in ['2026.11.2.0', '2026.1.0.12', '2027.12.10.3']:
        assert versioning.check(good) == good
    for bad in ['1.0.0', '2026.11.2', '2026.11.2.01', '2026.13.0.0', '2026.011.2.0', '2026.11.2.0b1']:
        with pytest.raises(AssertionError):
            versioning.check(bad)


# ---------------------------------------------------------------- release-following script

@pytest.fixture
def copy(tmp_path, monkeypatch):
    """A copy of the files the script writes, with both modules pointed at it."""
    for name in ['requirements-test.txt', 'README.md', 'README.en.md', 'CHANGELOG.md', 'CHANGELOG.en.md',
                 '.github/workflows/validate.yml']:
        (tmp_path / name).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / name, tmp_path / name)
    for family, spec in versioning.FAMILIES.items():
        (tmp_path / 'src' / family).mkdir(parents=True)
        shutil.copy(ROOT / 'src' / family / 'VERSION', tmp_path / 'src' / family / 'VERSION')
        for guide in spec['guides']:
            (tmp_path / guide).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(ROOT / guide, tmp_path / guide)
    monkeypatch.setattr(versioning, 'ROOT', tmp_path)
    monkeypatch.setattr(ha_release, 'ROOT', tmp_path)
    return tmp_path


def next_release():
    year, month, patch = (int(p) for p in versioning.tested_ha().split('.'))
    return f'{year}.{month}.{patch + 1}'


def test_apply_moves_every_family_to_the_new_release(copy):
    release = next_release()
    before = {family: versioning.read(family) for family in versioning.FAMILIES}
    versions = ha_release.apply(release, '3.15', today=datetime.date(2026, 12, 3))
    assert versioning.tested_ha() == release
    assert f'homeassistant=={release}\n' in (copy / 'requirements-test.txt').read_text()
    assert "python-version: '3.15'" in (copy / '.github/workflows/validate.yml').read_text()
    for family in versioning.FAMILIES:
        assert versioning.read(family) == f'{release}.0'
        assert versions[family] == (before[family], f'{release}.0')
        for readme in versioning.READMES:
            assert f'**{release}.0**' in (copy / readme).read_text()
    fr = (copy / 'CHANGELOG.md').read_text()
    en = (copy / 'CHANGELOG.en.md').read_text()
    # The new entry comes first, right after the title and the language links.
    assert fr.split('\n## ')[1].startswith(f'Home Assistant {release} — 3 décembre 2026\n')
    assert en.split('\n## ')[1].startswith(f'Home Assistant {release} — 3 December 2026\n')
    assert f'Télécommandes d’éclairage : {release}.0 (précédemment {before["lighting"]}).' in fr


def test_apply_refuses_an_older_release_or_a_prerelease(copy):
    with pytest.raises(AssertionError):
        ha_release.apply(versioning.tested_ha())
    with pytest.raises(AssertionError):
        ha_release.apply(next_release() + 'b0')


def test_bump_increments_the_counter_everywhere(copy):
    version = versioning.read('integration_watchdog')
    release, counter = version.rsplit('.', 1)
    assert versioning.bump('integration_watchdog') == f'{release}.{int(counter) + 1}'
    for guide in versioning.FAMILIES['integration_watchdog']['guides']:
        text = (copy / guide).read_text()
        assert f'{release}.{int(counter) + 1}' in text and version not in text
    # The other families keep their version, even where they share the same number.
    assert versioning.read('lighting') == version


def test_check_ignores_prereleases(monkeypatch, tmp_path):
    answers = {
        ha_release.PYPI: {'releases': {'2026.11.2': [{}], '2026.12.0b3': [{}], '2026.12.0rc1': [{}],
                                       '2026.11.3': [{'yanked': True}], '2026.10.4': [{}]}},
        'https://pypi.org/pypi/homeassistant/2026.11.2/json': {'info': {'requires_python': '>=3.14.2'}},
    }

    class Answer:
        def __init__(self, url):
            self.data = answers[url]

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(ha_release.urllib.request, 'urlopen', lambda url, timeout: Answer(url))
    monkeypatch.setattr(ha_release.json, 'load', lambda answer: answer.data)
    assert ha_release.latest_public() == ('2026.11.2', '3.14')
    output = tmp_path / 'output'
    monkeypatch.setenv('GITHUB_OUTPUT', str(output))
    monkeypatch.setattr(versioning, 'tested_ha', lambda: '2026.11.1')
    ha_release.check()
    assert output.read_text() == 'new=true\nversion=2026.11.2\npython=3.14\n'
