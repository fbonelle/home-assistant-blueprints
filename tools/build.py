# SPDX-License-Identifier: GPL-3.0-only
"""Build every published blueprint from its sources; no runtime Python in Home Assistant."""
from pathlib import Path
import runpy

ROOT = Path(__file__).resolve().parent.parent
# Each blueprint family keeps its own version, sources and builder.
for builder in ['build_integration_watchdog', 'build_battery', 'build_notifications', 'build_lighting']:
    runpy.run_path(str(ROOT / 'tools' / f'{builder}.py'), run_name='__main__')
