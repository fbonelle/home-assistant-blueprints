# SPDX-License-Identifier: GPL-3.0-only
"""Native Home Assistant 2026.10.4: the lighting blueprints with real lights and timers.

The automations are created from the published blueprints. Lights are real light entities
that record every command and update their state like a ZHA lamp does. Only the Zigbee
radio is simulated: remote presses are zha_event events with the payloads produced by the
zha-quirks profiles of the remotes in the house.
"""
import asyncio
import copy
import enum
from pathlib import Path

import pytest
import pytest_asyncio

from homeassistant import core, loader
from homeassistant.bootstrap import async_load_base_functionality
from homeassistant.components.blueprint.models import Blueprint, BlueprintInputs
from homeassistant.components.blueprint.schemas import BLUEPRINT_SCHEMA
from homeassistant.components.light import ColorMode, LightEntity, LightEntityFeature
from homeassistant.config_entries import ConfigEntries
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_state_change_event
from homeassistant.setup import async_setup_component
from homeassistant.util import color as color_util
from homeassistant.util import dt as dt_util
from homeassistant.util.yaml import load_yaml

ROOT = Path(__file__).resolve().parent.parent
FOLDER = ROOT / 'blueprints/automation/lighting'
REMOTES = ['telecommande_hue_dimmer.yaml', 'telecommande_hue_tap_dial.yaml',
           'telecommande_ikea_marche_arret.yaml', 'telecommande_ikea_5_boutons.yaml',
           'telecommande_ikea_styrbar.yaml', 'bouton_ewelink.yaml']
ALL = REMOTES + ['extinction_automatique.yaml']
REMOTE = 'a' * 32
OTHER = 'b' * 32


class Lamp(LightEntity):
    """A lamp that applies commands immediately, like ZHA's optimistic state."""

    _attr_should_poll = False

    def __init__(self, name, modes, kelvin=(2000, 6500), brightness=128, on=True, xy_error=0.0):
        self.entity_id = f'light.{name}'
        self._attr_name = name
        self._attr_unique_id = name
        self._attr_supported_color_modes = set(modes)
        self._attr_supported_features = LightEntityFeature.TRANSITION | LightEntityFeature.EFFECT
        self._attr_effect_list = ['off', 'colorloop']
        self._attr_effect = 'off'
        # Offset added to the reported colour, like a bulb that cannot render it exactly.
        self.xy_error = xy_error
        self._attr_min_color_temp_kelvin, self._attr_max_color_temp_kelvin = kelvin
        self._attr_is_on = on
        self._attr_brightness = brightness if ColorMode.ONOFF not in modes else None
        self._attr_color_mode = (ColorMode.XY if ColorMode.XY in modes else
                                 ColorMode.COLOR_TEMP if ColorMode.COLOR_TEMP in modes else
                                 ColorMode.ONOFF if ColorMode.ONOFF in modes else ColorMode.BRIGHTNESS)
        self._attr_xy_color = color_util.color_hs_to_xy(38, 53) if ColorMode.XY in modes else None
        self._attr_color_temp_kelvin = 3000 if ColorMode.COLOR_TEMP in modes else None
        self._attr_available = True
        self.calls = []

    async def async_turn_on(self, **kwargs):
        self.calls.append(('on', copy.deepcopy(kwargs)))
        self._attr_is_on = True
        if 'brightness' in kwargs and self._attr_brightness is not None:
            self._attr_brightness = kwargs['brightness']
        if 'rgb_color' in kwargs:
            kwargs = dict(kwargs, xy_color=color_util.color_RGB_to_xy(*kwargs['rgb_color']))
        if 'hs_color' in kwargs:
            kwargs = dict(kwargs, xy_color=color_util.color_hs_to_xy(*kwargs['hs_color']))
        if 'xy_color' in kwargs:
            x, y = kwargs['xy_color']
            self._attr_xy_color = (round(x + self.xy_error, 4), round(y + self.xy_error, 4))
            self._attr_color_mode = ColorMode.XY
        if 'effect' in kwargs:
            self._attr_effect = kwargs['effect']
        if 'color_temp_kelvin' in kwargs:
            self._attr_color_temp_kelvin = kwargs['color_temp_kelvin']
            self._attr_color_mode = ColorMode.COLOR_TEMP
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs):
        self.calls.append(('off', copy.deepcopy(kwargs)))
        self._attr_is_on = False
        self.async_write_ha_state()


