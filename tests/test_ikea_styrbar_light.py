# SPDX-License-Identifier: GPL-3.0-only
"""Real HA lights, input_text and queued automations. Only the Zigbee radio is simulated."""
import asyncio
import copy
import json
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
import pytest_asyncio

from homeassistant import core, loader
from homeassistant.bootstrap import async_load_base_functionality
from homeassistant.config_entries import ConfigEntries
from homeassistant.components.automation.config import AUTOMATION_BLUEPRINT_SCHEMA, PLATFORM_SCHEMA
from homeassistant.components.blueprint.models import Blueprint, BlueprintInputs
from homeassistant.components.light import LightEntity, ColorMode, LightEntityFeature
from homeassistant.components.input_text import CONFIG_SCHEMA as TEXT_SCHEMA
from homeassistant.exceptions import HomeAssistantError
from homeassistant.setup import async_setup_component
from homeassistant.helpers import entity as entity_helper
from homeassistant.util import color as color_util
from homeassistant.util import dt as dt_util
from homeassistant.util.yaml import load_yaml

ROOT = Path(__file__).resolve().parent.parent
BP = ROOT / 'blueprints/automation/ikea_styrbar_light/lampe_styrbar.yaml'

class RadioLight(LightEntity):
    _attr_supported_color_modes = {ColorMode.XY}
    _attr_color_mode = ColorMode.XY
    _attr_supported_features = LightEntityFeature.TRANSITION | LightEntityFeature.EFFECT
    _attr_effect_list = ['off','colorloop']
    _attr_effect = 'off'
    _attr_should_poll = False

    def __init__(self, index):
        self.entity_id = f'light.bedside_{index}'
        self._attr_name = f'Bedside {index}'
        self._attr_unique_id = f'bedside_{index}'
        self._attr_is_on = True
        self._attr_brightness = 128
        self._attr_xy_color = color_util.color_RGB_to_xy(255, 192, 140)
        self.calls = []
        self.gate = None
        self.fail = False
        self._attr_available = True

    async def async_turn_on(self, **kwargs):
        self.calls.append(('on', copy.deepcopy(kwargs)))
        if self.gate:
            await self.gate.wait()
        if self.fail:
            raise HomeAssistantError('Simulated radio timeout')
        self._attr_is_on = True
        self._attr_brightness = kwargs.get('brightness', self._attr_brightness)
        self._attr_xy_color = kwargs.get('xy_color', self._attr_xy_color)
        self._attr_effect = kwargs.get('effect', self._attr_effect)
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        self.calls.append(('off', kwargs))
        self._attr_is_on = False
        self.async_write_ha_state()

