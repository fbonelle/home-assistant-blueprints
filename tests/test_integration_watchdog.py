# SPDX-License-Identifier: GPL-3.0-only
"""Native Home Assistant 2026.10.4 tests of the self-contained integration watchdog.

The blueprint is expanded by Home Assistant itself and run either as a native Script
(with an injected clock) or as real automation entities. Only the integration reload
is replaced by a controlled service. Files and states live in pytest temporary folders.
"""
import asyncio
import copy
import json
import logging
from datetime import datetime, UTC
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
import pytest_asyncio

from homeassistant import core, loader
from homeassistant.bootstrap import async_load_base_functionality
from homeassistant.config_entries import ConfigEntries, ConfigEntry, ConfigEntryState
from homeassistant.components.automation.config import AUTOMATION_BLUEPRINT_SCHEMA, PLATFORM_SCHEMA
from homeassistant.components.blueprint.models import Blueprint, BlueprintInputs
from homeassistant.components.input_text import CONFIG_SCHEMA as TEXT_SCHEMA
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er, issue_registry as ir
from homeassistant.helpers import entity as entity_helper
from homeassistant.helpers.script import Script
from homeassistant.setup import async_setup_component
from homeassistant.util.yaml import load_yaml

ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = ROOT / 'examples' / 'integration_watchdog'
BLUEPRINT = ROOT / 'blueprints' / 'automation' / 'integration_watchdog' / 'surveillance_integrations.yaml'


class Env:
    async def setup(self, path, actual=False):
        self.hass = core.HomeAssistant(str(path))
        self.hass.config.time_zone = 'Europe/Paris'
        self.hass.config_entries = ConfigEntries(self.hass, {})
        loader.async_setup(self.hass)
        assert await async_load_base_functionality(self.hass)
        self.now = int(datetime.now(UTC).timestamp())
        # State writes get strictly increasing times (1 µs apart), as in a real event loop;
        # templates read the injected wall clock.
        self.micro = 0
        self.clock_patch = patch.object(core, 'time', SimpleNamespace(time=self.state_clock))
        self.clock_patch.start()
        self.entity_clock_patch = patch.object(entity_helper, 'timer', lambda: float(self.now))
        self.entity_clock_patch.start()
        from homeassistant.util import dt as dt_util
        self.now_patch = patch.object(dt_util, 'now', lambda time_zone=None: datetime.fromtimestamp(self.now, time_zone or UTC))
        self.now_patch.start()
        self.utcnow_patch = patch.object(dt_util, 'utcnow', lambda: datetime.fromtimestamp(self.now, UTC))
        self.utcnow_patch.start()
        self.calls = []
        self.modes = {}
        self.gates = {}
        self.monitors = []
        self.presets = load_yaml(str(EXAMPLES / 'automatisations_netatmo_overkiz.yaml'))
        self.rows = [dict(a['use_blueprint']['input']) for a in self.presets]
        self.entries = {}
        registry = er.async_get(self.hass)
        for row in self.rows:
            self.add_entry(row['entry_id'], 'netatmo' if row['name'] == 'Netatmo' else 'overkiz', row['name'])
            for entity in row['entities']:
                domain, obj = entity.split('.', 1)
                registered = registry.async_get_or_create(domain, self.entries[row['entry_id']].domain, entity,
                                                          suggested_object_id=obj, config_entry=self.entries[row['entry_id']])
                assert registered.entity_id == entity
                self.set(entity, '20')
        self.set('sensor.uptime', datetime.fromtimestamp(self.now - 10000, UTC).isoformat())
        self.bp = Blueprint(load_yaml(str(BLUEPRINT)), expected_domain='automation', schema=AUTOMATION_BLUEPRINT_SCHEMA)
        helpers = load_yaml(str(EXAMPLES / 'memoires_surveillance_integrations.yaml'))
        TEXT_SCHEMA(helpers)
        assert await async_setup_component(self.hass, 'input_text', helpers)
        assert await async_setup_component(self.hass, 'persistent_notification', {})
        # Both are always loaded by Home Assistant; no logger configuration is given.
        assert await async_setup_component(self.hass, 'system_log', {})
        assert await async_setup_component(self.hass, 'logger', {})
        self.hass.services.async_register('homeassistant', 'reload_config_entry', self.reload)
        if actual:
            await self.add_automations(path)
        await self.hass.async_start()
        await self.hass.async_block_till_done()
        await self.drain()
        return self

    def state_clock(self):
        self.micro += 1
        return float(self.now) + self.micro / 1_000_000

    def add_entry(self, entry_id, domain, title):
        entry = ConfigEntry(domain=domain, entry_id=entry_id, title=title, version=1, minor_version=1,
                            data={}, options={}, source='user', unique_id=entry_id, discovery_keys={},
                            subentries_data=None, state=ConfigEntryState.LOADED)
        self.hass.config_entries._entries[entry.entry_id] = entry
        self.entries[entry_id] = entry
        return entry

    def entry_state(self, entry_id, state):
        object.__setattr__(self.entries[entry_id], 'state', state)

    async def reload(self, call):
        """Controlled stand-in for homeassistant.reload_config_entry."""
        eid = call.data['entry_id']
        self.calls.append(eid)
        mode = self.modes.get(eid, 'fail')
        if mode == 'hold':
            await self.gates.setdefault(eid, asyncio.Event()).wait()
        elif mode == 'hang':
            await asyncio.Event().wait()
        elif mode == 'hang_unloaded':
            # Cut short after the unload: the entry stays unloaded.
            self.entry_state(eid, ConfigEntryState.NOT_LOADED)
            await asyncio.Event().wait()
        elif mode == 'error':
            raise HomeAssistantError('Controlled backend failure')
        elif mode == 'unload_failure':
            self.entry_state(eid, ConfigEntryState.FAILED_UNLOAD)
        elif mode == 'recover':
            self.entry_state(eid, ConfigEntryState.LOADED)
            row = next(r for r in self.rows if r['entry_id'] == eid)
            for entity in row['entities']:
                self.set(entity, '20')

    async def add_automations(self, path):
        target = path / 'blueprints' / 'automation' / 'local' / 'surveillance_integrations.yaml'
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(BLUEPRINT.read_text())
        if 'automation' in self.hass.config.components:
            from homeassistant.components.automation import _async_process_config
            from homeassistant.components.automation.config import async_validate_config
            from homeassistant.helpers.entity_component import DATA_INSTANCES
            validated = await async_validate_config(self.hass, {'automation': self.presets})
            await _async_process_config(self.hass, validated, self.hass.data[DATA_INSTANCES]['automation'])
        else:
            assert await async_setup_component(self.hass, 'automation', {'automation': self.presets})
        await self.hass.async_block_till_done()
        self.hass.services.async_register('homeassistant', 'reload_config_entry', self.reload)
        return {s.attributes.get('id'): s.entity_id for s in self.hass.states.async_all('automation')}

    def set(self, entity, value, age=0, attrs=None):
        self.hass.states.async_set(entity, value, attrs or {})
        state = self.hass.states.get(entity)
        stamp = datetime.fromtimestamp(self.now - age, UTC)
        state.last_changed = stamp
        state.last_updated = stamp
        state.last_reported = stamp
        return state

    def bad(self, index=0):
        for entity in self.rows[index]['entities']:
            self.set(entity, 'unavailable', age=1000)

    def healthy(self, index=0):
        for entity in self.rows[index]['entities']:
            self.set(entity, '20')

    def record(self, index=0):
        text = self.hass.states.get(self.rows[index]['memory']).state
        try:
            return json.loads(text[4:]) if text.startswith('iw3:') else None
        except json.JSONDecodeError:
            return None

    async def write_record(self, index, data, entity=None):
        text = 'iw3:' + json.dumps(data, separators=(',', ':'))
        await self.hass.services.async_call('input_text', 'set_value',
                                            {'entity_id': entity or self.rows[index]['memory'], 'value': text},
                                            blocking=True)

    async def monitor(self, index=0, **overrides):
        preset = copy.deepcopy(self.presets[index])
        if 'integrations' in overrides:
            rows = overrides.pop('integrations')
            overrides.update(rows[0])
        preset['use_blueprint']['input'].update(overrides)
        args = BlueprintInputs(self.bp, preset)
        args.validate()
        raw = args.async_substitute()
        raw['actions'][0]['variables']['clock_ts'] = '{{ injected_clock | int }}'
        expanded = PLATFORM_SCHEMA(raw)
        script = Script(self.hass, expanded['actions'], preset['alias'], 'automation',
                        script_mode=expanded['mode'], max_runs=expanded['max'],
                        max_exceeded=expanded['max_exceeded'], variables=expanded['variables'])
        self.monitors.append(script)
        return script, preset

    async def tick(self, index=0, advance=0, monitor=None, trigger=None, **overrides):
        self.now += advance
        if monitor is None:
            monitor = await self.monitor(index, **overrides)
        script, preset = monitor
        this = core.State('automation.' + preset['id'], 'on', {'id': preset['id']})
        await script.async_run({'injected_clock': self.now, 'this': this, 'trigger': trigger or {'id': 'scan'}},
                               context=core.Context())
        await self.drain()
        return self.record(index)

    async def drain(self):
        for _ in range(20):
            await asyncio.sleep(0)

    async def until(self, predicate, timeout=5):
        async def wait():
            while not predicate():
                await asyncio.sleep(0.001)
        await asyncio.wait_for(wait(), timeout)

    def notices(self):
        from homeassistant.components.persistent_notification import DOMAIN
        return self.hass.data[DOMAIN]

    async def close(self):
        if getattr(self, 'closed', False):
            return
        self.closed = True
        for gate in self.gates.values():
            gate.set()
        await self.drain()
        for script in self.monitors:
            await script.async_stop()
        await self.hass.async_stop()
        self.clock_patch.stop()
        self.entity_clock_patch.stop()
        self.now_patch.stop()
        self.utcnow_patch.stop()