class Env:
    async def setup(self, path, start=True):
        self.hass = core.HomeAssistant(str(path))
        self.hass.config_entries = ConfigEntries(self.hass, {})
        await self.hass.config.async_set_time_zone('Europe/Paris')
        loader.async_setup(self.hass)
        assert await async_load_base_functionality(self.hass)
        texts = {'memory': {'min': 0, 'max': 255}, 'short_memory': {'min': 0, 'max': 100}}
        for component, config in [('homeassistant', {}), ('system_log', {}), ('persistent_notification', {}),
                                  ('input_text', {'input_text': texts}),
                                  ('input_boolean', {'input_boolean': {'flag': {}}}),
                                  ('timer', {'timer': {'corridor': {'duration': 180}}}), ('light', {})]:
            assert await async_setup_component(self.hass, component, config)
        self.lamps = {
            'color': Lamp('color', [ColorMode.XY, ColorMode.COLOR_TEMP], (1801, 6535)),
            'xy': Lamp('xy', [ColorMode.XY]),
            'white': Lamp('white', [ColorMode.COLOR_TEMP], (2202, 4000)),
            'plain': Lamp('plain', [ColorMode.BRIGHTNESS]),
            'stairs': Lamp('stairs', [ColorMode.ONOFF], on=False),
            'one': Lamp('one', [ColorMode.BRIGHTNESS], on=False),
            'two': Lamp('two', [ColorMode.BRIGHTNESS], on=False),
            'three': Lamp('three', [ColorMode.BRIGHTNESS], on=False),
        }
        await self.hass.data['light'].async_add_entities(list(self.lamps.values()))
        target = path / 'blueprints/automation/local'
        target.mkdir(parents=True)
        for name in ALL:
            (target / name).write_text((FOLDER / name).read_text())
        if start:
            await self.hass.async_start()
            await self.hass.async_block_till_done()
        return self

    async def automation(self, blueprint, **inputs):
        config = dict(id='under_test', alias='Under test',
                      use_blueprint=dict(path=f'local/{blueprint}', input=dict(inputs)))
        if 'automation' in self.hass.config.components:
            raise AssertionError('One automation per test environment')
        assert await async_setup_component(self.hass, 'automation', {'automation': [config]})
        await self.hass.async_block_till_done()
        if self.hass.is_running:
            assert self.hass.states.get('automation.under_test').state == 'on'
        for lamp in self.lamps.values():
            lamp.calls.clear()

    async def press(self, command, args=None, params=None, device=REMOTE, settle=.05, time_fired=None, **extra):
        self.hass.bus.async_fire('zha_event', dict(device_id=device, command=command,
                                                   args=[] if args is None else args,
                                                   params={} if params is None else params, **extra),
                                 time_fired=time_fired)
        await self.hass.async_block_till_done() if settle is None else await asyncio.sleep(settle)

    def state(self, name):
        return self.hass.states.get(f'light.{name}')

    def memory(self):
        import json
        raw = self.hass.states.get('input_text.memory').state
        return json.loads(raw[4:]) if raw.startswith('lr1:') else None

    def notification(self):
        from homeassistant.components.persistent_notification import _async_get_or_create_notifications
        notes = _async_get_or_create_notifications(self.hass)
        return ' '.join(n['title'] + ' ' + n['message'] for n in notes.values())

    def pct(self, name):
        state = self.state(name)
        return round(state.attributes['brightness'] / 2.55) if state.state == 'on' else 0


@pytest_asyncio.fixture
async def env(tmp_path):
    environment = await Env().setup(tmp_path)
    yield environment
    await environment.hass.async_stop(force=True)


# ---------------------------------------------------------------- schemas and defaults

@pytest.mark.parametrize('name', ALL)
def test_published_blueprints_pass_native_schema(name):
    data = load_yaml(str(FOLDER / name))
    BLUEPRINT_SCHEMA(data)
    blueprint = Blueprint(data, expected_domain='automation', schema=BLUEPRINT_SCHEMA)
    assert blueprint.metadata['homeassistant']['min_version'] == '2026.10.0'
    version = (ROOT / 'src/lighting/VERSION').read_text().strip()
    assert blueprint.metadata['name'].endswith(f'— {version}')
    assert blueprint.metadata['source_url'].endswith(name)


@pytest.mark.parametrize('name', REMOTES)
def test_every_default_action_exists_and_holds_only_on_holds(name):
    inputs = Blueprint(load_yaml(str(FOLDER / name)), expected_domain='automation',
                       schema=BLUEPRINT_SCHEMA).inputs
    choices = {k: v for k, v in inputs.items() if k.endswith('_action')}
    assert choices
    for key, spec in choices.items():
        options = [o['value'] for o in spec['selector']['select']['options']]
        assert spec['default'] in options
        holds = [o for o in options if o.endswith('_hold')]
        assert bool(holds) == key.endswith('_hold_action'), key
        assert key.replace('_action', '_custom') in inputs
    labels = {o['value']: o['label'] for spec in choices.values() for o in spec['selector']['select']['options']}
    engine = load_yaml(str(ROOT / 'src/lighting/engine.yaml'))
    assert all(set(row) <= {'value', 'label', 'hold_only'} for row in engine['actions_catalog'])
    assert labels['toggle_level'] == "Basculer, en allumant au niveau d'allumage"
    assert len(set(labels.values())) == len(labels)
    palette = inputs['palette']
    if name == 'telecommande_ikea_styrbar.yaml':
        assert len(palette['default']) == 16 and palette['default'][0] == 'ha_warm'
    else:
        assert len(palette['default']) == 21 and palette['default'][0] == 'default'
    assert len(palette['selector']['select']['options']) == 44


