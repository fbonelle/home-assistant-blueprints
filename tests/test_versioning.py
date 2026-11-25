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
    assert f'Lighting remotes and automatic switch-off : {release}.0 (précédemment {before["lighting"]}).' in fr
    # Families are listed in alphabetical order of their names.
    assert fr.index('- Battery watch :') < fr.index('- Integration watchdog :') < fr.index('- Lighting remotes') \
        < fr.index('- Notification system :')


@pytest.mark.parametrize('release', ['2099.1.0', '2099.1.10'])
def test_apply_updates_readme_explanations_on_successive_releases(copy, release):
    # Exercise both a normal patch upgrade and a change of month/year.
    for target in [next_release(), release]:
        previous = versioning.tested_ha()
        ha_release.apply(target)
        for readme in versioning.READMES:
            text = (copy / readme).read_text()
            prose = '\n'.join(line for line in text.splitlines() if not line.startswith('|'))
            assert f'Home Assistant {target}' in prose, readme
            assert f'{target}.0' in prose, readme
            assert previous not in text, readme
            assert f"Home Assistant {versioning.minimum_ha(target).rsplit('.', 1)[0]}" in text, readme


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


# ---------------------------------------------------------------- minimum Home Assistant release

MIN_MONTH = '.'.join(versioning.minimum_ha().split('.')[:2])
# Guides that state the minimum release in their prerequisites.
MIN_GUIDES = ['docs/battery_watch.md', 'docs/battery_watch.en.md',
              'docs/integration_watchdog.md', 'docs/integration_watchdog.en.md']


@pytest.mark.parametrize('release, expected', [
    ('2026.11.3', '2026.8.0'), ('2026.12.0', '2026.9.0'),
    ('2027.1.0', '2026.10.0'), ('2027.2.12', '2026.11.0'),
    ('2027.3.1', '2026.12.0'), ('2027.4.0', '2027.1.0'),
])
def test_minimum_is_three_calendar_months_before_the_release(release, expected):
    assert versioning.minimum_ha(release) == expected


def test_minimum_follows_the_pin_without_reimporting(copy):
    for release in ['2027.1.0', '2027.2.3']:
        path = copy / 'requirements-test.txt'
        import re
        path.write_text(re.sub(r'^homeassistant==.*$', f'homeassistant=={release}',
                               path.read_text(), flags=re.M))
        assert versioning.minimum_ha() == versioning.minimum_ha(release)
        versioning.sync_minimum_docs()
        month = versioning.minimum_ha().rsplit('.', 1)[0]
        for name in versioning.READMES + MIN_GUIDES:
            assert f'Home Assistant **{month} ' in (copy / name).read_text() or \
                f'Home Assistant {month} ' in (copy / name).read_text(), name
    before = {path: path.read_bytes() for path in copy.rglob('*.md')}
    versioning.sync_minimum_docs()
    assert all(path.read_bytes() == text for path, text in before.items())


def test_every_published_blueprint_requires_the_minimum_release():
    files = sorted((ROOT / 'blueprints').rglob('*.yaml'))
    assert len(files) >= 14
    for path in files:
        assert load_yaml(str(path))['blueprint']['homeassistant']['min_version'] == versioning.minimum_ha(), path


def test_readmes_and_guides_state_the_minimum_release():
    for readme, wording in [('README.md', 'minimum'), ('README.en.md', 'or later')]:
        for family, spec in versioning.FAMILIES.items():
            row = [line for line in (ROOT / readme).read_text().splitlines()
                   if line.startswith('|') and spec['readme_link'] in line][0]
            assert f'Home Assistant {MIN_MONTH} {wording}' in row.split('|')[-2], (readme, family)
    for guide in MIN_GUIDES:
        assert f'Home Assistant **{MIN_MONTH} ' in (ROOT / guide).read_text(), guide


def test_markdown_never_quotes_another_home_assistant_release():
    """Only the minimum (prerequisites) and the tested release (version scheme, changelog)
    may be quoted: any other number is a statement that went out of date."""
    import re
    allowed = {MIN_MONTH, versioning.minimum_ha(), versioning.tested_ha()}
    for path in ROOT.glob('**/*.md'):
        if '.venv' in path.parts or 'node_modules' in path.parts:
            continue
        text = path.read_text()
        if path.name.startswith('CHANGELOG'):
            text = text.split('\n## ', 2)[1]  # Earlier entries keep the release they were made with.
        for match in re.finditer(r'Home Assistant[ *]*(?:officiel |official )?[ *]*(20\d{2}\.\d+(?:\.\d+)?)', text):
            assert match[1] in allowed, (path.name, match[0])


def test_sync_requirements_pins_what_the_installed_release_requires(copy, monkeypatch):
    monkeypatch.setattr(ha_release, 'integration_requirements', lambda: ['ical==99.1.2', 'newlib==1.0'])
    ha_release.sync_requirements()
    text = (copy / 'requirements-test.txt').read_text()
    assert 'ical==99.1.2\n' in text and text.count('ical==') == 1
    assert text.endswith('# Requirement of an integration loaded by the tests.\nnewlib==1.0\n')
    assert f'homeassistant=={versioning.tested_ha()}\n' in text


def test_integration_requirements_come_from_the_installed_manifests():
    from homeassistant.components import local_todo
    import json
    manifest = json.loads((Path(local_todo.__file__).parent / 'manifest.json').read_text())
    assert ha_release.integration_requirements() == manifest['requirements']


def test_failed_release_can_be_retried(copy):
    readme = copy / 'README.md'
    original = readme.read_text()
    readme.write_text(original.replace('docs/lighting.md', 'missing.md'))
    before = {path: path.read_bytes() for path in copy.rglob('*') if path.is_file()}
    release = next_release()
    with pytest.raises(AssertionError):
        ha_release.apply(release)
    assert all(path.read_bytes() == content for path, content in before.items())
    readme.write_text(original)
    ha_release.apply(release)
    assert versioning.tested_ha() == release