@pytest_asyncio.fixture
async def env(tmp_path):
    e = await Env().setup(tmp_path)
    yield e
    await e.close()


class LoopClock:
    """Moves the event loop clock forward, so a wait timeout expires without waiting."""

    def __init__(self):
        self.loop = asyncio.get_running_loop()
        self.base = self.loop.time
        self.shift = 0.0
        self.loop.time = lambda: self.base() + self.shift

    async def advance(self, seconds):
        self.shift += seconds
        for _ in range(50):
            await asyncio.sleep(0)

    def restore(self):
        del self.loop.time


def add_helper(env, slug):
    from homeassistant.components.input_text import InputText, STORAGE_FIELDS
    import probatio
    cfg = probatio.Schema(STORAGE_FIELDS)({'name': slug, 'max': 255})
    helper = InputText.from_storage(dict(cfg, id=slug))
    helper.entity_id = 'input_text.' + slug
    return helper


async def add_supervision(env, slug, domain='overkiz'):
    from homeassistant.helpers.entity_component import DATA_INSTANCES
    helper = add_helper(env, slug)
    await env.hass.data[DATA_INSTANCES]['input_text'].async_add_entities([helper])
    eid = slug + '_entry'
    entity = 'sensor.' + slug
    entry = env.add_entry(eid, domain, slug)
    er.async_get(env.hass).async_get_or_create('sensor', domain, entity, suggested_object_id=slug, config_entry=entry)
    env.set(entity, '20')
    row = {'name': slug, 'entry_id': eid, 'entities': [entity], 'memory': helper.entity_id,
           'uptime_entity': 'sensor.uptime', 'max_age': 0, 'stagger_seconds': 0}
    env.rows.append(row)
    env.presets.append({'id': slug, 'alias': slug, 'use_blueprint': {'path': 'local/surveillance_integrations.yaml', 'input': row}})
    return len(env.rows) - 1


# ----------------------------------------------------------------------------- self-contained

@pytest.mark.asyncio
async def test_blueprint_is_self_contained(env):
    assert not (ROOT / 'packages').exists()
    text = BLUEPRINT.read_text()
    for removed in ['script.surveillance_', 'automation.surveillance_admission', 'integration_watchdog_request',
                    'integration_watchdog_completed', 'integration_watchdog_rearm']:
        assert removed not in text
    data = env.bp.data
    assert data['mode'] == 'queued' and data['max_exceeded'] == 'silent'
    assert [t['id'] for t in data['triggers']] == ['scan', 'availability', 'start']
    form = data['blueprint']['input']['surveillance']['input']
    assert all(k in form for k in ['entry_id', 'entities', 'memory'])
    assert all(k not in form for k in ['worker', 'integrations'])