def test_examples_reference_published_blueprints_and_valid_actions():
    examples = load_yaml(str(ROOT / 'examples/lighting/automations.yaml'))
    assert len(examples) == 9
    ids = [e['id'] for e in examples]
    assert len(ids) == len(set(ids))
    for example in examples:
        path = example['use_blueprint']['path']
        assert path.startswith('fbonelle/')
        blueprint = Blueprint(load_yaml(str(FOLDER / path.split('/')[-1])), expected_domain='automation',
                              schema=BLUEPRINT_SCHEMA)
        BlueprintInputs(blueprint, example).validate()
        for key, value in example['use_blueprint']['input'].items():
            assert key in blueprint.inputs, (example['id'], key)
            if key.endswith('_action'):
                options = [o['value'] for o in blueprint.inputs[key]['selector']['select']['options']]
                assert value in options, (example['id'], key, value)


# ---------------------------------------------------------------- Philips Hue Dimmer

async def test_hue_dimmer_buttons_and_release_noise(env):
    await env.automation('telecommande_hue_dimmer.yaml', remote=REMOTE, light='light.plain')
    await env.press('on_press', settle=None)
    assert env.state('plain').state == 'off'
    # The short release that follows every press is ignored and never re-runs the toggle.
    await env.press('on_short_release', settle=None)
    assert env.state('plain').state == 'off'
    await env.press('up_press', settle=None)
    assert env.pct('plain') == 10, 'Plus on an off lamp switches it on at one step'
    await env.press('up_press', settle=None)
    assert env.pct('plain') == 20
    await env.press('off_press', settle=None)
    assert env.pct('plain') == 100
    await env.press('down_press', settle=None)
    assert env.pct('plain') == 90


async def test_hue_hold_is_one_step_per_repeated_event(env):
    await env.automation('telecommande_hue_dimmer.yaml', remote=REMOTE, light='light.plain')
    for _ in range(3):
        await env.press('up_hold', settle=None)
    assert abs(env.pct('plain') - 80) <= 1, 'Three steps of 10 % from about 50 %'
    assert len(env.lamps['plain'].calls) == 3
    await env.press('up_long_release', settle=None)
    await asyncio.sleep(.6)
    assert len(env.lamps['plain'].calls) == 3


async def test_dimming_stops_at_minimum_and_never_switches_off(env):
    await env.automation('telecommande_hue_dimmer.yaml', remote=REMOTE, light='light.plain', min_pct=5)
    for _ in range(15):
        await env.press('down_press', settle=None)
    assert env.state('plain').state == 'on'
    assert env.pct('plain') == 5
    calls = len(env.lamps['plain'].calls)
    await env.press('down_press', settle=None)
    assert len(env.lamps['plain'].calls) == calls, 'No command once the minimum is reached'


async def test_down_on_off_lamp_does_nothing(env):
    await env.automation('telecommande_hue_dimmer.yaml', remote=REMOTE, light='light.stairs')
    await env.press('down_press', settle=None)
    assert env.lamps['stairs'].calls == []


async def test_other_remote_and_unknown_events_are_ignored(env):
    await env.automation('telecommande_hue_dimmer.yaml', remote=REMOTE, light='light.plain')
    await env.press('on_press', device=OTHER, settle=None)
    await env.press('attribute_updated', args={'attribute_id': 0, 'value': False}, settle=None)
    await env.press('recall', args=[1, 0], settle=None)
    assert env.lamps['plain'].calls == []


async def test_unavailable_lamp_receives_nothing(env):
    await env.automation('telecommande_hue_dimmer.yaml', remote=REMOTE, light='light.plain')
    env.lamps['plain']._attr_available = False
    env.lamps['plain'].async_write_ha_state()
    await env.press('on_press', settle=None)
    assert env.lamps['plain'].calls == []


async def test_custom_action_receives_gesture(env):
    await env.automation('telecommande_hue_dimmer.yaml', remote=REMOTE, light='light.plain',
                         hue_hold_action='custom',
                         hue_hold_custom=[{'action': 'input_boolean.turn_on', 'target': {'entity_id': 'input_boolean.flag'}},
                                          {'event': 'custom_seen', 'event_data': {'gesture': '{{ gesture }}'}}])
    seen = []
    env.hass.bus.async_listen('custom_seen', lambda event: seen.append(event.data['gesture']))
    await env.press('off_hold', settle=None)
    assert env.hass.states.get('input_boolean.flag').state == 'on'
    assert seen == ['hue_hold']
    assert env.lamps['plain'].calls == []


async def test_unknown_action_value_is_treated_as_none(env):
    await env.automation('telecommande_hue_dimmer.yaml', remote=REMOTE, light='light.plain',
                         power_press_action='explode')
    await env.press('on_press', settle=None)
    assert env.lamps['plain'].calls == []


# ---------------------------------------------------------------- IKEA 5 buttons