class BedsideEnv:
    async def setup(self, path, overrides=None):
        self.now = datetime.now(UTC).replace(microsecond=0) + timedelta(seconds=1)
        self.hass = core.HomeAssistant(str(path))
        self.hass.config_entries = ConfigEntries(self.hass, {})
        self.hass.config.time_zone = 'Europe/Paris'
        loader.async_setup(self.hass)
        assert await async_load_base_functionality(self.hass)
        self.patch_now = patch.object(dt_util, 'now', lambda time_zone=None: self.now.astimezone(time_zone or UTC))
        self.patch_utc = patch.object(dt_util, 'utcnow', lambda: self.now)
        self.patch_core = patch.object(core, 'time', SimpleNamespace(time=lambda: self.now.timestamp()))
        self.patch_entity = patch.object(entity_helper, 'timer', lambda: self.now.timestamp())
        self.patch_now.start(); self.patch_utc.start(); self.patch_core.start(); self.patch_entity.start()
        assert await async_setup_component(self.hass, 'input_text', {'input_text': {
            f'bedside_{i}': dict(min=0, max=255) for i in range(2)}})
        assert await async_setup_component(self.hass, 'system_log', {})
        assert await async_setup_component(self.hass, 'light', {})
        self.lights = [RadioLight(i) for i in range(2)]
        await self.hass.data['light'].async_add_entities(self.lights)
        target = path / 'blueprints/automation/local/lampe_styrbar.yaml'
        target.parent.mkdir(parents=True)
        target.write_text(BP.read_text())
        self.configs = [dict(id=f'bedside_{i}', alias=f'Bedside {i}', use_blueprint=dict(
            path='local/lampe_styrbar.yaml', input=dict(remote=str(i+1)*32,
            light=f'light.bedside_{i}', memory=f'input_text.bedside_{i}', **(overrides or {})))) for i in range(2)]
        # Keep the production time_pattern configuration, but control its clock explicitly in tests.
        import homeassistant.components.homeassistant.triggers.time_pattern as pattern
        self.patch_timer = patch.object(pattern, 'async_track_time_change', lambda *a, **kw: lambda: None)
        self.patch_timer.start()
        assert await async_setup_component(self.hass, 'automation', {'automation': self.configs})
        await self.hass.async_start()
        await self.hass.async_block_till_done()
        self.now += timedelta(seconds=2)
        self.autos = [self.hass.data['automation'].get_entity(f'automation.bedside_{i}') for i in range(2)]
        assert all(self.autos)
        return self

    async def drain(self):
        for _ in range(30):
            await asyncio.sleep(0)

    async def emit(self, command, args=None, index=0, advance=.1, **extra):
        self.now += timedelta(seconds=advance)
        self.hass.bus.async_fire('zha_event', dict(device_id=str(index+1)*32, command=command,
                                                args=[] if args is None else args, **extra), time_fired=self.now.timestamp())
        await self.drain()

    async def tick(self, advance=1, index=0):
        self.now += timedelta(seconds=advance)
        await self.autos[index].async_trigger({'trigger': {'id': 'tick'}}, skip_condition=False)
        await self.drain()

    def memory(self, index=0):
        raw = self.hass.states.get(f'input_text.bedside_{index}').state
        return json.loads(raw[4:]) if raw.startswith('sl1:') else None

    async def write(self, value, index=0):
        await self.hass.services.async_call('input_text', 'set_value',
            dict(entity_id=f'input_text.bedside_{index}', value=value), blocking=True)

    async def close(self):
        for light in self.lights:
            if light.gate:
                light.gate.set()
        await self.drain()
        await self.hass.async_stop()
        self.patch_timer.stop(); self.patch_entity.stop(); self.patch_core.stop(); self.patch_utc.stop(); self.patch_now.stop()

@pytest_asyncio.fixture
async def bedside(tmp_path):
    env = await BedsideEnv().setup(tmp_path)
    try:
        yield env
    finally:
        await env.close()

@pytest.mark.asyncio
async def test_native_schema_and_exact_reference_defaults(bedside):
    bp = Blueprint(load_yaml(str(BP)), expected_domain='automation', schema=AUTOMATION_BLUEPRINT_SCHEMA)
    args = BlueprintInputs(bp, {'use_blueprint': {'path':'local/test.yaml', 'input':dict(
        remote='a'*32, light='light.test', memory='input_text.test')}})
    args.validate()
    expanded = args.async_substitute()
    assert PLATFORM_SCHEMA(expanded)['mode'] == 'queued'
    assert expanded['variables']['default_color'] == [255,192,140]
    assert [expanded['variables']['catalog'][k]['rgb_color'] for k in ['ha_warm','ha_soft','ha_white']] == [
        [255,192,140],[255,228,206],[255,254,250]]

@pytest.mark.asyncio
async def test_published_examples_and_helpers_use_distinct_ids(bedside):
    bp=Blueprint(load_yaml(str(BP)),expected_domain='automation',schema=AUTOMATION_BLUEPRINT_SCHEMA)
    examples=load_yaml(str(ROOT/'examples/ikea_styrbar_light/automations.yaml'))
    helpers=TEXT_SCHEMA(load_yaml(str(ROOT/'examples/ikea_styrbar_light/helpers.yaml')))['input_text']
    assert len({a['use_blueprint']['input']['remote'] for a in examples})==2
    assert len({a['use_blueprint']['input']['memory'] for a in examples})==2
    for example in examples:
        args=BlueprintInputs(bp,example);args.validate();PLATFORM_SCHEMA(args.async_substitute())
        helper=helpers[example['use_blueprint']['input']['memory'].split('.')[1]]
        assert helper['min']==0 and helper['max']==255

