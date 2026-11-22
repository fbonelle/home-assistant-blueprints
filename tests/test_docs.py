# SPDX-License-Identifier: GPL-3.0-only
"""Markdown pages: every link reaches an existing file and heading, every French page has
its English counterpart, and every import link points to a published blueprint."""
import re
import subprocess
import unicodedata
import urllib.parse
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PAGES = subprocess.check_output(['git', 'ls-files', '*.md'], cwd=ROOT, text=True).split()
REPO = 'https://github.com/fbonelle/home-assistant-blueprints/blob/main/'


def anchors(path):
    """GitHub heading anchors: lower case, punctuation removed, spaces turned into hyphens."""
    result = set()
    for heading in re.findall(r'^#+ +(.+?) *$', path.read_text(), flags=re.M):
        text = unicodedata.normalize('NFC', heading.strip().lower())
        text = re.sub(r'[^\w\- ]', '', text)
        result.add(text.replace(' ', '-'))
    return result


def target(page, url):
    """The repository file a link points to, or None for an external page."""
    if 'blueprint_url=' in url:
        url = urllib.parse.unquote(url.split('blueprint_url=')[1])
    if url.startswith(REPO):
        return ROOT / url[len(REPO):].split('#')[0], ''
    if url.startswith(('http://', 'https://', 'mailto:')):
        return None, ''
    path, _, anchor = url.partition('#')
    return ((ROOT / page).parent / path).resolve() if path else ROOT / page, anchor


@pytest.mark.parametrize('page', PAGES)
def test_links_reach_existing_files_and_headings(page):
    for url in re.findall(r'\]\(([^)\s]+)\)', (ROOT / page).read_text()):
        path, anchor = target(page, url)
        if path is None:
            continue
        assert path.exists(), (page, url)
        if anchor and path.suffix == '.md':
            assert urllib.parse.unquote(anchor) in anchors(path), (page, url)


@pytest.mark.parametrize('page', [p for p in PAGES if not p.endswith('.en.md')])
def test_every_french_page_has_an_english_page(page):
    assert (ROOT / page.replace('.md', '.en.md')).exists(), page
