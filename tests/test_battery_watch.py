# SPDX-License-Identifier: GPL-3.0-only
"""Native Home Assistant 2026.10.4: blueprint schema, registries, Local To-do memory, notifications.

Battery entities are plain states attached to real config entries, devices and labels. The memory is a
real Local To-do list stored in the temporary configuration directory. Only the notification target is
a recording service; nothing contacts a device or a provider.
"""
import asyncio
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
import pytest_asyncio

from homeassistant import core, loader
from homeassistant.bootstrap import async_load_base_functionality
from homeassistant.components.automation.config import AUTOMATION_BLUEPRINT_SCHEMA, PLATFORM_SCHEMA
from homeassistant.components.blueprint.models import Blueprint, BlueprintInputs
from homeassistant.config_entries import ConfigEntries, ConfigEntry, ConfigEntryState
from homeassistant.helpers import device_registry as dr, entity as entity_helper
from homeassistant.helpers import entity_registry as er, label_registry as lr
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util
from homeassistant.util.yaml import load_yaml

ROOT = Path(__file__).resolve().parent.parent
BP = ROOT / 'blueprints/automation/battery_watch/surveillance_piles.yaml'
EXAMPLES = ROOT / 'examples/battery_watch'
MEMORY = 'todo.piles_et_batteries'
AUTOMATION = 'automation.surveillance_des_piles_et_batteries_maison'
WEEKDAYS = ['mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun']


