# SPDX-License-Identifier: GPL-3.0-only
"""Build the lighting blueprints: one standalone automation blueprint per remote model,
plus the automatic switch-off blueprint.

The shared engine (src/lighting/engine.yaml) is copied into every remote blueprint at
build time, so Home Assistant runs self-contained blueprints with no shared script and
no memory helper. No Python runs inside Home Assistant.
"""
from pathlib import Path
import colorsys
import copy
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import versioning  # noqa: E402  (tools/versioning.py: version scheme shared by all families)
import yaml

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / 'src/lighting'
OUT = ROOT / 'blueprints/automation/lighting'
DOCS = 'https://github.com/fbonelle/home-assistant-blueprints/blob/main/docs/lighting.md'
SOURCE = 'https://github.com/fbonelle/home-assistant-blueprints/blob/main/blueprints/automation/lighting/'


class Input(str):
    """A !input reference kept verbatim in the generated YAML."""


class Loader(yaml.SafeLoader):
    pass


class Dumper(yaml.SafeDumper):
    pass


Loader.add_constructor('!input', lambda loader, node: Input(loader.construct_scalar(node)))
Dumper.add_representer(Input, lambda dumper, value: dumper.represent_scalar('!input', str(value)))
class Flow(list):
    """A short numeric list written on one line, such as a colour."""


Dumper.add_representer(Flow, lambda d, v: d.represent_sequence('tag:yaml.org,2002:seq', v, flow_style=True))
Dumper.add_representer(str, lambda d, v: d.represent_scalar(
    'tag:yaml.org,2002:str', '\n'.join(x.rstrip() for x in v.split('\n')), style='|' if '\n' in v else None))


def load(name):
    return yaml.load((BASE / name).read_text(), Loader=Loader)


def header(source):
    return ('# SPDX-License-Identifier: GPL-3.0-only\n'
            f'# Généré par tools/build_lighting.py ; modifier {source}.\n')


REMOTE_NOTE = (
    '# Structure : les variables traduisent l\'événement zha_event en geste normalisé\n'
    '# (« gesture »), choisissent la lampe (« lamp ») et l\'action réglée pour ce geste\n'
    '# (« action »). La condition écarte les événements sans action, qui ne redémarrent donc\n'
    '# jamais un maintien en cours. Les actions forment le moteur commun, identique pour\n'
    '# toutes les télécommandes ; ses commentaires détaillés sont dans src/lighting/engine.yaml.\n')


def write(name, data, source, note=''):
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / name).write_text(header(source) + note + yaml.dump(
        data, Dumper=Dumper, allow_unicode=True, sort_keys=False, width=110))


def rgb_xy(rgb):
    """The RGB-to-xy matrix used by Home Assistant, without device-specific clipping."""
    r, g, b = [v / 255 for v in rgb]
    r, g, b = [((v + .055) / 1.055) ** 2.4 if v > .04045 else v / 12.92 for v in (r, g, b)]
    x = r * .664511 + g * .154324 + b * .162028
    y = r * .283881 + g * .668433 + b * .047685
    z = r * .000088 + g * .072310 + b * .986039
    return [round(x / (x + y + z), 4), round(y / (x + y + z), 4)]


def catalog_entry(row):
    """The command sent to the lamp, unchanged, and xy coordinates used only to recognise it."""
    if 'hs' in row:
        rgb = [v * 255 for v in colorsys.hsv_to_rgb(row['hs'][0] / 360, row['hs'][1] / 100, 1)]
        return {'data': {'hs_color': Flow(row['hs'])}, 'xy': Flow(rgb_xy(rgb))}
    if 'rgb_color' in row:
        return {'data': {'rgb_color': Flow(row['rgb_color'])}, 'xy': Flow(rgb_xy(row['rgb_color']))}
    return {'data': {'xy_color': Flow(row['xy_color'])}, 'xy': Flow([round(v, 4) for v in row['xy_color']])}


def expand_gestures(model):
    """Every gesture of a model, with the double press added after each press that has one."""
    result = []
    for section in model['sections']:
        rows = []
        for gesture in section['gestures']:
            rows.append(gesture)
            if gesture.get('double'):
                assert gesture['key'].endswith('_press'), gesture
                rows.append({'key': gesture['key'].replace('_press', '_double'),
                             'label': 'Double appui (assistant de mémoire nécessaire)',
                             'default': gesture.get('double_default', 'none')})
        result.append((section, rows))
    return result