async def test_ikea_5_buttons_center_and_steps(env):
    await env.automation('telecommande_ikea_5_boutons.yaml', remote=REMOTE, light='light.color')
    await env.press('toggle', settle=None)
    assert env.state('color').state == 'off'
    await env.press('step_with_on_off', params={'step_mode': 0}, settle=None)
    assert env.pct('color') == 20
    await env.press('step', params={'step_mode': 1}, settle=None)
    assert env.pct('color') == 1 and env.state('color').state == 'on'
    # Recent firmware: long press on the centre is « release » with a zero first parameter.
    await env.press('release', args=[0], params={'param1': 0}, settle=None)
    state = env.state('color')
    assert env.pct('color') == 100
    hue, saturation = state.attributes['hs_color']
    assert abs(hue - 38) < 1.5 and abs(saturation - 53) < 1.5
    assert env.lamps['color'].calls[-1][1]['transition'] == .5


async def test_ikea_old_firmware_center_hold(env):
    await env.automation('telecommande_ikea_5_boutons.yaml', remote=REMOTE, light='light.plain')
    await env.press('move_to_level_with_on_off', args=[254, 0], settle=None)
    assert env.pct('plain') == 100


async def test_presets_follow_each_lamp_colour(env):
    await env.automation('telecommande_ikea_5_boutons.yaml', remote=REMOTE, light='light.color')
    # The lamp shows « Ambre chaud » (index 13): next is « Rose pâle », previous is « Pêche ».
    await env.lamps['color'].async_turn_on(hs_color=(28.308, 76.471))
    await env.press('press', args=[256, 13, 0], params={'param1': 256, 'param2': 13, 'param3': 0}, settle=None)
    assert env.lamps['color'].calls[-1][1]['xy_color'] == pytest.approx(color_util.color_hs_to_xy(316.957, 18.039), abs=1e-3)
    await env.press('press', args=[257, 13, 0], settle=None)
    await env.press('press', args=[257, 13, 0], settle=None)
    assert env.lamps['color'].calls[-1][1]['xy_color'] == pytest.approx(color_util.color_hs_to_xy(16.897, 68.235), abs=1e-3)


async def test_preset_from_off_lamp_starts_at_first_and_wraps(env):
    await env.automation('telecommande_ikea_5_boutons.yaml', remote=REMOTE, light='light.xy',
                         palette=['blue', 'lime'])
    await env.lamps['xy'].async_turn_off()
    await env.press('press', args=[256, 13, 0], settle=None)
    assert env.state('xy').state == 'on'
    assert env.lamps['xy'].calls[-1][1]['xy_color'] == pytest.approx(color_util.color_hs_to_xy(247.559, 49.804), abs=1e-3)
    await env.press('press', args=[256, 13, 0], settle=None)
    await env.press('press', args=[256, 13, 0], settle=None)
    assert env.lamps['xy'].calls[-1][1]['xy_color'] == pytest.approx(color_util.color_hs_to_xy(247.559, 49.804), abs=1e-3)


async def test_hold_loop_is_bounded_and_stopped_by_release(env):
    await env.automation('telecommande_ikea_5_boutons.yaml', remote=REMOTE, light='light.plain',
                         hold_interval=0.2, hold_step_pct=2, hold_limit=2)
    await env.press('move_with_on_off', params={'move_mode': 0}, settle=.5)
    # Noise from the same remote never interrupts the hold.
    await env.press('attribute_updated', args={'attribute_id': 0, 'value': True}, settle=.3)
    running = len(env.lamps['plain'].calls)
    assert running >= 3
    await env.press('stop_with_on_off', settle=.6)
    stopped = len(env.lamps['plain'].calls)
    assert stopped <= running + 1
    await asyncio.sleep(.5)
    assert len(env.lamps['plain'].calls) == stopped
    assert env.lamps['plain'].calls[-1][1]['transition'] == .2


async def test_lost_release_ends_at_hold_limit(env):
    await env.automation('telecommande_ikea_5_boutons.yaml', remote=REMOTE, light='light.plain',
                         hold_interval=0.2, hold_step_pct=1, hold_limit=2)
    await env.press('move', params={'move_mode': 1}, settle=2.6)
    calls = len(env.lamps['plain'].calls)
    assert 8 <= calls <= 10
    await asyncio.sleep(.6)
    assert len(env.lamps['plain'].calls) == calls


async def test_hold_stops_at_full_brightness(env):
    await env.automation('telecommande_ikea_5_boutons.yaml', remote=REMOTE, light='light.plain',
                         hold_interval=0.2, hold_step_pct=30, hold_limit=10)
    await env.press('move_with_on_off', settle=1.5)
    assert env.pct('plain') == 100
    assert len(env.lamps['plain'].calls) == 2
    assert env.hass.states.get('automation.under_test').attributes['current'] == 0