class BatteryEnv:
    async def setup(self, path, overrides=None):
        # A fixed Wednesday morning keeps the weekday tests deterministic.
        self.now = datetime(2026, 11, 11, 6, 0, tzinfo=UTC)
        self.hass = core.HomeAssistant(str(path))
        self.hass.config_entries = ConfigEntries(self.hass, {})
        self.hass.config.time_zone = 'Europe/Paris'
        loader.async_setup(self.hass)
        assert await async_load_base_functionality(self.hass)
        self.patches = [
            patch.object(dt_util, 'now', lambda time_zone=None: self.now.astimezone(time_zone or UTC)),
            patch.object(dt_util, 'utcnow', lambda: self.now),
            patch.object(core, 'time', SimpleNamespace(time=lambda: self.now.timestamp())),
            patch.object(entity_helper, 'timer', lambda: self.now.timestamp()),
        ]
        for p in self.patches:
            p.start()
        # The to-do panel depends on the HTTP server; it is not needed to call the to-do services.
        self.hass.config.components.add('http')
        todo_entry = ConfigEntry(domain='local_todo', entry_id='entry_local_todo', title='Piles et batteries',
                                 version=1, minor_version=1, source='user', unique_id='piles_et_batteries',
                                 data={'todo_list_name': 'Piles et batteries', 'storage_key': 'piles_et_batteries'},
                                 options={}, discovery_keys={}, subentries_data=None)
        self.hass.config_entries._entries[todo_entry.entry_id] = todo_entry
        assert await self.hass.config_entries.async_setup(todo_entry.entry_id)
        await self.hass.async_block_till_done()
        assert self.hass.states.get(MEMORY) is not None
        assert await async_setup_component(self.hass, 'persistent_notification', {})
        assert await async_setup_component(self.hass, 'system_log', {})
        self.sent = []

        async def record(call):
            self.sent.append(dict(call.data))
        self.hass.services.async_register('notify', 'mobile_app_example_phone', record)
        self._registries()
        target = path / 'blueprints/automation/fbonelle/surveillance_piles.yaml'
        target.parent.mkdir(parents=True)
        target.write_text(BP.read_text())
        self.config = load_yaml(str(EXAMPLES / 'automations.yaml'))
        self.config[0]['use_blueprint']['input'].update(overrides or {})
        # Keep the production time and time_pattern triggers, but drive their clock explicitly in tests.
        import homeassistant.components.homeassistant.triggers.time_pattern as pattern
        import homeassistant.components.homeassistant.triggers.time as fixed_time
        for module in [pattern, fixed_time]:
            self.patches.append(patch.object(module, 'async_track_time_change', lambda *a, **kw: lambda: None))
            self.patches[-1].start()
        assert await async_setup_component(self.hass, 'automation', {'automation': self.config})
        await self.hass.async_start()
        await self.hass.async_block_till_done()
        self.auto = self.hass.data['automation'].get_entity(AUTOMATION)
        assert self.auto
        return self

    def _entry(self, domain):
        entry = ConfigEntry(domain=domain, entry_id=f'entry_{domain}', title=domain, version=1, minor_version=1,
                            data={}, options={}, source='user', unique_id=f'entry_{domain}', discovery_keys={},
                            subentries_data=None, state=ConfigEntryState.LOADED)
        self.hass.config_entries._entries[entry.entry_id] = entry
        return entry

    def _registries(self):
        entities = er.async_get(self.hass)
        devices = dr.async_get(self.hass)
        labels = lr.async_get(self.hass)
        zha, mobile, icloud, nut = (self._entry(d) for d in ['zha', 'mobile_app', 'icloud', 'nut'])
        def device(entry, name, maker):
            return devices.async_get_or_create(config_entry_id=entry.entry_id, identifiers={(entry.domain, name)},
                                               name=name, manufacturer=maker, model='Fictional')
        def entity(entry, entity_id, dev=None, platform=None):
            domain, obj = entity_id.split('.', 1)
            created = entities.async_get_or_create(domain, platform or entry.domain, entity_id,
                                                   suggested_object_id=obj, config_entry=entry,
                                                   device_id=dev.id if dev else None)
            assert created.entity_id == entity_id
            return created
        remote = device(zha, 'Remote', 'IKEA of Sweden')
        smoke = device(zha, 'Smoke', 'HEIMAN')
        leak = device(zha, 'Leak', 'LUMI')
        spare = device(zha, 'Spare', 'SONOFF')
        phone = device(mobile, 'Phone', 'Google')
        watch = device(icloud, 'Watch', 'Apple')
        ups = device(nut, 'UPS', 'APC')
        entity(zha, 'sensor.remote_battery', remote)
        entity(zha, 'sensor.smoke_battery', smoke)
        entity(zha, 'binary_sensor.leak_battery_low', leak)
        entity(zha, 'sensor.spare_battery', spare)
        entity(mobile, 'sensor.phone_battery', phone)
        # Attached to the iCloud entry but published by another platform: integration_entities() misses it.
        entity(icloud, 'sensor.emma_phone_battery', None, platform='legacy_tracker')
        entity(zha, 'sensor.watch_battery', watch)
        entity(nut, 'sensor.ups_battery', ups)
        label = labels.async_create('Réserve')
        devices.async_update_device(spare.id, labels={label.label_id})
        self.label_id = label.label_id
        for e in ['sensor.remote_battery', 'sensor.smoke_battery', 'sensor.spare_battery', 'sensor.phone_battery',
                  'sensor.emma_phone_battery', 'sensor.watch_battery', 'sensor.ups_battery']:
            self.battery(e, 80)
        self.battery('binary_sensor.leak_battery_low', 'off')

    def battery(self, entity_id, value, age=0):
        name = entity_id.split('.', 1)[1].replace('_', ' ').capitalize()
        self.hass.states.async_set(entity_id, str(value), {'device_class': 'battery', 'friendly_name': name,
                                                          **({'unit_of_measurement': '%'} if entity_id.startswith('sensor.') else {})})
        state = self.hass.states.get(entity_id)
        stamp = self.now - timedelta(seconds=age)
        state.last_changed = state.last_updated = state.last_reported = stamp

    async def drain(self):
        for _ in range(30):
            await asyncio.sleep(0)
        await self.hass.async_block_till_done()

    async def run(self, trigger_id='scan', advance=300):
        self.now += timedelta(seconds=advance)
        variables = {} if trigger_id is None else {'trigger': {'id': trigger_id, 'platform': 'time'}}
        await self.auto.async_trigger(variables, skip_condition=True)
        await self.drain()

    async def items(self):
        response = await self.hass.services.async_call(
            'todo', 'get_items', {'entity_id': MEMORY, 'status': ['needs_action', 'completed']},
            blocking=True, return_response=True)
        return response[MEMORY]['items']

    async def todo(self, service, **data):
        await self.hass.services.async_call('todo', service, {'entity_id': MEMORY, **data}, blocking=True)
        await self.drain()

    def notice(self):
        from homeassistant.components.persistent_notification import DOMAIN
        return next((n for n in self.hass.data.get(DOMAIN, {}).values()
                     if n['notification_id'].startswith('battery_watch_')), None)

    async def close(self):
        await self.hass.async_stop()
        for p in reversed(self.patches):
            p.stop()


@pytest_asyncio.fixture
async def env(tmp_path):
    e = await BatteryEnv().setup(tmp_path)
    try:
        yield e
    finally:
        await e.close()


async def make(tmp_path, **kw):
    return await BatteryEnv().setup(tmp_path, **kw)