def gesture_inputs(gesture, catalog):
    """The action choice and the custom action of one gesture."""
    options = [dict(value=a['value'], label=a['label']) for a in catalog
               if gesture.get('hold') or not a.get('hold_only')]
    assert gesture['default'] in [o['value'] for o in options], gesture
    return {
        f"{gesture['key']}_action": {
            'name': gesture['label'],
            'default': gesture['default'],
            'selector': {'select': {'mode': 'dropdown', 'options': options}},
        },
        f"{gesture['key']}_custom": {
            'name': f"{gesture['label']} — action personnalisée",
            'description': 'Exécutée seulement si « Action personnalisée » est choisie ci-dessus.',
            'default': [],
            'selector': {'action': {}},
        },
    }


def build_remote(key, model, engine, palette, version):
    catalog = engine['actions_catalog']
    known = [a['value'] for a in catalog]
    sections = expand_gestures(model)
    gestures = [g for _, rows in sections for g in rows]
    keys = [g['key'] for g in gestures]
    assert len(keys) == len(set(keys)), key

    inputs = {
        'remote': {
            'name': 'Télécommande',
            'selector': {'device': {'filter': model['filter'] if isinstance(model['filter'], list)
                                    else [model['filter']]}},
        },
    }
    if model['targets'] == 'dial':
        for n in range(1, 5):
            inputs[f'light_{n}'] = {
                'name': f'Lampe du bouton {n}',
                'description': None if n == 1 else 'Facultatif.',
                'selector': {'entity': {'filter': [{'domain': 'light'}]}},
            }
            if n > 1:
                inputs[f'light_{n}']['default'] = ''
            else:
                del inputs[f'light_{n}']['description']
    else:
        inputs['light'] = {'name': 'Lampe', 'selector': {'entity': {'filter': [{'domain': 'light'}]}}}
    inputs['memory'] = copy.deepcopy(engine['memory_input'])
    # The memory helper is only needed for the double press of the models whose firmware
    # does not report it; elsewhere, its description must not suggest otherwise.
    memory_double = any(k.endswith('_double') for k in keys)
    if not memory_double:
        old = 'Nécessaire pour le double appui ; apporte aussi'
        text = engine['memory_input']['description']
        assert text.count(old) == 1, text
        inputs['memory']['description'] = text.replace(old, 'Apporte')

    for section, rows in sections:
        content = {}
        for gesture in rows:
            content.update(gesture_inputs(gesture, catalog))
        if section['key'] == 'dial':
            content['dial_scale'] = {
                'name': 'Sensibilité de la molette',
                'description': ('Multiplie l\'amplitude transmise par la molette, convertie en pour cent : '
                                'un cran lent vaut environ 3 %, une rotation rapide jusqu\'à 80 %.'),
                'default': 1,
                'selector': {'number': {'min': 0.1, 'max': 5, 'step': 0.1, 'mode': 'box'}},
            }
        inputs[section['key']] = {'name': section['name'], 'icon': section['icon'], 'input': content}

    settings = copy.deepcopy(engine['settings_inputs'])
    for name, value in model.get('settings', {}).items():
        assert name in settings, name
        settings[name]['default'] = value
    default_palette = model.get('palette', [k for k in palette if not k.startswith(('ha_', 'ikea_'))])
    assert all(k in palette for k in default_palette) and len(set(default_palette)) == len(default_palette)
    settings['palette']['default'] = default_palette
    settings['palette']['selector']['select']['options'] = [
        dict(value=k, label=v['name']) for k, v in palette.items()]
    inputs['settings'] = {'name': 'Réglages de variation et de couleur', 'icon': 'mdi:tune',
                          'collapsed': True, 'input': settings}

    # Variables in evaluation order: event fields, constants, inputs, gesture, target, action.
    variables = dict(engine['variables'])
    variables['repeating_hold'] = model['repeating_hold']
    variables['catalog'] = {k: catalog_entry(v) for k, v in palette.items()}
    variables['double_keys'] = [k for k in keys if k.endswith('_double')]
    for name in settings:
        variables[name] = Input(name)
    variables['memory_entity'] = Input('memory')
    variables['dial_scale'] = Input('dial_scale') if model['targets'] == 'dial' else 1
    variables['actions_map'] = {k: Input(f'{k}_action') for k in keys}
    variables['gesture_raw'] = model['decode']
    if model['targets'] == 'dial':
        for n in range(1, 5):
            variables[f'light_{n}'] = Input(f'light_{n}')
        variables['slots'] = '{{ [light_1, light_2, light_3, light_4] }}'
        variables['lamps'] = "{{ slots | select('string') | select('match', '^light[.]') | list }}"
        # A button drives its own lamp. The dial drives the lamp switched on most recently
        # among those that are on, or the lamp switched most recently if all are off;
        # unavailable lamps are never chosen. Lamps can follow one another (a group and its
        # members change together): among the lamps changed less than 2 s before the most
        # recent one, the lamp still carrying the context of this automation's previous run,
        # i.e. the lamp the remote actually commanded, wins.
        variables['lamp'] = (
            "{% if gesture_raw is match('^button_[1-4]_') %}"
            "{{ slots[gesture_raw[7] | int - 1] if slots[gesture_raw[7] | int - 1] is string else '' }}"
            "{% else %}"
            "{% set usable = lamps | select('has_value') | list %}"
            "{% set lit = usable | select('is_state', 'on') | list %}"
            "{% set pool = lit if lit | count > 0 else usable %}"
            "{% set ns = namespace(best='', stamp=-1, own='', own_stamp=-1) %}"
            "{% for e in pool %}"
            "{% set t = as_timestamp(states[e].last_changed, 0) %}"
            "{% if t > ns.stamp %}{% set ns.best = e %}{% set ns.stamp = t %}{% endif %}"
            "{% endfor %}"
            "{% for e in pool %}"
            "{% set s = states[e] %}"
            "{% set t = as_timestamp(s.last_changed, 0) %}"
            "{% if this is defined and s.context.id == this.context.id and ns.stamp - t <= 2"
            " and t > ns.own_stamp %}{% set ns.own = e %}{% set ns.own_stamp = t %}{% endif %}"
            "{% endfor %}{{ ns.own if ns.own != '' else ns.best }}"
            "{% endif %}")
    else:
        variables['lamp'] = Input('light')
    for name, value in engine['derived_variables'].items():
        variables[name] = value.replace('@known', repr(known)) if isinstance(value, str) else value

    custom = {'choose': [{'conditions': f"{{{{ gesture == '{k}' }}}}",
                          'sequence': Input(f'{k}_custom')} for k in keys]}

    def expand(value):
        if value == '@custom':
            return custom
        if isinstance(value, dict):
            return {k: expand(v) for k, v in value.items()}
        if isinstance(value, list):
            return [expand(v) for v in value]
        return value

    blueprint = {
        'blueprint': {
            'name': f"{model['name']} — {version}",
            'description': (model['description'].strip() + ' Actions et réglages communs à toutes '
                            'les télécommandes de la famille ; variations continues bornées. '
                            + ('Assistant de mémoire facultatif, nécessaire au double appui. ' if memory_double
                               else 'Assistant de mémoire facultatif. ') +
                            'Menu → Exécuter les actions affiche un diagnostic sans commander la lampe. '
                            f'Guide : {DOCS}'),
            'domain': 'automation',
            'homeassistant': {'min_version': versioning.MIN_HA},
            'author': 'fbonelle',
            'source_url': SOURCE + model['file'],
            'input': inputs,
        },
        'mode': 'restart',
        'max_exceeded': 'silent',
        'triggers': [{'trigger': 'event', 'event_type': 'zha_event',
                      'event_data': {'device_id': Input('remote')}}],
        'variables': variables,
        'conditions': [{'condition': 'template', 'value_template': engine['condition']}],
        'actions': expand(engine['actions']),
    }
    write(model['file'], blueprint, 'src/lighting/engine.yaml et src/lighting/models.yaml', REMOTE_NOTE)