async def test_lateral_hold_cycles_presets(env):
    await env.automation('telecommande_ikea_5_boutons.yaml', remote=REMOTE, light='light.color',
                         preset_hold_interval=0.2, hold_limit=2, palette=['blue', 'lime', 'yellow'])
    await env.lamps['color'].async_turn_on(hs_color=(247.559, 49.804))
    env.lamps['color'].calls.clear()
    await env.press('hold', args=[3328, 0], params={'param1': 3328, 'param2': 0}, settle=.5)
    await env.press('release', args=[5], params={'param1': 5}, settle=.3)
    expected = [color_util.color_hs_to_xy(*hs) for hs in [(75.821, 78.824), (65.647, 66.667), (247.559, 49.804)]]
    got = [call[1]['xy_color'] for call in env.lamps['color'].calls]
    assert got == [pytest.approx(x, abs=1e-3) for x in expected[:len(got)]]
    assert 2 <= len(got) <= 3


async def test_white_lamp_temperature_is_bounded_in_kelvin(env):
    await env.automation('telecommande_ikea_5_boutons.yaml', remote=REMOTE, light='light.white',
                         left_press_action='warmer', right_press_action='cooler', kelvin_step=500)
    await env.press('press', args=[256, 13, 0], settle=None)
    assert env.state('white').attributes['color_temp_kelvin'] == 3500
    await env.press('press', args=[256, 13, 0], settle=None)
    await env.press('press', args=[256, 13, 0], settle=None)
    assert env.state('white').attributes['color_temp_kelvin'] == 4000
    calls = len(env.lamps['white'].calls)
    await env.press('press', args=[256, 13, 0], settle=None)
    assert len(env.lamps['white'].calls) == calls, 'No command at the coldest white'
    await env.press('press', args=[257, 13, 0], settle=None)
    assert env.state('white').attributes['color_temp_kelvin'] == 3500
    # Reference colour of a white-only lamp: reference white bounded to the lamp range.
    await env.press('release', args=[0], settle=None)
    assert env.state('white').attributes['color_temp_kelvin'] == 2500
    assert env.pct('white') == 100


# ---------------------------------------------------------------- IKEA on/off switch

async def test_ikea_on_off_switch(env):
    await env.automation('telecommande_ikea_marche_arret.yaml', remote=REMOTE, light='light.plain',
                         hold_interval=0.2, hold_limit=2)
    await env.press('off', cluster_id=6, endpoint_id=1, settle=None)
    assert env.state('plain').state == 'off'
    assert env.lamps['plain'].calls[-1] == ('off', {'transition': 1})
    await env.press('on', cluster_id=6, endpoint_id=1, settle=None)
    assert env.state('plain').state == 'on'
    await env.press('move_with_on_off', params={'move_mode': 0}, settle=.5)
    assert env.pct('plain') >= 70
    await env.press('stop', settle=.4)
    level = env.pct('plain')
    await asyncio.sleep(.5)
    assert env.pct('plain') == level


# ---------------------------------------------------------------- eWeLink button

async def test_ewelink_single_and_double_click(env):
    await env.automation('bouton_ewelink.yaml', remote=REMOTE, light='light.plain')
    await env.press('toggle', settle=None)
    assert env.state('plain').state == 'off'
    await env.press('toggle', settle=None)
    assert env.pct('plain') == 25
    await env.press('on', settle=None)
    assert env.pct('plain') == 100
    await env.press('on', settle=None)
    assert env.pct('plain') == 25
    await env.lamps['plain'].async_turn_off()
    await env.press('on', settle=None)
    assert env.pct('plain') == 25


async def test_ewelink_state_reports_never_switch_the_garden(env):
    await env.automation('bouton_ewelink.yaml', remote=REMOTE, light='light.plain')
    for value in [False, 1, True, 0]:
        await env.press('attribute_updated', args={'attribute_id': 0, 'attribute_name': 'on_off', 'value': value},
                        cluster_id=6, settle=None)
    await env.press('off', settle=None)  # Long press: no action by default.
    assert env.lamps['plain'].calls == []


# ---------------------------------------------------------------- Philips Hue Tap Dial

async def test_tap_dial_buttons_and_duplicate_scene_events(env):
    await env.automation('telecommande_hue_tap_dial.yaml', remote=REMOTE, light_1='light.one',
                         light_2='light.two', light_3='light.three')
    await env.press('button_2_press', args={'button': 'button_2', 'press_type': 'press'}, cluster_id=64512, settle=None)
    await env.press('recall', args=[40057, 0], params={'group_id': 40057, 'scene_id': 0}, cluster_id=5, settle=None)
    await env.press('button_2_short_release', settle=None)
    assert env.state('two').state == 'on'
    assert [len(env.lamps[n].calls) for n in ['one', 'two', 'three']] == [0, 1, 0]
    # Button 4 has no lamp: nothing happens and nothing fails.
    await env.press('button_4_press', settle=None)
    assert all(env.state(n).state == 'off' for n in ['one', 'three'])