@pytest.mark.asyncio
async def test_fourth_unlisted_integration_needs_only_helper_and_form_inputs(env):
    index = await add_supervision(env, 'surveillance_quatrieme', 'tuya')
    env.bad(index)
    data = await env.tick(index)
    assert env.calls == [env.rows[index]['entry_id']] and data['i'] == 1
    assert env.hass.states.async_entity_ids('script') == []
    assert env.hass.states.get(env.rows[index]['memory']).attributes['editable'] is True


# ----------------------------------------------------------------------------- logging

@pytest.mark.asyncio
async def test_logging_level_is_set_by_the_blueprint(env):
    logger = logging.getLogger('integration_watchdog')
    logger.setLevel(logging.WARNING)
    env.bad()
    await env.tick()
    assert logger.level == logging.INFO
    await env.tick(advance=60, detailed_logging=True)
    assert logger.level == logging.DEBUG


@pytest.mark.asyncio
async def test_logging_avoids_healthy_scan_spam_and_has_a_detailed_mode(env, caplog):
    with caplog.at_level(logging.DEBUG, logger='integration_watchdog'):
        await env.tick()
        count = len([r for r in caplog.records if r.name == 'integration_watchdog'])
        await env.tick(advance=60)
        assert len([r for r in caplog.records if r.name == 'integration_watchdog']) == count
        await env.tick(advance=60, detailed_logging=True)
        assert any(r.name == 'integration_watchdog' and r.levelno == logging.DEBUG for r in caplog.records)


@pytest.mark.asyncio
async def test_logging_does_not_include_sensor_values(env, caplog):
    env.set(env.rows[0]['entities'][0], 'SENSITIVE_SENSOR_VALUE')
    await env.drain()
    with caplog.at_level(logging.DEBUG, logger='integration_watchdog'):
        await env.tick(detailed_logging=True)
    assert all('SENSITIVE_SENSOR_VALUE' not in r.getMessage() for r in caplog.records if r.name == 'integration_watchdog')


@pytest.mark.asyncio
async def test_logging_errors_never_suppress_alerts(env):
    env.entry_state(env.rows[0]['entry_id'], ConfigEntryState.FAILED_UNLOAD)

    async def bad_log(call):
        raise HomeAssistantError('Controlled log failure')
    env.hass.services.async_register('system_log', 'write', bad_log)
    await env.tick()
    notice = 'integration_watchdog_' + env.rows[0]['entry_id']
    assert notice in env.notices() and env.record()['k'] == 'fatal'
    # Even without the service, the alert and its acknowledgement come first.
    env.hass.services.async_remove('system_log', 'write')
    data = env.record()
    data['k'] = ''
    await env.write_record(0, data)
    env.notices().pop(notice)
    try:
        await env.tick(advance=60)
    except HomeAssistantError:
        pass
    assert notice in env.notices() and env.record()['k'] == 'fatal'


# ----------------------------------------------------------------------------- configuration

@pytest.mark.asyncio
async def test_native_schemas_and_healthy_monitor(env):
    for index in range(3):
        data = await env.tick(index)
        assert data is not None and data['i'] == 0
        assert len(env.hass.states.get(env.rows[index]['memory']).state) <= 255
    assert env.calls == []


@pytest.mark.asyncio
async def test_native_exclusion_prevents_reload(env):
    env.bad()
    await env.tick(excluded_instances=[{'entry_id': env.rows[0]['entry_id']}])
    assert env.calls == []


@pytest.mark.asyncio
async def test_invalid_native_exclusion_is_notified(env):
    env.bad()
    await env.tick(excluded_instances=None)
    assert env.calls == [] and env.notices()


@pytest.mark.asyncio
async def test_null_memory_is_a_configuration_notice(env):
    row = copy.deepcopy(env.rows[0])
    row['memory'] = None
    await env.tick(integrations=[row])
    assert env.calls == [] and env.notices()


@pytest.mark.asyncio
@pytest.mark.parametrize('bad_value', [None, '3', 0, -1, 1.5, float('nan'), float('inf'), False, 11])
async def test_invalid_attempt_count_is_notified_without_reloading(env, bad_value):
    env.bad()
    await env.tick(max_attempts=bad_value)
    assert env.calls == [] and env.notices()


@pytest.mark.asyncio
@pytest.mark.parametrize('key,value', [
    ('memory', None), ('entry_id', 123), ('entities', None),
    ('max_age', None), ('max_age', float('nan')), ('stagger_seconds', -1),
    ('recovery_seconds', 0), ('policy', 'invalid'), ('source_time_entity', 123)])
async def test_invalid_rows_are_rejected_safely(env, key, value):
    row = copy.deepcopy(env.rows[0])
    row[key] = value
    await env.tick(integrations=[row])
    assert env.calls == [] and env.notices()


@pytest.mark.asyncio
async def test_unavailable_uptime_alerts_and_does_not_reload(env):
    env.bad()
    env.set('sensor.uptime', 'unavailable')
    await env.tick()
    assert env.calls == [] and env.notices()


@pytest.mark.asyncio
async def test_invalid_minimum_is_reported_without_claiming_memory(env):
    from homeassistant.helpers.entity_component import DATA_INSTANCES
    helper = env.hass.data[DATA_INSTANCES]['input_text'].get_entity(env.rows[0]['memory'])
    helper._attr_native_min = 255
    helper.async_write_ha_state()
    env.bad()
    await env.tick()
    assert env.notices() and env.record() is None and not env.calls


@pytest.mark.asyncio
async def test_default_notifications_have_all_template_variables_and_no_template_warnings(env, caplog):
    env.entry_state(env.rows[0]['entry_id'], ConfigEntryState.FAILED_UNLOAD)
    await env.tick()
    assert not any('Template variable warning' in r.message for r in caplog.records)
    notice = env.notices()['integration_watchdog_' + env.rows[0]['entry_id']]
    assert 'Netatmo' in str(notice) and 'failed_unload' in str(notice)


# ----------------------------------------------------------------------------- memory