async def test_native_schema_and_example(env):
    bp = Blueprint(load_yaml(str(BP)), expected_domain='automation', schema=AUTOMATION_BLUEPRINT_SCHEMA)
    assert bp.name.startswith('Surveillance des piles et batteries — ')
    assert bp.name.endswith((ROOT / 'src/battery_watch/VERSION').read_text().strip())
    for example in load_yaml(str(EXAMPLES / 'automations.yaml')):
        args = BlueprintInputs(bp, example)
        args.validate()
        PLATFORM_SCHEMA(args.async_substitute())
    minimal = BlueprintInputs(bp, {'use_blueprint': {'path': 'x.yaml', 'input': {'memory': MEMORY}}})
    minimal.validate()
    defaults = minimal.async_substitute()
    assert defaults['variables']['threshold'] == 20
    assert defaults['variables']['excluded_integrations'] == ['mobile_app', 'icloud', 'icloud3', 'nut']
    assert defaults['variables']['excluded_manufacturers'] == ['Apple']


async def test_new_low_battery_is_reported_once_and_listed(env):
    await env.run()
    assert await env.items() == [] and env.sent == []
    env.battery('sensor.remote_battery', 18)
    await env.run()
    assert env.sent == [{'title': '🔋 Pile ou batterie à remplacer (1)', 'message': '• Remote battery — 18 %'}]
    items = await env.items()
    assert [(i['summary'], i['description'], i['status']) for i in items] == [
        ('Remote battery — 18 %', 'battery_watch:sensor.remote_battery', 'needs_action')]
    for level in [17, 15, 9]:
        env.battery('sensor.remote_battery', level)
        await env.run()
    assert len(env.sent) == 1
    assert [i['summary'] for i in await env.items()] == ['Remote battery — 9 %']


async def test_recovery_margin_and_replacement(env):
    await env.run()
    env.battery('sensor.remote_battery', 19)
    await env.run()
    env.battery('sensor.remote_battery', 22)
    await env.run()
    assert len(await env.items()) == 1, 'within the recovery margin the item is kept'
    env.battery('sensor.remote_battery', 19)
    await env.run()
    assert len(env.sent) == 1, 'oscillation around the threshold must not alert again'
    env.battery('sensor.remote_battery', 100)
    await env.run()
    assert await env.items() == [] and env.notice() is None
    env.battery('sensor.remote_battery', 10)
    await env.run()
    assert len(env.sent) == 2


async def test_checked_item_is_acknowledged_until_replacement(env):
    await env.run()
    env.battery('sensor.remote_battery', 10)
    env.battery('sensor.smoke_battery', 12)
    await env.run()
    assert len(env.sent) == 1 and env.notice()['title'] == 'Piles et batteries à vérifier (2)'
    remote = next(i for i in await env.items() if i['summary'].startswith('Remote'))
    await env.todo('update_item', item=remote['uid'], status='completed')
    # The state change of the list refreshes the persistent notification at once.
    await env.run('list', advance=0)
    assert env.notice()['title'] == 'Piles et batteries à vérifier (1)'
    assert 'Remote' not in env.notice()['message']
    env.battery('sensor.remote_battery', 6)
    await env.run()
    env.sent.clear()
    await env.run(None, advance=0)
    assert env.sent == [{'title': 'Piles et batteries à vérifier (1)', 'message': '• Smoke battery — 12 %'}]
    completed = [i for i in await env.items() if i['status'] == 'completed']
    assert [i['summary'] for i in completed] == ['Remote battery — 6 %']
    env.battery('sensor.remote_battery', 100)
    await env.run()
    env.battery('sensor.remote_battery', 8)
    await env.run()
    assert env.sent[-1]['message'] == '• Remote battery — 8 %', 'a replaced battery is reported again later'


async def test_manual_items_are_left_untouched(env):
    await env.todo('add_item', item='Acheter des piles AAA')
    env.battery('sensor.remote_battery', 10)
    await env.run()
    env.battery('sensor.remote_battery', 100)
    await env.run()
    assert [i['summary'] for i in await env.items()] == ['Acheter des piles AAA']


async def test_silent_device_after_delay_and_no_repeat_when_flapping(env):
    await env.run()
    env.battery('sensor.smoke_battery', 'unavailable', age=3600)
    await env.run(advance=0)
    assert env.sent == []
    env.battery('sensor.smoke_battery', 'unavailable', age=7 * 3600)
    await env.run(advance=0)
    assert env.sent[-1]['message'] == '• Smoke battery — muet depuis 7 h'
    # A restart makes the device unavailable again with a fresh timestamp: it stays listed.
    env.battery('sensor.smoke_battery', 'unavailable', age=0)
    await env.run()
    env.battery('sensor.smoke_battery', 'unknown')
    await env.run()
    env.battery('sensor.smoke_battery', 'unavailable', age=8 * 3600)
    await env.run(advance=0)
    assert len(env.sent) == 1 and len(await env.items()) == 1


async def test_binary_low_battery_alert(env):
    await env.run()
    env.battery('binary_sensor.leak_battery_low', 'on')
    await env.run()
    assert env.sent[-1]['message'] == '• Leak battery low — alerte pile faible'