async def test_tap_dial_rotation_follows_last_lamp_switched_on(env):
    await env.automation('telecommande_hue_tap_dial.yaml', remote=REMOTE, light_1='light.one',
                         light_2='light.two', light_3='light.three', dial_scale=1)
    # Real gestures are at least 0.15 s apart; closer ones are radio duplicates (filtered).
    await env.press('button_1_press', settle=.15)
    await env.press('button_3_press', settle=.15)
    before = env.pct('three')
    # step_size is in brightness units (0-255): 51 is 20 %.
    await env.press('step_with_on_off', params={'step_mode': 'StepMode.Up', 'step_size': 51, 'transition_time': 4},
                    cluster_id=8, settle=.15)
    assert env.pct('three') == before + 20
    assert env.lamps['three'].calls[-1][1]['transition'] == 1
    await env.press('step_with_on_off', params={'step_mode': 1, 'step_size': 26}, settle=.15)
    assert abs(env.pct('three') - (before + 10)) <= 1
    # Lamp three switched off: the dial goes back to lamp one, still on.
    await env.press('button_3_press', settle=.15)
    level = env.pct('one')
    await env.press('step_with_on_off', params={'step_mode': 0, 'step_size': 51}, settle=.15)
    assert env.pct('one') == level + 20
    assert env.state('three').state == 'off'


async def test_tap_dial_with_all_lamps_off_wakes_last_used(env):
    await env.automation('telecommande_hue_tap_dial.yaml', remote=REMOTE, light_1='light.one',
                         light_2='light.two')
    await env.press('button_2_press', settle=.15)
    await env.press('button_2_press', settle=.15)
    await env.press('step_with_on_off', params={'step_mode': 0, 'step_size': 51}, settle=.15)
    assert env.pct('two') == 20 and env.state('one').state == 'off'


# ---------------------------------------------------------------- Automatic switch-off

async def test_auto_off_with_timer(env):
    await env.automation('extinction_automatique.yaml', entities=['light.stairs'], timer='timer.corridor')
    await env.lamps['stairs'].async_turn_on()
    await env.hass.async_block_till_done()
    timer = env.hass.states.get('timer.corridor')
    assert timer.state == 'active' and timer.attributes['duration'] == '0:03:00'
    await env.hass.services.async_call('timer', 'finish', {'entity_id': 'timer.corridor'}, blocking=True)
    await env.hass.async_block_till_done()
    assert env.state('stairs').state == 'off'


async def test_auto_off_manual_off_cancels_timer(env):
    await env.automation('extinction_automatique.yaml', entities=['light.stairs'], timer='timer.corridor')
    await env.lamps['stairs'].async_turn_on()
    await env.hass.async_block_till_done()
    await env.lamps['stairs'].async_turn_off()
    await env.hass.async_block_till_done()
    assert env.hass.states.get('timer.corridor').state == 'idle'


async def test_auto_off_ignores_other_timers(env):
    await env.automation('extinction_automatique.yaml', entities=['light.stairs'], timer='timer.corridor')
    await env.lamps['stairs'].async_turn_on()
    await env.hass.async_block_till_done()
    env.hass.bus.async_fire('timer.finished', {'entity_id': 'timer.other'})
    await env.hass.async_block_till_done()
    assert env.state('stairs').state == 'on'


async def test_auto_off_without_timer_and_partial_off(env):
    await env.automation('extinction_automatique.yaml', entities=['light.stairs', 'light.one'],
                         duration={'hours': 0, 'minutes': 0, 'seconds': 1})
    await env.lamps['stairs'].async_turn_on()
    await env.lamps['one'].async_turn_on()
    await asyncio.sleep(.3)
    # One lamp switched off while the other stays on: the wait goes on.
    await env.lamps['one'].async_turn_off()
    await asyncio.sleep(1.2)
    assert env.state('stairs').state == 'off'


async def test_auto_off_without_timer_manual_off_cancels(env):
    await env.automation('extinction_automatique.yaml', entities=['light.stairs'],
                         duration={'hours': 0, 'minutes': 0, 'seconds': 1})
    await env.lamps['stairs'].async_turn_on()
    await asyncio.sleep(.2)
    await env.lamps['stairs'].async_turn_off()
    await env.lamps['stairs'].async_turn_on()
    env.lamps['stairs'].calls.clear()
    await asyncio.sleep(.5)
    assert env.state('stairs').state == 'on', 'The wait restarted with the new switch-on'
    await asyncio.sleep(.8)
    assert env.state('stairs').state == 'off'


async def test_auto_off_start_rearms_forgotten_light(tmp_path):
    env = await Env().setup(tmp_path, start=False)
    try:
        await env.automation('extinction_automatique.yaml', entities=['light.stairs'], timer='timer.corridor')
        env.lamps['stairs']._attr_is_on = True
        env.lamps['stairs'].async_write_ha_state()
        await env.hass.async_start()
        await env.hass.async_block_till_done()
        assert env.hass.states.get('timer.corridor').state == 'active'
    finally:
        await env.hass.async_stop(force=True)



class ZigpyEnum(int, enum.Enum):
    """Built like zigpy's enum8 (an int mixed into enum.Enum, not an IntEnum).

    str() and format() give « StepMode.Down », repr() gives « <StepMode.Down: 1> ».
    """

    def __format__(self, format_spec):
        return int.__format__(self, format_spec) if format_spec else f'{type(self).__name__}.{self.name}'

    __str__ = __format__


