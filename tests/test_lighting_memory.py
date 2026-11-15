# SPDX-License-Identifier: GPL-3.0-only
"""Native Home Assistant 2026.10.4: STYRBAR in the lighting family and the optional memory.

These tests replay the scenarios of the former STYRBAR suite against the shared engine:
double press, recall colour, bounded holds, release at the level actually reached,
repeated hold packets, radio duplicates, out-of-order events, palette position, invalid
or shared memory and the diagnostic. The same environment as tests/test_lighting.py is
used: real lights, a real input_text helper, simulated Zigbee events only.
"""
import asyncio
import json

import pytest
import pytest_asyncio

from homeassistant.components.blueprint.models import Blueprint
from homeassistant.components.blueprint.schemas import BLUEPRINT_SCHEMA
from homeassistant.util import color as color_util
from homeassistant.util import dt as dt_util
from homeassistant.util.yaml import load_yaml

from test_lighting import FOLDER, Env, REMOTE

STYRBAR = 'telecommande_ikea_styrbar.yaml'
RIGHT = dict(args=[256, 13, 0], params={'param1': 256, 'param2': 13, 'param3': 0})
LEFT = dict(args=[257, 13, 0], params={'param1': 257, 'param2': 13, 'param3': 0})
RIGHT_HOLD = dict(args=[3328, 0], params={'param1': 3328, 'param2': 0})
WARM = color_util.color_RGB_to_xy(255, 192, 140)


@pytest_asyncio.fixture
async def env(tmp_path):
    environment = await Env().setup(tmp_path)
    yield environment
    await environment.hass.async_stop(force=True)


def xy_of(call):
    value = call[1].get('xy_color')
    return list(value) if value is not None else None


# ---------------------------------------------------------------- defaults

def test_styrbar_defaults_match_the_former_blueprint():
    inputs = Blueprint(load_yaml(str(FOLDER / STYRBAR)), expected_domain='automation',
                       schema=BLUEPRINT_SCHEMA).inputs
    expected = dict(up_press_action='on', up_double_action='recall', up_hold_action='brighter_hold',
                    down_press_action='off', down_hold_action='dimmer_hold',
                    left_press_action='previous_preset', right_press_action='next_preset',
                    left_hold_action='previous_preset_hold', right_hold_action='next_preset_hold',
                    brightness_speed=35, hold_interval=0.3, preset_hold_interval=0.4, hold_limit=15,
                    color_transition=0.3, transition=0, debounce_ms=50, double_press_ms=800,
                    recall_color=[255, 192, 140], min_pct=1, max_pct=100, memory='')
    assert {k: inputs[k]['default'] for k in expected} == expected
    assert inputs['palette']['default'] == [
        'ha_warm', 'ha_soft', 'ha_white', 'ikea_amber', 'ikea_peach', 'ikea_dark_peach', 'ikea_dark_red',
        'ikea_pink', 'ikea_light_pink', 'ikea_dark_pink', 'ikea_light_purple', 'ikea_dark_purple',
        'ikea_blue', 'ikea_light_blue', 'ikea_lime', 'ikea_yellow']
    data = load_yaml(str(FOLDER / STYRBAR))
    catalog = data['variables']['catalog']
    assert [catalog[k]['data']['rgb_color'] for k in ['ha_warm', 'ha_soft', 'ha_white']] == [
        [255, 192, 140], [255, 228, 206], [255, 254, 250]]
    assert catalog['ikea_blue']['data'] == {'xy_color': [0.17, 0.05]}


@pytest.mark.parametrize('name', ['telecommande_ikea_5_boutons.yaml', 'telecommande_ikea_marche_arret.yaml', STYRBAR])
def test_double_press_inputs_only_on_ikea_presses(name):
    inputs = Blueprint(load_yaml(str(FOLDER / name)), expected_domain='automation', schema=BLUEPRINT_SCHEMA).inputs
    doubles = [k for k in inputs if k.endswith('_double_action')]
    presses = [k for k in inputs if k.endswith('_press_action')]
    assert len(doubles) == len(presses) > 0
    assert all(k.replace('_action', '_custom') in inputs for k in doubles)


# ---------------------------------------------------------------- double press and recall

async def test_double_up_recalls_colour_and_keeps_brightness(env):
    await env.automation(STYRBAR, remote=REMOTE, light='light.color', memory='input_text.memory')
    await env.lamps['color'].async_turn_on(hs_color=(247.559, 49.804))
    env.lamps['color'].calls.clear()
    await env.press('on', settle=.1)
    await env.press('on', settle=.2)
    calls = env.lamps['color'].calls
    assert len(calls) == 2
    assert 'brightness' not in calls[1][1] and calls[1][1]['transition'] == .3
    assert xy_of(calls[1]) == pytest.approx(WARM, abs=1e-3)
    assert env.pct('color') == 50
    # A third press is a new single press, not another double.
    await env.press('on', settle=.2)
    assert len(env.lamps['color'].calls) == 3 and env.lamps['color'].calls[2][1] == {}