@pytest.mark.asyncio
async def test_corrupted_memory_is_not_reset(env):
    row = env.rows[0]
    await env.hass.services.async_call('input_text', 'set_value', {'entity_id': row['memory'], 'value': 'iw3:{broken'}, blocking=True)
    env.bad()
    await env.tick()
    assert env.hass.states.get(row['memory']).state == 'iw3:{broken'
    assert env.calls == [] and env.notices()


@pytest.mark.asyncio
async def test_owner_prevents_reusing_same_memory_in_another_automation(env):
    await env.tick()
    monitor = await env.monitor()
    monitor[1]['id'] = 'another_owner'
    env.bad()
    await env.tick(monitor=monitor)
    assert env.calls == [] and env.notices()


@pytest.mark.asyncio
async def test_existing_helper_cannot_be_retargeted_to_another_instance(env):
    await env.tick()
    before = env.record()
    row = dict(env.rows[1], memory=env.rows[0]['memory'])
    await env.tick(1, integrations=[row])
    assert env.record() == before and env.notices() and not env.calls


@pytest.mark.asyncio
async def test_full_history_stays_within_native_memory_capacity(env):
    for index, row in enumerate(env.rows):
        await env.tick(index)
        data = env.record(index)
        data.update(a=[env.now - i for i in range(6)], i=3, n=env.now + 3600, p=env.now * 1000000, f=env.now,
                    h=env.now, t=env.now, s='suspended', k='suspended')
        await env.write_record(index, data)
        assert len(env.hass.states.get(row['memory']).state) <= 255
        assert env.record(index)['a'] == data['a']


@pytest.mark.asyncio
async def test_capacity_all_memory_fields_with_six_attempts_is_checked_by_real_planner(env):
    await env.tick()
    d = env.record()
    d.update(a=[env.now - i for i in range(6)], i=3, n=env.now + 3600, p=env.now * 1000000, f=2, h=env.now,
             t=env.now, s='timeout', k='timeout')
    await env.write_record(0, d)
    data = await env.tick(advance=60)
    assert data['i'] == 3 and len(data['a']) == 6 and data['p'] == 0 and data['s'] == 'verify'
    assert len(env.hass.states.get(env.rows[0]['memory']).state) <= 255


@pytest.mark.asyncio
async def test_clock_rollback_stops_without_resetting_budgets(env):
    env.bad()
    await env.tick()
    before = env.record()
    env.now -= 120
    await env.tick()
    assert env.record() == before and len(env.calls) == 1 and env.notices()


@pytest.mark.asyncio
async def test_legacy_migration_preserves_daily_and_incident_budgets(env):
    legacy = {'v': 2, 'o': 'w_' + env.presets[0]['id'], 'a': [env.now - 100], 'i': 2, 'n': 0, 'p': 0, 'f': 0,
              'h': 0, 't': env.now, 's': 'suspended', 'k': 'suspended'}
    await env.hass.services.async_call('input_text', 'set_value', {'entity_id': env.rows[0]['memory'],
                                       'value': 'iw2:' + json.dumps(legacy, separators=(',', ':'))}, blocking=True)
    await env.tick()
    d = env.record()
    assert d['v'] == 3 and d['i'] == 2 and d['a'] == legacy['a'] and d['e'].startswith('e_')


@pytest.mark.asyncio
async def test_restart_restores_the_budget(env, tmp_path):
    env.bad()
    await env.tick()
    before = env.record()
    assert before['i'] == 1 and len(before['a']) == 1
    await env.close()
    restarted = await Env().setup(tmp_path)
    try:
        restored = restarted.record()
        assert restored['i'] == 1 and restored['a'] == before['a']
        restarted.set('sensor.uptime', datetime.fromtimestamp(restarted.now, UTC).isoformat())
        await restarted.tick()
        assert restarted.record()['i'] == 1 and restarted.calls == []
    finally:
        await restarted.close()


# ----------------------------------------------------------------------------- reload inside the run

@pytest.mark.asyncio
async def test_reload_runs_inside_the_run_and_opens_verification(env):
    env.bad()
    data = await env.tick()
    assert env.calls == [env.rows[0]['entry_id']]
    assert data['p'] == 0 and data['f'] > 2 and data['s'] == 'verify' and data['i'] == 1 and len(data['a']) == 1


@pytest.mark.asyncio
async def test_backend_error_still_opens_verification_without_claiming_success(env):
    env.bad()
    env.modes[env.rows[0]['entry_id']] = 'error'
    data = await env.tick()
    assert data['s'] == 'verify' and data['i'] == 1 and data['p'] == 0
    assert env.calls == [env.rows[0]['entry_id']]


@pytest.mark.asyncio
async def test_queued_runs_wait_and_never_reload_twice(env):
    env.bad()
    eid = env.rows[0]['entry_id']
    env.modes[eid] = 'hold'
    monitor = await env.monitor()
    first = asyncio.create_task(env.tick(monitor=monitor))
    await env.until(lambda: env.calls == [eid])
    others = [asyncio.create_task(env.tick(advance=60, monitor=monitor)) for _ in range(5)]
    await env.drain()
    assert env.record()['f'] == 2 and env.calls == [eid]
    env.gates[eid].set()
    await asyncio.gather(first, *others)
    assert env.calls == [eid] and env.record()['i'] == 1 and env.record()['s'] == 'verify'


@pytest.mark.asyncio
async def test_simultaneous_supervision_runs_do_not_duplicate_requests(env):
    env.bad()
    monitor = await env.monitor()
    await asyncio.gather(env.tick(monitor=monitor), env.tick(monitor=monitor))
    assert len(env.calls) == 1 and env.record()['i'] == 1 and len(env.record()['a']) == 1


@pytest.mark.asyncio
async def test_stuck_reload_alerts_after_delay_without_cancelling_it(env):
    env.bad()
    eid = env.rows[0]['entry_id']
    env.modes[eid] = 'hold'
    clock = LoopClock()
    try:
        task = asyncio.create_task(env.tick(reload_timeout=60))
        await env.until(lambda: env.calls == [eid])
        notice = 'integration_watchdog_' + eid
        assert notice not in env.notices()
        env.now += 61
        await clock.advance(61)
        assert notice in env.notices() and 'ne s’est' not in str(env.notices()[notice])
        assert '60 secondes' in str(env.notices()[notice])
        # The reload is not cancelled: its end is still recorded and verified.
        assert not task.done() and env.record()['f'] == 2
        env.gates[eid].set()
        await task
    finally:
        clock.restore()
    data = env.record()
    assert data['s'] == 'verify' and data['k'] == 'timeout' and data['p'] == 0 and len(env.calls) == 1