class StepMode(ZigpyEnum):
    """Stand-in for zigpy's LevelControl.StepMode, as ZHA puts it in zha_event params."""
    Up = 0
    Down = 1


class MoveMode(ZigpyEnum):
    Up = 0
    Down = 1


async def test_tap_dial_reads_zigpy_enum_params(env):
    """Real Hue Tap Dial event: step_mode is an enum and options are None."""
    await env.automation('telecommande_hue_tap_dial.yaml', remote=REMOTE, light_1='light.one',
                         light_2='light.two')
    await env.press('button_2_press', settle=.15)
    before = env.pct('two')
    real = {'step_mode': StepMode.Down, 'step_size': 51, 'transition_time': 4,
            'options_mask': None, 'options_override': None}
    await env.press('step_with_on_off', params=real, cluster_id=8, settle=.15)
    assert env.pct('two') == before - 20
    await env.press('step_with_on_off', params=dict(real, step_mode=StepMode.Up, step_size=102), settle=.15)
    assert env.pct('two') == before + 20


async def test_ikea_reads_zigpy_enum_params(env):
    await env.automation('telecommande_ikea_5_boutons.yaml', remote=REMOTE, light='light.color',
                         palette=['blue', 'lime'])
    await env.press('press', args=[256, 13, 0],
                    params={'param1': 256, 'param2': 13, 'param3': 0, 'extra': MoveMode.Down}, settle=None)
    assert env.lamps['color'].calls[-1][1]['xy_color'] == pytest.approx(
        color_util.color_hs_to_xy(247.559, 49.804), abs=1e-3)


@pytest.mark.parametrize('name', REMOTES)
async def test_event_fields_render_as_plain_literals(env, name):
    """Home Assistant 2026.11 renders these variables to text before reading them back.

    zigpy enums print as « <StepMode.Down: 1> », which cannot be read back: the whole value
    would be lost. The text produced for args and params must therefore be a plain literal.
    """
    import ast
    from homeassistant.helpers.template import Template
    variables = load_yaml(str(FOLDER / name))['variables']
    data = {'command': 'step_with_on_off', 'args': [StepMode.Down, 32, 4],
            'params': {'step_mode': StepMode.Down, 'step_size': 32, 'transition_time': 4,
                       'options_mask': None, 'options_override': None, 'on_off': True, 'rate': 1.5}}

    class Event:
        pass
    event = Event()
    event.data = data
    context = {'trigger': {'event': event}}
    args = Template(variables['args'], env.hass).async_render(context, parse_result=False)
    params = Template(variables['params'], env.hass).async_render(context, parse_result=False)
    assert ast.literal_eval(args.strip()) == [1, 32, 4]
    assert ast.literal_eval(params.strip()) == {'step_mode': 1, 'step_size': 32, 'transition_time': 4,
                                                'options_mask': None, 'options_override': None,
                                                'on_off': True, 'rate': 1.5}
    hue_args = Template(variables['args'], env.hass).async_render(
        {'trigger': {'event': type('E', (), {'data': {'args': {'button': 'button_1', 'press_type': 'press',
                                                                'args': [1, 3145728]}}})()}}, parse_result=False)
    assert ast.literal_eval(hue_args.strip())['button'] == 'button_1'



async def test_tap_dial_drops_radio_duplicates(env):
    """Recorded on 15 November: button 2 received twice, 50 ms apart; then two rotation
    reports of opposite directions 5 ms apart."""
    await env.automation('telecommande_hue_tap_dial.yaml', remote=REMOTE, light_1='light.one',
                         light_2='light.two')
    await env.press('button_2_press', settle=.05)
    await env.press('button_2_press', settle=.15)
    assert env.state('two').state == 'on' and len(env.lamps['two'].calls) == 1
    await env.lamps['two'].async_turn_on(brightness=round(20 * 2.55))
    await asyncio.sleep(.15)
    await env.press('step_with_on_off', params={'step_mode': StepMode.Up, 'step_size': 111}, settle=.005)
    await env.press('step_with_on_off', params={'step_mode': StepMode.Down, 'step_size': 26}, settle=.15)
    assert env.pct('two') == round(20 + 111 / 2.55)


async def test_dial_amplitude_is_converted_to_percent(env):
    """Recorded range of the dial: 8 (slow notch) to 226 (fast spin)."""
    await env.automation('telecommande_hue_tap_dial.yaml', remote=REMOTE, light_1='light.one')
    await env.lamps['one'].async_turn_on(brightness=3)
    await asyncio.sleep(.15)
    await env.press('step_with_on_off', params={'step_mode': StepMode.Up, 'step_size': 8}, settle=.15)
    assert env.pct('one') == round(1.2 + 8 / 2.55)
    await env.press('step_with_on_off', params={'step_mode': StepMode.Up, 'step_size': 226}, settle=.15)
    assert env.pct('one') == 93