@pytest.mark.asyncio
async def test_on_off_and_double_recall_preserves_brightness(bedside):
    env = bedside; lamp = env.lights[0]
    lamp._attr_xy_color = (.2,.1); lamp.async_write_ha_state()
    await env.emit('off')
    assert not lamp.is_on
    await env.emit('on')
    assert lamp.is_on and lamp.xy_color == (.2,.1)
    await env.emit('on', advance=.4)
    assert lamp.brightness == 128
    assert lamp.xy_color == color_util.color_RGB_to_xy(255,192,140)
    assert env.memory()['c'] == 'paired'

@pytest.mark.asyncio
async def test_right_hold_recalls_default_without_double_press(bedside):
    await bedside.emit('hold', [3328,0])
    assert bedside.lights[0].xy_color == color_util.color_RGB_to_xy(255,192,140)
    assert bedside.memory()['h'] == ''

@pytest.mark.asyncio
async def test_palette_and_recall_stop_active_colorloop(bedside):
    for command,args in [('press',[256,13,0]),('hold',[3328,0])]:
        bedside.lights[0]._attr_effect='colorloop';bedside.lights[0].async_write_ha_state()
        await bedside.emit(command,args)
        assert bedside.lights[0].effect=='off'

@pytest.mark.asyncio
async def test_hold_release_and_tick(bedside):
    await bedside.emit('move_with_on_off', [0,83])
    first = bedside.lights[0].brightness
    assert first > 128 and bedside.memory()['h'] == 'up'
    await bedside.tick()
    assert bedside.lights[0].brightness > first, (bedside.memory(), bedside.lights[0].calls, bedside.now)
    await bedside.emit('stop_with_on_off')
    count = len(bedside.lights[0].calls)
    await bedside.tick()
    assert len(bedside.lights[0].calls) == count and bedside.memory()['h'] == ''

@pytest.mark.asyncio
async def test_cycle_order_and_wrap(bedside):
    for expected in ['ha_soft','ha_white','ikea_amber']:
        await bedside.emit('press', [256,13,0])
        assert bedside.memory()['i'] == bedside.configs[0]['use_blueprint']['input'].get('palette',
            ['ha_warm','ha_soft','ha_white','ikea_amber']).index(expected)
    await bedside.emit('press', [257,13,0])
    assert bedside.memory()['i'] == 2

@pytest.mark.asyncio
async def test_missing_release_expires_and_does_not_replay(bedside):
    await bedside.emit('move_with_on_off',[0,83])
    count = len(bedside.lights[0].calls)
    await bedside.tick(advance=16)
    assert len(bedside.lights[0].calls) == count
    assert bedside.memory()['h'] == ''
    await bedside.tick(advance=100)
    assert len(bedside.lights[0].calls) == count

@pytest.mark.asyncio
async def test_repeated_hold_packets_do_not_accelerate_or_extend(bedside):
    await bedside.emit('move_with_on_off',[0,83])
    started = bedside.memory()['s']; count = len(bedside.lights[0].calls)
    for _ in range(20):
        await bedside.emit('move_with_on_off',[0,83],advance=.9)
    assert bedside.memory()['s'] == started
    assert len(bedside.lights[0].calls) == count
    await bedside.tick()
    assert bedside.memory()['h'] == ''

@pytest.mark.asyncio
async def test_direction_change_and_off_cancel_hold(bedside):
    await bedside.emit('move_with_on_off',[0,83])
    previous = bedside.lights[0].brightness
    await bedside.emit('move',['MoveMode.Down',83])
    assert bedside.lights[0].brightness < previous
    await bedside.emit('off')
    count = len(bedside.lights[0].calls)
    await bedside.tick()
    assert not bedside.lights[0].is_on and len(bedside.lights[0].calls) == count

@pytest.mark.asyncio
async def test_dim_down_does_not_wake_off_light(bedside):
    await bedside.emit('off')
    count = len(bedside.lights[0].calls)
    await bedside.emit('move',[1,83])
    await bedside.tick()
    assert len(bedside.lights[0].calls) == count and bedside.memory()['h'] == ''

@pytest.mark.asyncio
async def test_dim_up_from_off_starts_at_minimum(bedside):
    await bedside.emit('off')
    await bedside.emit('move_with_on_off',['MoveMode.Up',83])
    assert 1 <= bedside.lights[0].brightness <= 3