@pytest.mark.asyncio
async def test_stuck_reload_does_not_block_other_supervisions(env):
    env.bad(0)
    env.modes[env.rows[0]['entry_id']] = 'hold'
    stuck = asyncio.create_task(env.tick(0))
    await env.until(lambda: len(env.calls) == 1)
    index = 1
    env.bad(index)
    await env.tick(index, integrations=[dict(env.rows[index], stagger_seconds=0)])
    assert env.calls == [env.rows[0]['entry_id'], env.rows[index]['entry_id']]
    env.gates[env.rows[0]['entry_id']].set()
    await stuck


@pytest.mark.asyncio
async def test_interrupted_reload_with_loaded_entry_opens_verification(env):
    env.bad()
    env.modes[env.rows[0]['entry_id']] = 'hang'
    monitor = await env.monitor()
    task = asyncio.create_task(env.tick(monitor=monitor))
    await env.until(lambda: len(env.calls) == 1)
    await monitor[0].async_stop()
    await asyncio.gather(task, return_exceptions=True)
    assert env.record()['p'] > 0 and env.record()['f'] == 2
    data = await env.tick(advance=60)
    assert data['p'] == 0 and data['s'] == 'verify' and data['i'] == 1 and len(env.calls) == 1


@pytest.mark.asyncio
async def test_interrupted_reload_that_left_the_entry_unloaded_is_resumed(env):
    eid = env.rows[0]['entry_id']
    env.bad()
    env.modes[eid] = 'hang_unloaded'
    monitor = await env.monitor()
    task = asyncio.create_task(env.tick(monitor=monitor))
    await env.until(lambda: len(env.calls) == 1)
    await monitor[0].async_stop()
    await asyncio.gather(task, return_exceptions=True)
    assert env.entries[eid].state is ConfigEntryState.NOT_LOADED
    env.modes[eid] = 'recover'
    data = await env.tick(advance=60)
    assert env.calls == [eid, eid] and env.entries[eid].state is ConfigEntryState.LOADED
    assert data['i'] == 2 and len(data['a']) == 2 and data['s'] == 'verify'


@pytest.mark.asyncio
async def test_interrupted_reload_resumption_respects_the_budget(env):
    eid = env.rows[0]['entry_id']
    await env.tick()
    d = env.record()
    d.update(i=3, p=env.now * 1000000, f=2, s='running')
    await env.write_record(0, d)
    env.entry_state(eid, ConfigEntryState.NOT_LOADED)
    env.bad()
    data = await env.tick(advance=60)
    assert env.calls == [] and data['s'] == 'suspended' and env.notices()


@pytest.mark.asyncio
async def test_never_admitted_reservation_is_dropped_without_spending_budget(env):
    await env.tick()
    d = env.record()
    d.update(p=env.now * 1000000, f=0, s='running')
    await env.write_record(0, d)
    data = await env.tick(advance=60)
    assert data['p'] == 0 and data['i'] == 0 and data['a'] == [] and env.calls == []


@pytest.mark.asyncio
async def test_unfinished_closing_is_done_before_validation(env):
    """A finished or interrupted reload is closed even when the settings are invalid."""
    await env.tick()
    d = env.record()
    d.update(i=1, a=[env.now], p=env.now * 1000000, f=env.now + 1, s='running')
    await env.write_record(0, d)

    async def bad_notice(call):
        raise HomeAssistantError('Controlled auxiliary failure')
    env.hass.services.async_register('test', 'failure', bad_notice)
    with pytest.raises(HomeAssistantError):
        await env.tick(advance=60, configuration_resolved_actions=[{'action': 'test.failure'}])
    assert env.record()['p'] == 0 and env.record()['s'] == 'verify'


@pytest.mark.asyncio
async def test_exclusion_preserves_closing_and_budget(env):
    await env.tick()
    d = env.record()
    d.update(i=1, a=[env.now], p=env.now * 1000000, f=2, s='running')
    await env.write_record(0, d)
    await env.tick(advance=60, excluded_instances=[{'entry_id': env.rows[0]['entry_id']}])
    data = env.record()
    assert data['p'] == 0 and data['i'] == 1 and len(data['a']) == 1 and data['s'] == 'verify'


# ----------------------------------------------------------------------------- admission

@pytest.mark.asyncio
async def test_fifty_one_simultaneous_requests_admit_fifty_and_defer_one(env):
    for number in range(48):
        await add_supervision(env, 'surveillance_stress_' + str(number))
    for index, row in enumerate(env.rows):
        env.bad(index)
        env.modes[row['entry_id']] = 'hold'
    monitors = [await env.monitor(i, stagger_seconds=0) for i in range(51)]
    tasks = [asyncio.create_task(env.tick(i, monitor=m)) for i, m in enumerate(monitors)]
    await env.until(lambda: len(env.calls) == 50 and sum(env.record(i)['p'] == 0 for i in range(51)) == 1)
    await env.drain()
    assert len(env.calls) == 50 and len(set(env.calls)) == 50
    records = [env.record(i) for i in range(51)]
    assert sum(d['i'] for d in records) == 50 and sum(len(d['a']) for d in records) == 50
    deferred = [d for d in records if d['s'] == 'deferred']
    assert len(deferred) == 1 and deferred[0]['i'] == 0
    for gate in env.gates.values():
        gate.set()
    await asyncio.gather(*tasks)


@pytest.mark.asyncio
async def test_full_pool_defers_and_stale_reservations_are_ignored(env):
    from homeassistant.helpers.entity_component import DATA_INSTANCES
    running = {'v': 3, 'o': 'w_other', 'a': [], 'i': 1, 'n': 0, 'p': env.now * 1000000, 'f': 2, 'h': 0,
               't': env.now, 's': 'running', 'k': ''}
    for number in range(50):
        helper = add_helper(env, 'surveillance_busy_' + str(number))
        await env.hass.data[DATA_INSTANCES]['input_text'].async_add_entities([helper])
        await env.write_record(0, dict(running, o='w_busy' + str(number), e='e_busy' + str(number)), helper.entity_id)
    index = 1
    row = dict(env.rows[index], stagger_seconds=0)
    env.bad(index)
    data = await env.tick(index, integrations=[row])
    assert env.calls == [] and data['s'] == 'deferred' and data['i'] == 0 and data['a'] == []
    # One hour later these reservations belong to supervisions that never came back.
    data = await env.tick(index, advance=3601, integrations=[row])
    assert env.calls == [row['entry_id']] and data['i'] == 1