async def test_binary_alerts_can_be_ignored(tmp_path):
    e = await make(tmp_path, overrides={'include_binary': False})
    try:
        await e.run()
        e.battery('binary_sensor.leak_battery_low', 'on')
        await e.run()
        assert e.sent == [] and await e.items() == []
    finally:
        await e.close()


async def test_personal_devices_and_ups_never_reported(env):
    await env.run()
    for entity_id in ['sensor.emma_phone_battery', 'sensor.watch_battery', 'sensor.ups_battery']:
        env.battery(entity_id, 'unavailable', age=48 * 3600)
    env.battery('sensor.phone_battery', 3)
    await env.run(advance=0)
    assert env.sent == [] and await env.items() == [] and env.notice() is None


async def test_labels_and_entities_exclusions(tmp_path):
    e = await make(tmp_path, overrides={'excluded_entities': ['sensor.smoke_battery'],
                                        'excluded_labels': ['reserve']})
    try:
        await e.run()
        e.battery('sensor.smoke_battery', 5)
        e.battery('sensor.spare_battery', 5)
        e.battery('sensor.remote_battery', 5)
        await e.run()
        assert [m['message'] for m in e.sent] == ['• Remote battery — 5 %']
    finally:
        await e.close()


async def test_summary_weekday_empty_and_manual_run(tmp_path):
    e = await make(tmp_path, overrides={'summary_weekdays': ['wed']})
    try:
        e.battery('sensor.remote_battery', 15)
        await e.run()
        e.battery('binary_sensor.leak_battery_low', 'on')
        await e.run()
        e.sent.clear()
        await e.run('summary', advance=0)
        assert e.sent == [{'title': 'Piles et batteries à vérifier (2)',
                           'message': '• Leak battery low — alerte pile faible\n• Remote battery — 15 %'}]
        e.now += timedelta(days=1)
        await e.run('summary', advance=0)
        assert len(e.sent) == 1, 'Thursday is not selected'
        await e.run(None, advance=0)
        assert len(e.sent) == 2, 'a manual run always sends the summary'
        e.battery('sensor.remote_battery', 90)
        e.battery('binary_sensor.leak_battery_low', 'off')
        await e.run()
        e.now += timedelta(days=6)
        await e.run('summary', advance=0)
        assert len(e.sent) == 2 and e.notice() is None
    finally:
        await e.close()


async def test_summary_when_empty(tmp_path):
    e = await make(tmp_path, overrides={'summary_when_empty': True})
    try:
        await e.run('summary', advance=0)
        assert e.sent == [{'title': 'Piles et batteries : rien à signaler',
                           'message': 'Aucune pile ni batterie à remplacer.'}]
    finally:
        await e.close()


async def test_missing_list_reports_configuration(tmp_path):
    e = await make(tmp_path, overrides={'memory': 'todo.absente'})
    try:
        e.battery('sensor.remote_battery', 5)
        await e.run()
        assert e.sent == [] and await e.items() == []
        assert 'Liste de tâches locale' in e.notice()['message']
    finally:
        await e.close()


async def test_notification_conditions_keep_memory_up_to_date(tmp_path):
    e = await make(tmp_path, overrides={'notification_conditions': [
        {'condition': 'template', 'value_template': '{{ false }}'}]})
    try:
        await e.run()
        e.battery('sensor.remote_battery', 5)
        await e.run()
        assert e.sent == [] and len(await e.items()) == 1
        assert 'Remote battery — 5 %' in e.notice()['message']
    finally:
        await e.close()


async def test_no_size_limit_and_no_repeat_with_many_devices(env):
    await env.run()
    for i in range(80):
        env.battery(f'sensor.extra_{i:02d}_battery', 5)
    await env.run()
    assert env.sent[-1]['title'] == '🔋 Pile ou batterie à remplacer (80)'
    assert len(await env.items()) == 80
    count = len(env.sent)
    await env.run()
    assert len(env.sent) == count
    assert env.notice()['title'] == 'Piles et batteries à vérifier (80)'


async def test_entity_without_registry_entry_is_watched(env):
    await env.run()
    env.battery('sensor.template_battery', 4)
    await env.run()
    assert env.sent[-1]['message'] == '• Template battery — 4 %'


async def test_summary_disabled_and_no_actions_configured(tmp_path):
    e = await make(tmp_path, overrides={'summary_enabled': False, 'alert_actions': [], 'summary_actions': []})
    try:
        e.battery('sensor.remote_battery', 5)
        await e.run()
        await e.run('summary', advance=0)
        assert e.sent == [] and 'Remote battery — 5 %' in e.notice()['message']
    finally:
        await e.close()