@pytest.mark.asyncio
async def test_external_off_cancels_hold_without_relighting(bedside):
    await bedside.emit('move_with_on_off',[0,83])
    await bedside.hass.services.async_call('light','turn_off',dict(entity_id='light.bedside_0'),blocking=True)
    count=len(bedside.lights[0].calls)
    await bedside.tick()
    assert not bedside.lights[0].is_on and bedside.memory()['h']==''
    assert len(bedside.lights[0].calls)==count

@pytest.mark.asyncio
async def test_slow_light_does_not_block_other_remote(bedside):
    bedside.lights[0].gate=asyncio.Event()
    await bedside.emit('on')
    await bedside.emit('off',index=1)
    assert len(bedside.lights[0].calls)==1
    assert not bedside.lights[1].is_on
    bedside.lights[0].gate.set();await bedside.drain()

@pytest.mark.asyncio
async def test_unavailable_cancels_hold_and_recovery_does_not_replay(bedside):
    await bedside.emit('move_with_on_off',[0,83])
    bedside.lights[0]._attr_available = False; bedside.lights[0].async_write_ha_state()
    count = len(bedside.lights[0].calls)
    await bedside.tick()
    assert bedside.memory()['h'] == ''
    bedside.lights[0]._attr_available = True; bedside.lights[0].async_write_ha_state()
    await bedside.tick()
    assert len(bedside.lights[0].calls) == count

@pytest.mark.asyncio
async def test_service_failure_disarms_before_call(bedside,caplog):
    bedside.lights[0].fail = True
    await bedside.emit('move_with_on_off',[0,83])
    assert bedside.memory()['h'] == ''
    count = len(bedside.lights[0].calls)
    await bedside.tick()
    assert len(bedside.lights[0].calls) == count
    assert 'Simulated radio timeout' in caplog.text

@pytest.mark.asyncio
async def test_external_color_change_resynchronizes_palette(bedside):
    await bedside.emit('press',[256,13,0])
    assert bedside.memory()['i'] == 1
    await bedside.hass.services.async_call('light','turn_on',dict(entity_id='light.bedside_0',xy_color=[.17,.05]),blocking=True)
    await bedside.emit('press',[256,13,0])
    assert tuple(bedside.lights[0].xy_color) == (.2,.1)

@pytest.mark.asyncio
async def test_independent_remotes_and_other_device_ignored(bedside):
    await bedside.emit('on')
    await bedside.emit('on',index=1,advance=.2)
    assert bedside.memory()['c'] == bedside.memory(1)['c'] == 'on'
    assert len(bedside.lights[0].calls) == len(bedside.lights[1].calls) == 1
    bedside.hass.bus.async_fire('zha_event',dict(device_id='f'*32,command='off',args=[]))
    await bedside.drain()
    assert bedside.lights[0].is_on and bedside.lights[1].is_on

@pytest.mark.asyncio
@pytest.mark.parametrize('value', ['garbage','sl1:{}','sl1:[]','sl1:null'])
async def test_corrupt_memory_stops_without_overwrite(bedside,value,caplog):
    await bedside.write(value)
    await bedside.emit('on')
    assert not bedside.lights[0].calls
    assert bedside.hass.states.get('input_text.bedside_0').state == value
    assert 'appartient' in caplog.text and 'Error rendering' not in caplog.text

@pytest.mark.asyncio
async def test_shared_memory_owner_mismatch_is_blocked(bedside,caplog):
    await bedside.emit('on')
    original = bedside.hass.states.get('input_text.bedside_0').state
    await bedside.write(original,index=1)
    await bedside.emit('off',index=1)
    assert not bedside.lights[1].calls
    assert bedside.hass.states.get('input_text.bedside_1').state == original
    assert 'appartient' in caplog.text

@pytest.mark.asyncio
async def test_duplicate_short_presses_filtered_but_real_double_kept(bedside):
    await bedside.emit('on')
    await bedside.emit('on',advance=.01)
    assert len(bedside.lights[0].calls) == 1
    await bedside.emit('on',advance=.4)
    assert len(bedside.lights[0].calls) == 2 and bedside.memory()['c'] == 'paired'

@pytest.mark.asyncio
async def test_late_second_on_is_not_double(bedside):
    await bedside.emit('on')
    await bedside.emit('on',advance=1)
    assert bedside.memory()['c'] == 'on'
    assert all('xy_color' not in data for _,data in bedside.lights[0].calls)