def follow(env, member, group):
    """Make `group` mirror `member` like a Zigbee group: same on/off state, written just
    after the member and with a context of its own (not the remote's)."""
    lamp = env.lamps[group]

    @callback
    def mirror(event):
        new = event.data['new_state']
        if new is None or (new.state == 'on') == lamp.is_on:
            return
        lamp._attr_is_on = new.state == 'on'
        lamp._context = None
        lamp.async_write_ha_state()
    return async_track_state_change_event(env.hass, [f'light.{member}'], mirror)


async def test_tap_dial_prefers_the_member_over_a_following_group(env):
    """Enzo's remote: button 2 drives a group, button 3 one of its members. Switching the
    member on switches the group state on just after; the dial must stay on the member."""
    await env.automation('telecommande_hue_tap_dial.yaml', remote=REMOTE, light_1='light.one',
                         light_2='light.two', light_3='light.three')
    follow(env, 'three', 'two')
    await env.press('button_3_press', settle=.15)
    assert env.state('two').state == 'on' and env.state('three').state == 'on'
    assert env.state('two').last_changed >= env.state('three').last_changed
    level = env.pct('three')
    calls = len(env.lamps['two'].calls)
    await env.press('step_with_on_off', params={'step_mode': StepMode.Up, 'step_size': 51}, settle=.15)
    assert env.pct('three') == level + 20 and len(env.lamps['two'].calls) == calls
    # Further notches stay on the member (its context is now the dial run's).
    await env.press('step_with_on_off', params={'step_mode': StepMode.Down, 'step_size': 26}, settle=.15)
    assert abs(env.pct('three') - (level + 10)) <= 1 and len(env.lamps['two'].calls) == calls


async def test_tap_dial_prefers_the_group_when_its_button_was_pressed(env):
    await env.automation('telecommande_hue_tap_dial.yaml', remote=REMOTE, light_1='light.one',
                         light_2='light.two', light_3='light.three')
    follow(env, 'two', 'three')
    await env.press('button_2_press', settle=.15)
    assert env.state('three').last_changed >= env.state('two').last_changed
    await env.press('step_with_on_off', params={'step_mode': StepMode.Up, 'step_size': 51}, settle=.15)
    assert len(env.lamps['two'].calls) == 2 and len(env.lamps['three'].calls) == 0


async def test_tap_dial_lamp_switched_on_later_elsewhere_comes_first(env):
    await env.automation('telecommande_hue_tap_dial.yaml', remote=REMOTE, light_1='light.one',
                         light_2='light.two')
    await env.press('button_1_press', settle=.15)
    # Lamp two switched on from the app, more than 2 s later.
    await asyncio.sleep(2.1)
    await env.hass.services.async_call('light', 'turn_on', {'entity_id': 'light.two', 'brightness_pct': 30},
                                       blocking=True)
    await env.press('step_with_on_off', params={'step_mode': StepMode.Up, 'step_size': 51}, settle=.15)
    assert env.pct('two') == 50


async def test_tap_dial_never_chooses_an_unavailable_lamp(env):
    await env.automation('telecommande_hue_tap_dial.yaml', remote=REMOTE, light_1='light.one',
                         light_2='light.two')
    await env.press('button_1_press', settle=.15)
    await env.press('button_1_press', settle=.15)
    assert env.state('one').state == 'off'
    # Lamp two drops off the network after lamp one was used: the dial wakes lamp one.
    env.lamps['two']._attr_available = False
    env.lamps['two'].async_write_ha_state()
    await env.press('step_with_on_off', params={'step_mode': StepMode.Up, 'step_size': 51}, settle=.15)
    assert env.pct('one') == 20 and len(env.lamps['two'].calls) == 0


async def test_tap_dial_ignores_unknown_direction(env):
    await env.automation('telecommande_hue_tap_dial.yaml', remote=REMOTE, light_1='light.one')
    await env.lamps['one'].async_turn_on(brightness=128)
    for mode in [None, 7, 'sideways']:
        await env.press('step_with_on_off', params={'step_mode': mode, 'step_size': 51}, settle=.15)
    await env.press('step_with_on_off', params={'step_size': 51}, settle=.15)
    assert len(env.lamps['one'].calls) == 1


async def test_debounce_without_memory_tolerates_late_bookkeeping(env):
    """The second report fired before the first run was recorded (Home Assistant busy)."""
    await env.automation('telecommande_hue_tap_dial.yaml', remote=REMOTE, light_1='light.one')
    await env.lamps['one'].async_turn_on(brightness=round(20 * 2.55))
    await asyncio.sleep(.15)
    # Both reports were radioed 50 ms ago, 5 ms apart; the first run is recorded only now.
    fired = dt_util.utcnow().timestamp() - .05
    await env.press('step_with_on_off', params={'step_mode': StepMode.Up, 'step_size': 51},
                    time_fired=fired, settle=.03)
    await env.press('step_with_on_off', params={'step_mode': StepMode.Down, 'step_size': 26},
                    time_fired=fired + .005, settle=.15)
    assert env.pct('one') == 40