async def test_late_second_press_is_a_single_press(env):
    await env.automation(STYRBAR, remote=REMOTE, light='light.color', memory='input_text.memory',
                         double_press_ms=250)
    await env.press('on', settle=.35)
    await env.press('on', settle=.1)
    assert [c[1] for c in env.lamps['color'].calls] == [{}, {}]


async def test_double_press_needs_memory_and_diagnostic_says_so(env):
    await env.automation(STYRBAR, remote=REMOTE, light='light.color')
    await env.press('on', settle=.1)
    await env.press('on', settle=.1)
    assert [c[1] for c in env.lamps['color'].calls] == [{}, {}]
    await env.hass.services.async_call('automation', 'trigger',
                                       {'entity_id': 'automation.under_test', 'skip_condition': True}, blocking=True)
    await env.hass.async_block_till_done()
    text = env.notification()
    assert 'double appui est configuré mais ne peut pas fonctionner' in text
    assert 'light.color' in text and 'aucune commande envoyée' in text
    assert len(env.lamps['color'].calls) == 2


async def test_radio_duplicate_is_filtered_but_a_real_double_is_kept(env):
    await env.automation(STYRBAR, remote=REMOTE, light='light.color', memory='input_text.memory')
    await env.press('on', settle=.01)
    await env.press('on', settle=.3)   # Duplicate within 50 ms: ignored.
    assert len(env.lamps['color'].calls) == 1
    await env.press('on', settle=.2)   # Real second press within 800 ms: recall.
    assert xy_of(env.lamps['color'].calls[-1]) == pytest.approx(WARM, abs=1e-3)


async def test_duplicate_filter_without_memory(env):
    await env.automation(STYRBAR, remote=REMOTE, light='light.color')
    await env.press('off', settle=.01)
    await env.press('on', settle=.2)   # Within 50 ms of the previous gesture: ignored.
    assert env.state('color').state == 'off'


async def test_lateral_hold_can_recall_like_the_former_fallback(env):
    await env.automation(STYRBAR, remote=REMOTE, light='light.color', right_hold_action='recall')
    await env.press('hold', **RIGHT_HOLD, settle=.2)
    assert len(env.lamps['color'].calls) == 1
    assert xy_of(env.lamps['color'].calls[0]) == pytest.approx(WARM, abs=1e-3)


async def test_colours_may_be_forbidden_to_switch_on(env):
    await env.automation(STYRBAR, remote=REMOTE, light='light.color', colors_turn_on=False)
    await env.lamps['color'].async_turn_off()
    env.lamps['color'].calls.clear()
    await env.press('press', **RIGHT, settle=.1)
    await env.press('hold', **RIGHT_HOLD, settle=.3)
    assert env.lamps['color'].calls == []
    assert env.state('color').state == 'off'


async def test_recall_may_be_forbidden_to_switch_on(env):
    await env.automation(STYRBAR, remote=REMOTE, light='light.color', right_hold_action='recall',
                         recall_turns_on=False)
    await env.lamps['color'].async_turn_off()
    env.lamps['color'].calls.clear()
    await env.press('hold', **RIGHT_HOLD, settle=.2)
    assert env.lamps['color'].calls == []


async def test_colour_stops_an_active_effect(env):
    await env.automation(STYRBAR, remote=REMOTE, light='light.color')
    await env.lamps['color'].async_turn_on(effect='colorloop')
    env.lamps['color'].calls.clear()
    await env.press('press', **RIGHT, settle=.1)
    assert env.lamps['color'].calls[0][1]['effect'] == 'off'


# ---------------------------------------------------------------- holds

async def test_up_hold_from_off_starts_at_minimum_and_is_bounded(env):
    await env.automation(STYRBAR, remote=REMOTE, light='light.plain', hold_interval=0.2, hold_limit=2)
    await env.lamps['plain'].async_turn_off()
    env.lamps['plain'].calls.clear()
    await env.press('move_with_on_off', args=[0, 83], params={'move_mode': 0, 'rate': 83}, settle=2.6)
    calls = env.lamps['plain'].calls
    assert calls[0][1]['brightness'] == 3   # 1 % minimum
    # 35 %/s for 2 s: about 70 % above the minimum, then the hold limit stops it.
    assert 60 <= env.pct('plain') <= 80
    count = len(calls)
    await asyncio.sleep(.5)
    assert len(env.lamps['plain'].calls) == count
    assert env.hass.states.get('automation.under_test').attributes['current'] == 0


