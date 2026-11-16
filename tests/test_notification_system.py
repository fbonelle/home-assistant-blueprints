# SPDX-License-Identifier: GPL-3.0-only
"""Native Home Assistant 2026.10.4: the four notification blueprints running together.

Scripts and the relay automation are created from the published blueprints, exactly as in the
example package. Input helpers, persistent notifications, labels and the entity registry are the
real components. Only the outbound services (mobile app, ntfy, SMTP, speech, volume, scenes and
the logbook) are recording doubles; a double can be switched to fail like an unreachable provider.
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
from homeassistant.components.automation.config import AUTOMATION_BLUEPRINT_SCHEMA
from homeassistant.components.blueprint.models import Blueprint, BlueprintInputs
from homeassistant.components.blueprint.schemas import BLUEPRINT_SCHEMA
from homeassistant.config_entries import ConfigEntries
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity as entity_helper
from homeassistant.helpers import entity_registry as er, label_registry as lr
from homeassistant.setup import async_setup_component
from homeassistant.util import dt as dt_util
from homeassistant.util.yaml import load_yaml

ROOT = Path(__file__).resolve().parent.parent
SOURCES = {
    'script': ['envoi_canal.yaml', 'repartiteur.yaml', 'lecture_vocale.yaml'],
    'automation': ['relais_mobile.yaml'],
}
PACKAGE = ROOT / 'examples/notification_system/package.yaml'
DISPATCH = 'notify_dispatch_global'
OUTBOUND = {
    'notify': ['mobile_app_mon_telephone', 'famille'],
    'ntfy': ['publish'],
    'smtp': ['send_message'],
    'tts': ['speak'],
    'media_player': ['volume_set'],
    'scene': ['create', 'turn_on'],
    'logbook': ['log'],
}


class NotifyEnv:
    async def setup(self, path, sender=None, dispatcher=None, tts=None, relay=None, before_start=None):
        # Wednesday 11 November 2026, 10:00 in Paris: daytime, outside the night window.
        self.now = datetime(2026, 11, 11, 9, 0, tzinfo=UTC)
        self.hass = core.HomeAssistant(str(path))
        self.hass.config_entries = ConfigEntries(self.hass, {})
        self.hass.config.time_zone = 'Europe/Paris'
        await self.hass.config.async_set_time_zone('Europe/Paris')
        loader.async_setup(self.hass)
        assert await async_load_base_functionality(self.hass)
        self.patches = [
            patch.object(dt_util, 'now', lambda time_zone=None: self.now.astimezone(time_zone or dt_util.get_default_time_zone())),
            patch.object(dt_util, 'utcnow', lambda: self.now),
            patch.object(core, 'time', SimpleNamespace(time=lambda: self.now.timestamp())),
            patch.object(entity_helper, 'timer', lambda: self.now.timestamp()),
        ]
        for p in self.patches:
            p.start()
        # logger and system_log are always loaded by Home Assistant.
        for component in ['persistent_notification', 'system_log', 'logger', 'input_text', 'input_boolean']:
            config = {}
            if component == 'input_text':
                config = {'input_text': {'notify_dedup_slots': {'max': 255}}}
            if component == 'input_boolean':
                config = {'input_boolean': {'tts_muted': {}}}
            assert await async_setup_component(self.hass, component, config)
        self.calls = {f'{d}.{s}': [] for d, services in OUTBOUND.items() for s in services}
        self.failing = set()
        for domain, services in OUTBOUND.items():
            for service in services:
                self.hass.services.async_register(domain, service, self._recorder(f'{domain}.{service}'))
        self.hass.states.async_set('zone.home', '1')
        # The ntfy notify entity: 'unknown' until it has sent something, as in Home Assistant.
        self.hass.states.async_set('notify.ntfy_technique', 'unknown')
        self._speakers()
        for domain, files in SOURCES.items():
            target = path / 'blueprints' / domain / 'fbonelle/notification_system'
            target.mkdir(parents=True, exist_ok=True)
            for name in files:
                (target / name).write_text((ROOT / 'blueprints' / domain / 'notification_system' / name).read_text())
        package = load_yaml(str(PACKAGE))
        scripts = package['script']
        scripts['notify_send_channel']['use_blueprint']['input'].update(sender or {})
        scripts[DISPATCH]['use_blueprint']['input'].update(dispatcher or {})
        scripts['tts_engine']['use_blueprint']['input'].update(tts or {})
        automations = package['automation']
        automations[0]['use_blueprint']['input'].update(relay or {})
        self.package = package
        assert await async_setup_component(self.hass, 'script', {'script': scripts})
        if before_start:
            await before_start(self)
        assert await async_setup_component(self.hass, 'automation', {'automation': automations})
        await self.hass.async_start()
        await self.drain()
        for name in ['notify_send_channel', DISPATCH, 'tts_engine']:
            assert self.hass.states.get(f'script.{name}') is not None, name
        assert self.hass.states.get('automation.notifications_relais_vers_le_mobile') is not None
        return self

    def _recorder(self, name):
        async def record(call):
            self.calls[name].append(dict(call.data))
            if name in self.failing:
                raise HomeAssistantError(f'{name} unreachable')
        return record

    def _speakers(self):
        entities = er.async_get(self.hass)
        labels = lr.async_get(self.hass)
        label = labels.async_create('tts')
        self.label_id = label.label_id
        for obj, state in [('salon', 'idle'), ('cuisine', 'playing'), ('bureau', 'unavailable'), ('garage', 'idle')]:
            entry = entities.async_get_or_create('media_player', 'test', obj, suggested_object_id=obj)
            if obj != 'garage':
                entities.async_update_entity(entry.entity_id, labels={label.label_id})
            self.hass.states.async_set(entry.entity_id, state)

    async def drain(self):
        for _ in range(40):
            await asyncio.sleep(0)
        await self.hass.async_block_till_done()

    async def notify(self, advance=0, **data):
        self.now += timedelta(seconds=advance)
        await self.hass.services.async_call('script', DISPATCH, data, blocking=True)
        await self.drain()

    def notifications(self):
        from homeassistant.components.persistent_notification import DOMAIN
        return {n['notification_id']: n for n in self.hass.data.get(DOMAIN, {}).values()}

    def logs(self):
        from homeassistant.components.system_log import DOMAIN
        handler = self.hass.data[DOMAIN]
        return [' '.join(e.to_dict()['message']) for e in handler.records.values()]

    def sent(self, name):
        return self.calls[name]

    async def close(self):
        await self.hass.async_stop()
        for p in reversed(self.patches):
            p.stop()


@pytest_asyncio.fixture
async def env(tmp_path):
    e = await NotifyEnv().setup(tmp_path)
    try:
        yield e
    finally:
        await e.close()


async def make(tmp_path, **kw):
    return await NotifyEnv().setup(tmp_path, **kw)


async def test_blueprints_are_valid_and_versioned():
    version = (ROOT / 'src/notification_system/VERSION').read_text().strip()
    for domain, files in SOURCES.items():
        for name in files:
            data = load_yaml(str(ROOT / 'blueprints' / domain / 'notification_system' / name))
            bp = Blueprint(data, expected_domain=domain,
                           schema=AUTOMATION_BLUEPRINT_SCHEMA if domain == 'automation' else BLUEPRINT_SCHEMA)
            assert bp.name.endswith('— ' + version)
            assert bp.metadata['source_url'].endswith(f'/blueprints/{domain}/notification_system/{name}')
    relay = Blueprint(load_yaml(str(ROOT / 'blueprints/automation/notification_system/relais_mobile.yaml')),
                      expected_domain='automation', schema=AUTOMATION_BLUEPRINT_SCHEMA)
    minimal = BlueprintInputs(relay, {'use_blueprint': {'path': 'x.yaml', 'input': {'dispatcher_script': 'script.x'}}})
    minimal.validate()
    defaults = minimal.async_substitute()['variables']
    assert defaults['critical_markers'] == ['🚨', 'Urgence', 'Panne']
    assert defaults['dismissed_prefixes'] == [] and defaults['target'] == 'principal'


async def test_info_goes_to_mobile_only_with_a_trace(env):
    await env.notify(title='Lave-linge', message='Le cycle est terminé.')
    [push] = env.sent('notify.mobile_app_mon_telephone')
    assert push['title'] == 'Lave-linge' and push['message'] == 'Le cycle est terminé.'
    data = push['data']
    assert data['group'] == 'ha_info' and data['color'] == '#2196F3' and data['subtitle'] == 'ℹ️ INFO'
    assert data['push'] == {'sound': {'name': 'default'}} and 'priority' not in data
    assert data['url'] == data['clickAction'] == '/lovelace/0'
    assert data['tag'].startswith('sys_disp_') and data['tag'] in env.notifications()
    for name in ['notify.famille', 'ntfy.publish', 'smtp.send_message', 'tts.speak', 'logbook.log']:
        assert env.sent(name) == [], name


async def test_night_is_silent_and_target_all_uses_family(env):
    env.now = datetime(2026, 11, 11, 21, 30, tzinfo=UTC)  # 22:30 in Paris
    await env.notify(title='Porte', message='Ouverte', target='all')
    assert env.sent('notify.mobile_app_mon_telephone') == []
    [push] = env.sent('notify.famille')
    assert push['data']['push'] == {'sound': {'name': 'none'}}


async def test_family_falls_back_to_main_phone_when_not_configured(tmp_path):
    e = await make(tmp_path, sender={'family_service': ''})
    try:
        await e.notify(title='Courrier', message='Arrivé', target='all')
        assert len(e.sent('notify.mobile_app_mon_telephone')) == 1 and e.sent('notify.famille') == []
    finally:
        await e.close()


async def test_critical_pierces_silence_emails_and_speaks(env):
    env.now = datetime(2026, 11, 11, 23, 0, tzinfo=UTC)  # midnight: critical still speaks
    await env.notify(title='Fuite', message="Eau détectée dans la cave", level='critical',
                     entity_id='binary_sensor.fuite_cave')
    [push] = env.sent('notify.mobile_app_mon_telephone')
    data = push['data']
    assert data['push'] == {'sound': {'name': 'none', 'critical': 1, 'volume': 1.0}}
    assert data['priority'] == 'high' and data['ttl'] == 0 and data['channel'] == 'Alerte critique'
    assert data['url'] == '/history?entity_id=binary_sensor.fuite_cave' and data['color'] == '#D32F2F'
    [mail] = env.sent('smtp.send_message')
    assert mail['entity_id'] == ['notify.smtp_alertes'] and mail['title'] == '🚨 ALERTE : Fuite'
    assert 'href="https://ha.example.org/history?entity_id=binary_sensor.fuite_cave"' in mail['html']
    assert 'attachments' not in mail
    [log] = env.sent('logbook.log')
    assert log['name'] == 'Notification CRITICAL' and log['entity_id'] == f'script.{DISPATCH}'
    speakers = sorted(c['media_player_entity_id'] for c in env.sent('tts.speak'))
    assert speakers == ['media_player.cuisine', 'media_player.salon']
    assert env.sent('tts.speak')[0]['message'] == 'Fuite. Eau détectée dans la cave'
    assert sorted(c['entity_id'][0] for c in env.sent('media_player.volume_set')) == speakers
    assert all(c['volume_level'] == 0.8 for c in env.sent('media_player.volume_set'))
    [snapshot] = env.sent('scene.create')
    assert snapshot['scene_id'] == 'tts_restore_tts_engine' and sorted(snapshot['snapshot_entities']) == speakers
    await asyncio.sleep(len('Fuite. Eau détectée dans la cave') / 12 + 2.5)
    await env.drain()
    assert env.sent('scene.turn_on') == [{'entity_id': ['scene.tts_restore_tts_engine']}]


async def test_warning_speaks_by_day_only_when_someone_is_home(env):
    await env.notify(title='Fenêtre', message='Ouverte sous la pluie', level='warning')
    assert len(env.sent('tts.speak')) == 2 and env.sent('media_player.volume_set') == []
    env.hass.states.async_set('zone.home', '0')
    await env.notify(title='Fenêtre', message='Toujours ouverte', level='warning')
    assert len(env.sent('tts.speak')) == 2
    env.hass.states.async_set('zone.home', '2')
    env.now = datetime(2026, 11, 11, 21, 0, tzinfo=UTC)
    await env.notify(title='Fenêtre', message='Ouverte la nuit', level='warning')
    assert len(env.sent('tts.speak')) == 2
    await env.notify(title='Info', message='Forcée', tts=True)
    assert len(env.sent('tts.speak')) == 4


async def test_technical_goes_to_ntfy_with_app_link(env):
    await env.notify(title='🔧 Zigbee', message='Coordinateur relancé', level='technical',
                     data={'snapshot_file': '/config/www/snapshots/cam.jpg'})
    [publish] = env.sent('ntfy.publish')
    assert publish['entity_id'] == 'notify.ntfy_technique' and publish['tags'] == ['hammer_and_wrench', 'server']
    assert publish['click'] == 'homeassistant://navigate/config/logs' and publish['priority'] == 3
    assert publish['attach'] == 'https://ha.example.org/local/snapshots/cam.jpg'
    assert publish['icon'] == 'https://ha.example.org/static/icons/favicon-192x192.png'
    assert env.sent('notify.mobile_app_mon_telephone') == [] and env.sent('tts.speak') == []


async def test_ntfy_failure_falls_back_to_mobile(env):
    env.failing.add('ntfy.publish')
    await env.notify(title='Sauvegarde', message='Échec', level='technical')
    assert len(env.sent('ntfy.publish')) == 1
    [push] = env.sent('notify.mobile_app_mon_telephone')
    assert push['title'] == '🚨 FALLBACK NTFY : Sauvegarde' and push['data']['subtitle'] == '🔧 SYSTÈME'
    assert any('Échec ntfy' in line for line in env.logs())


@pytest.mark.parametrize('state', ['unavailable', None])
async def test_unavailable_ntfy_entity_falls_back_instead_of_losing_the_message(env, state):
    """Seen at start-up: Home Assistant drops a send to an unavailable entity with a mere warning."""
    if state is None:
        env.hass.states.async_remove('notify.ntfy_technique')
    else:
        env.hass.states.async_set('notify.ntfy_technique', state)
    await env.notify(title='Sauvegarde', message='Échec', level='technical')
    assert env.sent('ntfy.publish') == []
    [push] = env.sent('notify.mobile_app_mon_telephone')
    assert push['title'] == '🚨 FALLBACK NTFY : Sauvegarde'
    assert any('Échec ntfy' in line for line in env.logs())


async def test_no_fallback_when_disabled(tmp_path):
    e = await make(tmp_path, dispatcher={'ntfy_fallback': False})
    try:
        e.failing.add('ntfy.publish')
        await e.notify(title='Sauvegarde', message='Échec', level='technical')
        assert e.sent('notify.mobile_app_mon_telephone') == []
    finally:
        await e.close()


async def test_email_failure_is_logged_and_mobile_still_sent(env):
    env.failing.add('smtp.send_message')
    await env.notify(title='Incendie', message='Fumée', level='critical')
    assert len(env.sent('smtp.send_message')) == 1 and len(env.sent('notify.mobile_app_mon_telephone')) == 1
    assert any('Échec de l’e-mail' in line for line in env.logs())


async def test_email_attachment_forms(env):
    await env.notify(title='Sonnette', message='Visiteur', level='critical',
                     data={'snapshot_file': '/local/snapshots/porte.jpg', 'click': '/lovelace/camera'})
    [mail] = env.sent('smtp.send_message')
    assert mail['attachments'] == [{'media_source': {
        'media_content_id': 'media-source://media_source/local/snapshots/porte.jpg',
        'media_content_type': 'image/jpeg'}, 'filename': 'porte.jpg', 'content_id': 'snapshot'}]
    assert 'cid:snapshot' in mail['html'] and 'https://ha.example.org/lovelace/camera' in mail['html']
    [push] = env.sent('notify.mobile_app_mon_telephone')
    assert push['data']['image'] == 'https://ha.example.org/local/snapshots/porte.jpg'
    await env.notify(title='Sonnette', message='Visiteur distant', level='critical',
                     data={'snapshot_file': 'https://cam.example.org/a.png?x=1'})
    mail = env.sent('smtp.send_message')[-1]
    assert 'attachments' not in mail and 'src="https://cam.example.org/a.png?x=1"' in mail['html']


async def test_duplicates_are_dropped_inside_the_window(env, caplog):
    caplog.set_level(logging.INFO, logger='notification_system')
    await env.notify(title='Porte', message='Ouverte')
    await env.notify(advance=60, title='Porte', message='Ouverte')
    await env.notify(advance=60, title='Garage', message='Ouvert')
    await env.notify(advance=60, title='Porte', message='Ouverte')
    assert [c['title'] for c in env.sent('notify.mobile_app_mon_telephone')] == ['Porte', 'Garage']
    # Same text, higher level: an escalation is not a duplicate.
    await env.notify(title='Porte', message='Ouverte', level='warning')
    assert len(env.sent('notify.mobile_app_mon_telephone')) == 3
    # The window is fixed: 300 s after the first send, the message passes again.
    await env.notify(advance=200, title='Porte', message='Ouverte')
    assert len(env.sent('notify.mobile_app_mon_telephone')) == 4
    # A dropped duplicate is normal operation: logged at INFO, never as a warning.
    assert not any('Doublon écarté' in line for line in env.logs())
    assert any(r.name == 'notification_system' and r.levelno == logging.INFO and 'Doublon écarté' in r.getMessage()
               for r in caplog.records)
    assert logging.getLogger('notification_system').level == logging.INFO
    assert len(env.hass.states.get('input_text.notify_dedup_slots').state) <= 255


async def test_corrupt_memory_never_suppresses(env):
    await env.hass.services.async_call('input_text', 'set_value', {
        'entity_id': 'input_text.notify_dedup_slots', 'value': 'garbage|12:|:abc|x:y'}, blocking=True)
    await env.notify(title='Test', message='Passe')
    assert len(env.sent('notify.mobile_app_mon_telephone')) == 1


async def test_caller_notification_id_is_prefixed_once(env):
    await env.notify(title='A', message='1', data={'notif_id': 'lave_linge'})
    await env.notify(title='B', message='2', data={'notif_id': 'sys_disp_seche_linge'})
    tags = [c['data']['tag'] for c in env.sent('notify.mobile_app_mon_telephone')]
    assert tags == ['sys_disp_lave_linge', 'sys_disp_seche_linge']
    assert {'sys_disp_lave_linge', 'sys_disp_seche_linge'} <= set(env.notifications())


async def test_tts_mute_and_missing_speakers(tmp_path):
    e = await make(tmp_path)
    try:
        await e.hass.services.async_call('input_boolean', 'turn_on', {'entity_id': 'input_boolean.tts_muted'},
                                         blocking=True)
        await e.notify(title='Fuite', message='Cave', level='critical')
        await e.drain()
        assert e.sent('tts.speak') == []
    finally:
        await e.close()
    e = await make(tmp_path / 'b', tts={'speaker_label': 'absent'})
    try:
        await e.notify(title='Fuite', message='Cave', level='critical')
        await e.drain()
        assert e.sent('tts.speak') == [] and e.sent('scene.create') == []
        assert any('Aucune enceinte disponible' in line for line in e.logs())
    finally:
        await e.close()


async def create(env, notification_id, title, message='Détail'):
    await env.hass.services.async_call('persistent_notification', 'create', {
        'notification_id': notification_id, 'title': title, 'message': message}, blocking=True)
    await env.drain()


async def dismiss(env, notification_id):
    await env.hass.services.async_call('persistent_notification', 'dismiss',
                                       {'notification_id': notification_id}, blocking=True)
    await env.drain()


async def test_relay_levels_and_one_to_one_dismiss(env):
    await create(env, 'zha_reset', '⚠️ Alerte Zigbee')
    [push] = env.sent('notify.mobile_app_mon_telephone')
    assert push['title'] == '⚠️ Alerte Zigbee' and push['data']['tag'] == 'sys_disp_zha_reset'
    assert push['data']['group'] == 'ha_warning'
    # skip_trace: the relayed notification is not duplicated as sys_disp_zha_reset.
    assert set(env.notifications()) == {'zha_reset'}
    await dismiss(env, 'zha_reset')
    assert env.sent('notify.mobile_app_mon_telephone')[-1] == {
        'message': 'clear_notification', 'data': {'tag': 'sys_disp_zha_reset'}}
    for nid, title, level in [('a', '🚨 Panne chaudière', 'critical'), ('b', '📡 Réseau', 'technical'),
                              ('c', 'Mise à jour disponible', 'info')]:
        await create(env, nid, title)
    groups = [c['data'].get('group') for c in env.sent('notify.mobile_app_mon_telephone')[-2:]]
    assert groups == ['ha_critical', 'ha_info']
    assert [p['title'] for p in env.sent('ntfy.publish')] == ['📡 Réseau']


async def test_relay_never_loops_on_its_own_notifications(env):
    await env.notify(title='Lave-linge', message='Terminé')
    assert len(env.sent('notify.mobile_app_mon_telephone')) == 1
    await env.drain()
    assert len(env.sent('notify.mobile_app_mon_telephone')) == 1


async def test_relay_ignored_and_dismissed_prefixes(tmp_path):
    e = await make(tmp_path, relay={'ignored_prefixes': ['silencieux_'],
                                    'dismissed_prefixes': ['capfile_energy_manual_']})
    try:
        await create(e, 'silencieux_1', '⚠️ Alerte muette')
        assert e.sent('notify.mobile_app_mon_telephone') == [] and 'silencieux_1' in e.notifications()
        await create(e, 'capfile_energy_manual_01ABC', 'Capfile — Configurez le dashboard Énergie')
        assert 'capfile_energy_manual_01ABC' not in e.notifications()
        # Never sent, so nothing to clear on the phone either.
        assert e.sent('notify.mobile_app_mon_telephone') == []
    finally:
        await e.close()


async def test_relay_never_replays_notifications_present_at_startup(tmp_path):
    async def before(e):
        await create(e, 'autre_ancienne', '⚠️ Alerte ancienne')
    e = await make(tmp_path, before_start=before)
    try:
        assert 'autre_ancienne' in e.notifications() and e.sent('notify.mobile_app_mon_telephone') == []
    finally:
        await e.close()