@pytest.mark.asyncio
async def test_duplicate_supervisor_is_detected_and_never_admitted_twice(env):
    from homeassistant.helpers.entity_component import DATA_INSTANCES
    helper = add_helper(env, 'surveillance_copie')
    await env.hass.data[DATA_INSTANCES]['input_text'].async_add_entities([helper])
    env.bad()
    env.modes[env.rows[0]['entry_id']] = 'hold'
    a = await env.monitor()
    b = await env.monitor(memory=helper.entity_id)
    b[1]['id'] = 'another_supervisor'
    tasks = [asyncio.create_task(env.tick(monitor=a)), asyncio.create_task(env.tick(monitor=b))]
    await env.drain()
    await asyncio.sleep(0.05)
    assert len(env.calls) <= 1
    env.gates.setdefault(env.rows[0]['entry_id'], asyncio.Event()).set()
    await asyncio.gather(*tasks)
    await env.tick(monitor=a, advance=60)
    await env.tick(monitor=b, advance=60)
    assert len(env.calls) <= 1 and env.notices()


# ----------------------------------------------------------------------------- policy

@pytest.mark.asyncio
async def test_native_reauth_guard_prevents_reload(env):
    env.bad()
    row = env.rows[0]
    ir.async_create_issue(env.hass, 'homeassistant', 'config_entry_reauth_netatmo_' + row['entry_id'],
                          is_fixable=False, severity=ir.IssueSeverity.ERROR, translation_key='config_entry_reauth')
    data = await env.tick()
    assert data['s'] == 'auth' and env.calls == []
    assert env.notices()


@pytest.mark.asyncio
async def test_failed_unload_is_notified(env):
    env.bad()
    env.modes[env.rows[0]['entry_id']] = 'unload_failure'
    data = await env.tick()
    assert data['s'] == 'fatal' and env.notices()


@pytest.mark.asyncio
async def test_initial_fatal_state_is_notified(env):
    env.bad()
    env.entry_state(env.rows[0]['entry_id'], ConfigEntryState.MIGRATION_ERROR)
    data = await env.tick()
    assert data['s'] == 'fatal' and env.calls == [] and env.notices()


@pytest.mark.asyncio
async def test_not_loaded_entry_without_interruption_is_not_forced(env):
    env.bad()
    env.entry_state(env.rows[0]['entry_id'], ConfigEntryState.NOT_LOADED)
    data = await env.tick()
    assert data['s'] == 'fatal' and env.calls == [] and env.notices()


@pytest.mark.asyncio
async def test_autonomous_recovery_dismisses_alarm_after_stability(env):
    index = 1
    row = env.rows[index]
    env.entry_state(row['entry_id'], ConfigEntryState.MIGRATION_ERROR)
    await env.tick(index)
    notice = 'integration_watchdog_' + row['entry_id']
    assert notice in env.notices()
    env.entry_state(row['entry_id'], ConfigEntryState.LOADED)
    env.healthy(index)
    await env.tick(index, advance=60)
    for _ in range(3):
        data = await env.tick(index, advance=60)
    assert data['s'] == 'healthy' and data['k'] == ''
    assert notice not in env.notices() and env.calls == []


@pytest.mark.asyncio
async def test_transient_recovery_does_not_declare_success(env):
    index = 1
    row = copy.deepcopy(env.rows[index])
    row['stagger_seconds'] = 0
    env.bad(index)
    env.modes[row['entry_id']] = 'recover'
    await env.tick(index, integrations=[row])
    await env.tick(index, advance=60, integrations=[row])
    await env.tick(index, advance=60, integrations=[row])
    env.bad(index)
    data = await env.tick(index, advance=60, integrations=[row])
    assert data['s'] != 'healthy' and data['i'] == 1
    assert env.calls == [row['entry_id']]


@pytest.mark.asyncio
async def test_incident_budget_suspends_indefinite_cycles(env):
    index = 1
    row = dict(env.rows[index], stagger_seconds=0, recovery_seconds=180)
    env.bad(index)
    data = await env.tick(index, integrations=[row])
    for _ in range(10):
        data = await env.tick(index, advance=180, integrations=[row])
        if data['s'] == 'suspended':
            break
        env.now = data['n']
        data = await env.tick(index, integrations=[row])
    assert data['s'] == 'suspended' and len(env.calls) == 3
    await env.tick(index, advance=86401, integrations=[row])
    assert len(env.calls) == 3 and env.record(index)['s'] == 'suspended'


@pytest.mark.asyncio
async def test_rolling_24h_budget_does_not_reset_on_midnight(env):
    index = 1
    row = dict(env.rows[index], stagger_seconds=0)
    await env.tick(index)
    data = env.record(index)
    data.update(a=[env.now - 100 - i for i in range(6)], i=0, s='healthy', h=0)
    await env.write_record(index, data)
    env.bad(index)
    data = await env.tick(index, integrations=[row])
    assert data['s'] == 'limited' and env.calls == []
    await env.tick(index, advance=86401, integrations=[row])
    assert env.calls == [row['entry_id']]


@pytest.mark.asyncio
async def test_long_gap_does_not_count_as_observed_stability(env):
    await env.tick(1)
    data = await env.tick(1, advance=1800)
    assert data['s'] != 'healthy' and data['h'] == env.now


@pytest.mark.asyncio
async def test_failed_notification_is_retried_before_acknowledgement(env):
    row = env.rows[0]
    env.bad()
    env.entry_state(row['entry_id'], ConfigEntryState.FAILED_UNLOAD)
    sent = []

    async def notify(call):
        sent.append(call.data)
        if len(sent) == 1:
            raise HomeAssistantError('Controlled notification failure')
    env.hass.services.async_register('test', 'notify', notify)
    args = {'failure_actions': [{'action': 'test.notify'}]}
    with pytest.raises(HomeAssistantError):
        await env.tick(**args)
    assert env.record()['k'] == ''
    await env.tick(advance=60, **args)
    assert len(sent) == 2 and env.record()['k'] == 'fatal'