async def test_release_freezes_the_level_actually_reached(env):
    await env.automation(STYRBAR, remote=REMOTE, light='light.plain', memory='input_text.memory', hold_interval=0.4)
    await env.press('move_with_on_off', args=[0, 83], settle=.2)
    first = env.lamps['plain'].calls[0][1]
    assert first['transition'] == .4
    await env.press('stop_with_on_off', settle=.1)
    freeze = env.lamps['plain'].calls[-1][1]
    assert freeze['transition'] == 0
    # The bulb was half-way through a 14 % step that started at 50 %.
    reached = freeze['brightness'] / 2.55
    assert 52 < reached < 63
    assert env.memory()['h'] == '' and env.memory()['g'] == 'stop'


async def test_release_without_memory_stops_without_freezing(env):
    await env.automation(STYRBAR, remote=REMOTE, light='light.plain', hold_interval=0.4)
    await env.press('move_with_on_off', settle=.2)
    await env.press('stop_with_on_off', settle=.6)
    assert len(env.lamps['plain'].calls) == 1


async def test_release_never_overrides_an_external_change(env):
    await env.automation(STYRBAR, remote=REMOTE, light='light.plain', memory='input_text.memory', hold_interval=0.4)
    await env.press('move_with_on_off', settle=.1)
    await env.hass.services.async_call('light', 'turn_on', {'entity_id': 'light.plain', 'brightness': 30}, blocking=True)
    count = len(env.lamps['plain'].calls)
    await env.press('stop_with_on_off', settle=.1)
    assert len(env.lamps['plain'].calls) == count
    assert env.state('plain').attributes['brightness'] == 30


@pytest.mark.parametrize('memory', [True, False])
async def test_repeated_hold_packets_do_not_accelerate(env, memory):
    extra = dict(memory='input_text.memory') if memory else {}
    await env.automation(STYRBAR, remote=REMOTE, light='light.plain', hold_interval=0.3, **extra)
    await env.press('move_with_on_off', settle=.1)
    for _ in range(3):
        await env.press('move_with_on_off', settle=.1)
    # 0.4 s at 0.3 s per step: 2 commands, whatever the number of repeated packets.
    assert len(env.lamps['plain'].calls) == 2


async def test_direction_change_with_memory_restarts_the_hold(env):
    await env.automation(STYRBAR, remote=REMOTE, light='light.plain', memory='input_text.memory', hold_interval=0.3)
    await env.press('move_with_on_off', settle=.1)
    up = env.pct('plain')
    await env.press('move', args=[1, 83], settle=.1)
    assert env.pct('plain') < up
    assert env.memory()['h'] == 'down_hold' and env.memory()['d'] == 'dimmer'


async def test_external_off_cancels_hold_without_relighting(env):
    await env.automation(STYRBAR, remote=REMOTE, light='light.plain', hold_interval=0.2)
    await env.press('move_with_on_off', settle=.1)
    await env.hass.services.async_call('light', 'turn_off', {'entity_id': 'light.plain'}, blocking=True)
    count = len(env.lamps['plain'].calls)
    await asyncio.sleep(.5)
    assert len(env.lamps['plain'].calls) == count
    assert env.state('plain').state == 'off'


async def test_unavailable_lamp_ends_the_hold(env):
    await env.automation(STYRBAR, remote=REMOTE, light='light.plain', hold_interval=0.2)
    await env.press('move_with_on_off', settle=.1)
    env.lamps['plain']._attr_available = False
    env.lamps['plain'].async_write_ha_state()
    count = len(env.lamps['plain'].calls)
    await asyncio.sleep(.5)
    assert len(env.lamps['plain'].calls) == count


async def test_colour_change_during_a_fade_keeps_the_reached_level(env):
    await env.automation(STYRBAR, remote=REMOTE, light='light.color', memory='input_text.memory', hold_interval=0.4)
    await env.press('move_with_on_off', settle=.2)
    await env.press('press', **RIGHT, settle=.1)
    colour = env.lamps['color'].calls[-1][1]
    assert 'xy_color' in colour and 52 < colour['brightness'] / 2.55 < 63


async def test_lost_lateral_release_stops_at_the_limit(env):
    await env.automation(STYRBAR, remote=REMOTE, light='light.color', preset_hold_interval=0.2, hold_limit=2)
    await env.press('hold', **RIGHT_HOLD, settle=2.5)
    count = len(env.lamps['color'].calls)
    assert 9 <= count <= 11
    await asyncio.sleep(.4)
    assert len(env.lamps['color'].calls) == count