def build():
    version = versioning.read('lighting')
    engine = load('engine.yaml')
    palette = load('palette.yaml')
    for key, model in load('models.yaml').items():
        build_remote(key, model, engine, palette, version)
    # The automatic switch-off blueprint is hand-written YAML: copy it verbatim to keep its
    # comments, adding only the version, the guide link and the publication fields.
    text = (BASE / 'auto_off.yaml').read_text()
    replacements = [
        ("  name: Extinction automatique de l'éclairage\n",
         f"  name: Extinction automatique de l'éclairage — {version}\n"),
        ("    Assistant Minuteur facultatif pour voir le temps restant.\n",
         f"    Assistant Minuteur facultatif pour voir le temps restant.\n    Guide : {DOCS}\n"),
        (f"    min_version: '{versioning.MIN_PLACEHOLDER}'  # tools/versioning.py (MIN_HA)\n",
         f'    min_version: {versioning.MIN_HA}\n'),
        ('  domain: automation\n',
         f"  domain: automation\n  author: fbonelle\n  source_url: {SOURCE}extinction_automatique.yaml\n"),
    ]
    for old, new in replacements:
        assert text.count(old) == 1, old
        text = text.replace(old, new)
    text = text.split('\n', 1)[1]  # The licence line is written again by header().
    yaml.load(text, Loader=Loader)
    (OUT / 'extinction_automatique.yaml').write_text(header('src/lighting/auto_off.yaml') + text)
    examples = ROOT / 'examples/lighting'
    examples.mkdir(parents=True, exist_ok=True)
    if (BASE / 'automations.yaml').exists():
        (examples / 'automations.yaml').write_text((BASE / 'automations.yaml').read_text())


if __name__ == '__main__':
    build()