@pytest.mark.asyncio
async def test_maintenance_stops_interventions_but_not_observation(env):
    env.bad()
    data = await env.tick(additional_conditions=[{'condition': 'template', 'value_template': '{{ false }}'}])
    assert data['s'] == 'paused' and env.calls == []


@pytest.mark.asyncio
async def test_observation_only_never_reloads(env):
    env.bad()
    data = await env.tick(observation_only=True)
    assert data['s'] == 'observation' and env.calls == []


@pytest.mark.asyncio
async def test_native_retry_is_respected(env):
    env.bad()
    env.entry_state(env.rows[0]['entry_id'], ConfigEntryState.SETUP_RETRY)
    data = await env.tick()
    assert data['s'] == 'native' and env.calls == []


@pytest.mark.asyncio
async def test_long_native_retry_alerts_without_forcing_a_reload(env):
    env.bad()
    env.entry_state(env.rows[0]['entry_id'], ConfigEntryState.SETUP_RETRY)
    await env.tick()
    data = await env.tick(advance=1801)
    assert data['s'] == 'native' and data['k'] == 'native' and env.calls == [] and env.notices()


@pytest.mark.asyncio
async def test_native_retry_deadline_is_not_reused_as_a_recovery_pause(env):
    env.bad()
    entry_id = env.rows[0]['entry_id']
    env.entry_state(entry_id, ConfigEntryState.SETUP_RETRY)
    await env.tick()
    env.entry_state(entry_id, ConfigEntryState.LOADED)
    data = await env.tick(advance=60)
    assert data['s'] == 'verify' and len(env.calls) == 1


@pytest.mark.asyncio
async def test_disabled_entry_is_respected(env):
    from homeassistant.config_entries import ConfigEntryDisabler
    env.bad()
    object.__setattr__(env.entries[env.rows[0]['entry_id']], 'disabled_by', ConfigEntryDisabler.USER)
    data = await env.tick()
    assert data['s'] == 'disabled' and env.calls == []


@pytest.mark.asyncio
async def test_report_during_reload_alone_is_not_sufficient(env):
    env.bad()
    env.modes[env.rows[0]['entry_id']] = 'recover'
    await env.tick()
    await env.tick(advance=60)
    for _ in range(4):
        data = await env.tick(advance=60)
    assert data['s'] == 'verify' and data['h'] == 0 and len(env.calls) == 1


@pytest.mark.asyncio
async def test_post_reload_fresh_report_and_stability_are_required(env):
    env.bad()
    env.modes[env.rows[0]['entry_id']] = 'recover'
    await env.tick()
    await env.tick(advance=60)
    env.now += 60
    env.healthy()
    await env.drain()
    await env.tick()
    for _ in range(3):
        data = await env.tick(advance=60)
    assert data['s'] == 'healthy' and data['i'] == 1
    assert len(env.calls) == 1


@pytest.mark.asyncio
async def test_subsecond_pre_completion_reports_are_not_fresh(env):
    eid = env.rows[0]['entry_id']
    env.bad()
    env.modes[eid] = 'hold'
    task = asyncio.create_task(env.tick())
    await env.until(lambda: len(env.calls) == 1)
    env.now += 60
    for entity in env.rows[0]['entities']:
        state = env.set(entity, '20')
        state.last_reported = datetime.fromtimestamp(env.now + 0.2, UTC)
    env.now += 0.9
    env.gates[eid].set()
    await task
    for _ in range(4):
        data = await env.tick(advance=60)
    assert data['s'] == 'verify' and data['h'] == 0
    env.healthy()
    await env.tick(advance=1)
    for _ in range(3):
        data = await env.tick(advance=60)
    assert data['s'] == 'healthy'


@pytest.mark.asyncio
async def test_real_source_timestamp_can_detect_frozen_data(env):
    env.set('sensor.source_time', datetime.fromtimestamp(env.now - 3600, UTC).isoformat())
    row = dict(env.rows[0], source_time_entity='sensor.source_time')
    await env.tick(integrations=[row])
    assert env.calls == [row['entry_id']]


@pytest.mark.asyncio
async def test_invalid_source_timestamp_is_not_reloaded_blindly(env):
    env.set('sensor.source_time', 'unknown')
    row = dict(env.rows[0], source_time_entity='sensor.source_time')
    data = await env.tick(integrations=[row])
    assert data['s'] == 'fatal' and env.calls == [] and env.notices()


@pytest.mark.asyncio
async def test_quick_relapse_keeps_incident_budget(env):
    index = 1
    row = dict(env.rows[index], stagger_seconds=0)
    env.bad(index)
    env.modes[row['entry_id']] = 'recover'
    await env.tick(index, integrations=[row])
    await env.tick(index, advance=60, integrations=[row])
    for _ in range(3):
        data = await env.tick(index, advance=60, integrations=[row])
    assert data['s'] == 'healthy' and data['i'] == 1
    env.bad(index)
    await env.drain()
    data = await env.tick(index, advance=60, integrations=[row])
    assert data['i'] == 2 and len(env.calls) == 2


@pytest.mark.asyncio
async def test_stable_recovery_rearms_incident_but_keeps_daily_history(env):
    index = 1
    row = dict(env.rows[index], stagger_seconds=0)
    env.bad(index)
    env.modes[row['entry_id']] = 'recover'
    await env.tick(index, integrations=[row])
    await env.tick(index, advance=60, integrations=[row])
    for _ in range(31):
        data = await env.tick(index, advance=60, integrations=[row])
    assert data['s'] == 'healthy' and data['i'] == 0 and len(data['a']) == 1


@pytest.mark.asyncio
async def test_manual_run_resets_attempts_but_keeps_daily_history(env):
    index = 1
    await env.tick(index)
    before = env.record(index)
    before.update(i=3, a=[env.now - 100], s='suspended')
    await env.write_record(index, before)
    # "Run actions" in the automation menu: no trigger id.
    data = await env.tick(index, trigger={'platform': None})
    assert data['i'] == 0 and data['a'] == before['a']


# ----------------------------------------------------------------------------- real automation entities