# ---------------------------------------------------------------- palette position

async def test_memory_keeps_the_exact_position_when_the_bulb_renders_colours_badly(env):
    # Two neighbouring whites and a bulb that shows every colour shifted towards the second.
    env.lamps['xy'].xy_error = 0.012
    palette = ['ikea_sunrise', 'ikea_warm_white', 'ikea_cool_white']
    await env.automation(STYRBAR, remote=REMOTE, light='light.xy', memory='input_text.memory', palette=palette)
    await env.lamps['xy'].async_turn_off()
    env.lamps['xy'].calls.clear()
    for _ in range(4):
        await env.press('press', **RIGHT, settle=.1)
    sent = [xy_of(c) for c in env.lamps['xy'].calls]
    assert sent == [[0.4369, 0.4041], [0.4599, 0.4106], [0.3804, 0.3804], [0.4369, 0.4041]]


async def test_without_memory_position_follows_the_closest_colour(env):
    palette = ['ikea_sunrise', 'ikea_warm_white', 'ikea_cool_white']
    await env.automation(STYRBAR, remote=REMOTE, light='light.xy', palette=palette)
    await env.lamps['xy'].async_turn_on(xy_color=(0.4599, 0.4106))
    env.lamps['xy'].calls.clear()
    await env.press('press', **RIGHT, settle=.1)
    await env.press('press', **LEFT, settle=.1)
    assert [xy_of(c) for c in env.lamps['xy'].calls] == [[0.3804, 0.3804], [0.4599, 0.4106]]


async def test_external_colour_change_resynchronises_the_palette(env):
    palette = ['ikea_sunrise', 'ikea_warm_white', 'ikea_cool_white', 'ikea_blue']
    await env.automation(STYRBAR, remote=REMOTE, light='light.xy', memory='input_text.memory', palette=palette)
    await env.press('press', **RIGHT, settle=.1)
    await env.hass.services.async_call('light', 'turn_on', {'entity_id': 'light.xy', 'xy_color': [0.38, 0.38]},
                                       blocking=True)
    await env.press('press', **RIGHT, settle=.1)
    assert xy_of(env.lamps['xy'].calls[-1]) == [0.17, 0.05]


async def test_memory_stays_under_255_characters(env):
    await env.automation(STYRBAR, remote=REMOTE, light='light.color', memory='input_text.memory',
                         preset_hold_interval=0.2, hold_limit=3)
    await env.press('hold', args=[3329, 0], params={'param1': 3329, 'param2': 0}, settle=.5)
    raw = env.hass.states.get('input_text.memory').state
    assert raw.startswith('lr1:') and len(raw) <= 200
    assert env.memory()['h'] == 'left_hold' and env.memory()['i'] >= 0
    await env.press('release', args=[4], settle=.1)
    assert env.memory()['h'] == '' and env.memory()['i'] >= 0


# ---------------------------------------------------------------- event ordering and age

async def test_out_of_order_and_old_events_are_ignored(env):
    await env.automation(STYRBAR, remote=REMOTE, light='light.color', memory='input_text.memory')
    now = dt_util.utcnow().timestamp()
    await env.press('off', settle=.1)
    await env.press('on', time_fired=now - 1, settle=.1)   # Older than the last processed event.
    assert env.state('color').state == 'off'
    await env.press('on', time_fired=dt_util.utcnow().timestamp() - 8, settle=.1)
    assert env.state('color').state == 'off'
    await env.press('on', settle=.1)
    assert env.state('color').state == 'on'


async def test_future_timestamps_in_memory_are_discarded(env):
    await env.hass.services.async_call('input_text', 'set_value', {
        'entity_id': 'input_text.memory', 'value': 'placeholder'}, blocking=True)
    await env.automation(STYRBAR, remote=REMOTE, light='light.plain', memory='input_text.memory')
    automation = env.hass.states.get('automation.under_test')
    import hashlib
    owner = 'a' + hashlib.sha256(automation.entity_id.encode()).hexdigest()[:10]
    future = dt_util.utcnow().timestamp() + 3600
    await env.hass.services.async_call('input_text', 'set_value', {
        'entity_id': 'input_text.memory',
        'value': 'lr1:' + json.dumps(dict(v=1, o=owner, g='down_press', t=future, h='up_hold', d='brighter',
                                          s=future, i=-1, p='', x=[], k=''))}, blocking=True)
    await env.press('off', settle=.1)
    assert env.state('plain').state == 'off'
    assert env.memory()['t'] < future - 3000


