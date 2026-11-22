# SPDX-License-Identifier: GPL-3.0-only
"""Isolated test runs: Home Assistant never installs a package during the tests.

When an integration is loaded, Home Assistant installs its missing requirements with pip.
In the tests this would reach PyPI and silently replace the versions chosen by the project.
Requirement processing is therefore replaced by a check: every requirement must already be
installed at the exact version given by the manifest of the installed Home Assistant
release, otherwise the test fails and names the requirement. The versions to install are
written by « python tools/ha_release.py sync-requirements » (see CONTRIBUTING.md).
"""
import pytest
from homeassistant import requirements
from homeassistant.util import package


class MissingRequirement(AssertionError):
    pass


async def _check_only(self, name, reqs, is_built_in=True):
    missing = [req for req in reqs if not package.is_installed(req)]
    if missing:
        raise MissingRequirement(
            f'{name} needs {", ".join(missing)}: run « python tools/ha_release.py sync-requirements », '
            'then install requirements-test.txt again')


def _never_install(*args, **kwargs):
    raise MissingRequirement(f'Package installation attempted during the tests: {args}')


@pytest.fixture(autouse=True)
def no_package_installation(monkeypatch):
    monkeypatch.setattr(requirements.RequirementsManager, 'async_process_requirements', _check_only)
    monkeypatch.setattr(package, 'install_package', _never_install)