@pytest.mark.asyncio
async def test_unknown_events_do_not_cancel_hold(bedside):
    await bedside.emit('move_with_on_off',[0,83])
    await bedside.emit('battery_report',[50])
    await bedside.emit('press',[999,13,0])
    assert bedside.memory()['h'] == 'up'
    await bedside.tick()
    assert len(bedside.lights[0].calls) == 2

@pytest.mark.asyncio
async def test_reload_clears_gestures_without_changing_light(bedside):
    await bedside.emit('move_with_on_off',[0,83])
    count = len(bedside.lights[0].calls)
    bedside.hass.bus.async_fire('automation_reloaded')
    await bedside.drain()
    assert bedside.memory()['h'] == '' and bedside.memory()['t'] == 0
    await bedside.tick()
    assert len(bedside.lights[0].calls) == count

@pytest.mark.asyncio
async def test_disable_enable_does_not_resume_hold(bedside):
    await bedside.emit('move_with_on_off',[0,83])
    bedside.now += timedelta(seconds=1)
    await bedside.hass.services.async_call('automation','turn_off',dict(entity_id='automation.bedside_0'),blocking=True)
    bedside.now += timedelta(seconds=1)
    await bedside.hass.services.async_call('automation','turn_on',dict(entity_id='automation.bedside_0'),blocking=True)
    await bedside.drain()
    count = len(bedside.lights[0].calls)
    await bedside.tick()
    assert len(bedside.lights[0].calls) == count and bedside.memory()['h'] == '', (bedside.memory(), bedside.hass.states.get('automation.bedside_0'))

@pytest.mark.asyncio
async def test_clock_rollback_discards_old_hold(bedside):
    await bedside.emit('move_with_on_off',[0,83])
    bedside.now -= timedelta(seconds=120)
    await bedside.tick(advance=1)
    assert bedside.memory()['h'] == ''
    await bedside.emit('on')
    assert bedside.memory()['c'] == 'on'
    await bedside.emit('move_with_on_off',[0,83])
    assert bedside.memory()['h']=='up'

@pytest.mark.asyncio
async def test_slow_radio_serializes_calls_and_discards_stale_buttons(bedside):
    lamp=bedside.lights[0];lamp.gate=asyncio.Event()
    await bedside.emit('press',[256,13,0])
    await bedside.emit('press',[256,13,0])
    assert len(lamp.calls)==1
    bedside.now += timedelta(seconds=6)
    lamp.gate.set(); await bedside.drain()
    assert len(lamp.calls)==1
    assert bedside.memory()['h']==''

@pytest.mark.asyncio
async def test_palette_entire_cycle_and_memory_stays_under_255(bedside):
    expected=[1,2,*range(3,16),0]
    for index in expected:
        await bedside.emit('press',[256,13,0],advance=.15)
        assert bedside.memory()['i']==index
        assert len(bedside.hass.states.get('input_text.bedside_0').state)<=255
    await bedside.emit('press',[257,13,0])
    assert bedside.memory()['i']==15

@pytest.mark.asyncio
async def test_selector_bounds_and_custom_color(tmp_path):
    env=await BedsideEnv().setup(tmp_path,dict(min_brightness=20,max_brightness=40,default_color=[127,172,255],on_brightness=30))
    try:
        await env.emit('on')
        assert 75 <= env.lights[0].brightness <= 77
        await env.emit('hold',[3328,0])
        assert env.lights[0].xy_color==color_util.color_RGB_to_xy(127,172,255)
        assert 75 <= env.lights[0].brightness <= 77
        await env.emit('move_with_on_off',[0,83])
        await env.tick()
        assert env.lights[0].brightness<=102 and env.memory()['h']==''
        await env.emit('move',[1,83])
        await env.tick();await env.tick()
        assert env.lights[0].brightness>=51 and env.memory()['h']==''
    finally:
        await env.close()

@pytest.mark.asyncio
@pytest.mark.parametrize('overrides', [dict(palette=[]),dict(palette=['ha_warm','ha_warm']),
    dict(palette=['missing']),dict(palette=[{}]),dict(min_brightness=80,max_brightness=10),
    dict(default_color=[255,-1,0]),dict(default_color=[255,True,0]),dict(default_color=[0,0,0]),
    dict(dim_interval=0),dict(min_brightness='bad')])