# ---------------------------------------------------------------- invalid configurations

@pytest.mark.parametrize('value, word', [('lr1:{not json', 'illisible'), ('lr1:' + json.dumps(dict(v=1, o='someone')), 'autre automatisation'),
                                         ('free text', 'illisible')])
async def test_unusable_memory_is_never_overwritten(env, value, word):
    await env.hass.services.async_call('input_text', 'set_value', {'entity_id': 'input_text.memory', 'value': value},
                                       blocking=True)
    await env.automation(STYRBAR, remote=REMOTE, light='light.color', memory='input_text.memory')
    await env.press('off', settle=.1)
    assert env.state('color').state == 'off', 'The remote keeps working without memory'
    assert env.hass.states.get('input_text.memory').state == value
    assert word in env.notification()


async def test_too_short_memory_is_a_configuration_error(env):
    await env.automation(STYRBAR, remote=REMOTE, light='light.color', memory='input_text.short_memory')
    await env.press('off', settle=.1)
    assert env.lamps['color'].calls == []
    assert 'longueur maximale 255' in env.notification()


@pytest.mark.parametrize('settings, word', [(dict(min_pct=60, max_pct=40), 'minimale dépasse'),
                                            (dict(debounce_ms=200, double_press_ms=200), 'doublons'),
                                            (dict(recall_color=[0, 0, 0]), 'couleur de rappel'),
                                            (dict(palette=['ikea_blue', 'not_a_colour']), 'palette')])
async def test_inconsistent_settings_are_reported_and_block_commands(env, settings, word):
    await env.automation(STYRBAR, remote=REMOTE, light='light.color', **settings)
    await env.press('off', settle=.1)
    assert env.lamps['color'].calls == []
    assert word in env.notification()


async def test_without_memory_a_badly_rendered_colour_can_skip_a_preset(env):
    """The documented limit: the same bulb without memory skips the neighbouring white."""
    env.lamps['xy'].xy_error = 0.012
    palette = ['ikea_sunrise', 'ikea_warm_white', 'ikea_cool_white']
    await env.automation(STYRBAR, remote=REMOTE, light='light.xy', palette=palette)
    await env.lamps['xy'].async_turn_off()
    env.lamps['xy'].calls.clear()
    for _ in range(2):
        await env.press('press', **RIGHT, settle=.1)
    assert [xy_of(c) for c in env.lamps['xy'].calls] == [[0.4369, 0.4041], [0.3804, 0.3804]]


# ---------------------------------------------------------------- diagnostic of every model

@pytest.mark.parametrize('name, inputs', [
    ('telecommande_hue_dimmer.yaml', dict(light='light.plain')),
    ('telecommande_hue_tap_dial.yaml', dict(light_1='light.one', light_2='light.color')),
    ('telecommande_ikea_marche_arret.yaml', dict(light='light.plain', memory='input_text.memory')),
    ('telecommande_ikea_5_boutons.yaml', dict(light='light.white')),
    (STYRBAR, dict(light='light.color', memory='input_text.memory')),
    ('bouton_ewelink.yaml', dict(light='light.xy')),
])
async def test_manual_run_shows_a_diagnostic_without_commands(env, caplog, name, inputs):
    await env.automation(name, remote=REMOTE, **inputs)
    await env.hass.services.async_call('automation', 'trigger',
                                       {'entity_id': 'automation.under_test', 'skip_condition': True}, blocking=True)
    await env.hass.async_block_till_done()
    text = env.notification()
    assert 'diagnostic' in text
    # One line per item, so that the notification shows a real list.
    assert text.count('\n- communication : ') == len([k for k in inputs if k.startswith('light')])
    assert '\n- modes : ' in text and ' ;\n' not in text
    for target in [v for k, v in inputs.items() if k.startswith('light')]:
        assert target in text
    assert all(lamp.calls == [] for lamp in env.lamps.values())
    assert 'Error' not in caplog.text and 'Template' not in caplog.text


async def test_former_styrbar_memory_is_taken_over(env):
    await env.hass.services.async_call('input_text', 'set_value', {
        'entity_id': 'input_text.memory', 'value': 'sl1:' + json.dumps(dict(v=1, o='x', c='', t=0))}, blocking=True)
    await env.automation(STYRBAR, remote=REMOTE, light='light.color', memory='input_text.memory')
    await env.press('on', settle=.1)
    await env.press('on', settle=.2)
    assert env.memory()['g'] == 'up_double'
    assert xy_of(env.lamps['color'].calls[-1]) == pytest.approx(WARM, abs=1e-3)