@pytest.mark.asyncio
async def test_actual_automation_entity_reloads_and_manual_run_retries(env, tmp_path):
    entities = await env.add_automations(tmp_path)
    entity = entities[env.presets[0]['id']]
    env.bad()
    await env.drain()
    await env.hass.services.async_call('automation', 'trigger', {'entity_id': entity, 'skip_condition': False}, blocking=True)
    await env.hass.async_block_till_done()
    assert env.calls == [env.rows[0]['entry_id']]
    data = env.record()
    assert data['p'] == 0 and data['f'] > 2 and data['s'] == 'verify' and data['i'] == 1
    # A periodic check during the verification window does not reload again.
    env.now += 60
    from homeassistant.helpers.entity_component import DATA_INSTANCES
    automation = env.hass.data[DATA_INSTANCES]['automation'].get_entity(entity)
    await automation.async_trigger({'trigger': {'id': 'scan', 'platform': 'time_pattern'}})
    await env.hass.async_block_till_done()
    assert len(env.calls) == 1 and env.record()['i'] == 1
    # "Run actions" resets the attempts of this failure and retries at once.
    await env.hass.services.async_call('automation', 'trigger', {'entity_id': entity, 'skip_condition': False}, blocking=True)
    await env.hass.async_block_till_done()
    assert len(env.calls) == 2 and env.record()['i'] == 1 and len(env.record()['a']) == 2


@pytest.mark.asyncio
async def test_actual_manual_run_resets_attempts(env, tmp_path):
    entities = await env.add_automations(tmp_path)
    target = entities[env.presets[1]['id']]
    await env.hass.services.async_call('automation', 'trigger', {'entity_id': target}, blocking=True)
    await env.hass.async_block_till_done()
    before = env.record(1)
    before.update(i=3, a=[env.now - 100], s='suspended')
    await env.write_record(1, before)
    await env.hass.services.async_call('automation', 'trigger', {'entity_id': target}, blocking=True)
    await env.hass.async_block_till_done()
    assert env.record(1)['i'] == 0 and env.record(1)['a'] == before['a']


@pytest.mark.asyncio
async def test_actual_availability_trigger_resets_stability_without_a_probe(env, tmp_path):
    entities = await env.add_automations(tmp_path)
    target = entities[env.presets[1]['id']]
    await env.hass.services.async_call('automation', 'trigger', {'entity_id': target, 'skip_condition': False}, blocking=True)
    await env.hass.async_block_till_done()
    data = env.record(1)
    data['h'] -= 179
    await env.write_record(1, data)
    entity = env.rows[1]['entities'][0]
    env.set(entity, 'unavailable')
    await env.hass.async_block_till_done()
    assert env.record(1)['h'] == 0
    env.set(entity, '20')
    await env.hass.async_block_till_done()
    assert env.record(1)['h'] >= data['h'] + 170
    assert env.record(1)['s'] != 'healthy' and env.calls == []


@pytest.mark.asyncio
async def test_actual_value_changes_do_not_reset_availability_stability(env, tmp_path):
    entities = await env.add_automations(tmp_path)
    target = entities[env.presets[1]['id']]
    await env.hass.services.async_call('automation', 'trigger', {'entity_id': target, 'skip_condition': False}, blocking=True)
    await env.hass.async_block_till_done()
    data = env.record(1)
    data['h'] -= 100
    await env.write_record(1, data)
    env.set(env.rows[1]['entities'][0], '30')
    await env.hass.async_block_till_done()
    assert env.record(1)['h'] == data['h']


@pytest.mark.asyncio
async def test_actual_restart_closes_interrupted_work_without_refunding_budget(env, tmp_path):
    entities = await env.add_automations(tmp_path)
    env.bad()
    env.modes[env.rows[0]['entry_id']] = 'hang'
    await env.drain()
    await env.hass.services.async_call('automation', 'trigger', {'entity_id': entities[env.presets[0]['id']],
                                       'skip_condition': False}, blocking=False)
    await env.until(lambda: len(env.calls) == 1)
    before = env.record()
    assert before['p'] > 0 and before['f'] == 2 and before['i'] == 1
    await env.close()
    restarted = await Env().setup(tmp_path, actual=True)
    try:
        await restarted.hass.async_block_till_done()
        d = restarted.record()
        assert d['p'] == 0 and d['i'] == 1 and d['a'] == before['a']
        assert d['s'] == 'verify' and restarted.calls == []
    finally:
        await restarted.close()


@pytest.mark.asyncio
async def test_actual_automation_disabled_during_reload_resumes_an_unloaded_entry(env, tmp_path):
    entities = await env.add_automations(tmp_path)
    target = entities[env.presets[0]['id']]
    eid = env.rows[0]['entry_id']
    env.bad()
    env.modes[eid] = 'hang_unloaded'
    await env.drain()
    await env.hass.services.async_call('automation', 'trigger', {'entity_id': target, 'skip_condition': False}, blocking=False)
    await env.until(lambda: len(env.calls) == 1)
    await env.hass.services.async_call('automation', 'turn_off', {'entity_id': target}, blocking=True)
    await env.hass.async_block_till_done()
    assert env.record()['f'] == 2 and env.entries[eid].state is ConfigEntryState.NOT_LOADED
    env.modes[eid] = 'recover'
    await env.hass.services.async_call('automation', 'turn_on', {'entity_id': target}, blocking=True)
    from homeassistant.helpers.entity_component import DATA_INSTANCES
    automation = env.hass.data[DATA_INSTANCES]['automation'].get_entity(target)
    await automation.async_trigger({'trigger': {'id': 'scan', 'platform': 'time_pattern'}})
    await env.hass.async_block_till_done()
    d = env.record()
    assert env.calls == [eid, eid] and env.entries[eid].state is ConfigEntryState.LOADED
    assert d['p'] == 0 and d['i'] == 2 and d['s'] == 'verify'


@pytest.mark.asyncio
async def test_manual_run_keeps_an_interrupted_reload_resumable(env):
    eid = env.rows[0]['entry_id']
    await env.tick()
    d = env.record()
    d.update(i=3, a=[env.now], p=env.now * 1000000, f=2, s='running')
    await env.write_record(0, d)
    env.entry_state(eid, ConfigEntryState.NOT_LOADED)
    env.bad()
    env.modes[eid] = 'recover'
    data = await env.tick(advance=60, trigger={'platform': None})
    assert env.calls == [eid] and data['i'] == 1 and len(data['a']) == 2