async def test_bad_configuration_is_blocked(tmp_path,overrides,caplog):
    env=await BedsideEnv().setup(tmp_path,overrides)
    try:
        await env.emit('on')
        assert not env.lights[0].calls
        assert 'ikea_styrbar_light' in caplog.text
        assert 'Error rendering' not in caplog.text
    finally:
        await env.close()

@pytest.mark.asyncio
async def test_single_item_palette_and_off_options(tmp_path):
    env=await BedsideEnv().setup(tmp_path,dict(palette=['ikea_blue'],colors_turn_on=False,recall_turns_on=False))
    try:
        await env.emit('off'); count=len(env.lights[0].calls)
        await env.emit('press',[256,13,0]);await env.emit('hold',[3328,0])
        assert len(env.lights[0].calls)==count
        await env.emit('on');await env.emit('press',[256,13,0])
        assert env.memory()['i']==0 and tuple(env.lights[0].xy_color)==(.17,.05)
        await env.emit('press',[257,13,0])
        assert env.memory()['i']==0
    finally:
        await env.close()

@pytest.mark.asyncio
async def test_recall_fallback_can_be_moved_or_disabled(tmp_path):
    env=await BedsideEnv().setup(tmp_path,dict(recall_fallback='left_hold'))
    try:
        await env.emit('hold',[3328,0]);assert not env.lights[0].calls
        await env.emit('hold',[3329,0]);assert len(env.lights[0].calls)==1
        await env.emit('hold',[3329,0],advance=.3);assert len(env.lights[0].calls)==1
    finally:
        await env.close()

@pytest.mark.asyncio
@pytest.mark.parametrize('skip', [False,True])
async def test_manual_run_has_no_light_action_or_template_error(bedside,caplog,skip):
    await bedside.hass.services.async_call('automation','trigger',
        dict(entity_id='automation.bedside_0',skip_condition=skip),blocking=True)
    assert not bedside.lights[0].calls
    assert 'Error' not in caplog.text

@pytest.mark.asyncio
async def test_worst_memory_length_and_zero_duplicate_filter(tmp_path):
    env=await BedsideEnv().setup(tmp_path,dict(debounce_ms=0))
    try:
        env.now=env.now.replace(microsecond=123456)
        env.lights[0]._attr_xy_color=(.12345678901234567,.23456789012345678)
        env.lights[0].async_write_ha_state()
        await env.emit('move_with_on_off',[0,83])
        assert env.memory()['h']=='up'
        assert len(env.hass.states.get('input_text.bedside_0').state)<=255
        await env.tick();assert env.memory()['h']=='up'
        await env.emit('stop')
        await env.emit('on');await env.emit('on',advance=.001)
        assert env.memory()['c']=='paired'
    finally:
        await env.close()

@pytest.mark.asyncio
async def test_late_release_and_out_of_order_on(bedside):
    await bedside.emit('move_with_on_off',[0,83])
    before=bedside.memory();count=len(bedside.lights[0].calls)
    bedside.hass.bus.async_fire('zha_event',dict(device_id='1'*32,command='off',args=[]),
        time_fired=before['t']-.5)
    await bedside.drain()
    assert bedside.memory()==before and len(bedside.lights[0].calls)==count
    bedside.hass.bus.async_fire('zha_event',dict(device_id='1'*32,command='stop',args=[]),
        time_fired=before['t']+.2)
    bedside.now+=timedelta(seconds=6)
    await bedside.drain()
    assert bedside.memory()['h']==''

@pytest.mark.asyncio
async def test_all_23_presets_and_expiry_before_next_step(tmp_path):
    catalog=load_yaml(str(ROOT/'src/ikea_styrbar_light/palette.yaml'))
    env=await BedsideEnv().setup(tmp_path,dict(palette=list(catalog),dim_interval=5,hold_limit=2))
    try:
        for expected in [*range(1,23),0]:
            await env.emit('press',[256,13,0],advance=.15)
            assert env.memory()['i']==expected
        await env.emit('move_with_on_off',[0,83]); count=len(env.lights[0].calls)
        await env.tick(advance=3)
        assert env.memory()['h']=='' and len(env.lights[0].calls)==count
    finally:
        await env.close()
