# SPDX-License-Identifier: GPL-3.0-only
"""Build the self-contained integration watchdog blueprint and its examples.

The blueprint needs no shared configuration file. Everything that used to live in a
package (memory writer, reload worker, admission queue, log automation, manual
commands) is done by the supervision run itself:

* The automation runs in ``queued`` mode: one run at a time per supervision, so it is
  the only writer of its Text helper. Every write is read back.
* The reload runs inside the run. A parallel branch watches the reload delay and sends
  the "reload stuck" alert without touching the memory.
* A reload found "started" at the beginning of a run was necessarily cut short (stop,
  edit, Home Assistant shutdown): queued mode guarantees no other run is alive. It is
  closed automatically; if the entry stayed unloaded, the reload is resumed.
* The global cap of simultaneous reloads and the duplicate check use a
  write-then-read reservation in the helpers themselves (see ``ADMISSION``).
* The run sets the level of its own logger before writing to the log.
"""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
import versioning  # noqa: E402  (tools/versioning.py: version scheme shared by all families)

import yaml

ROOT = Path(__file__).resolve().parent.parent
BASE = ROOT / 'src' / 'integration_watchdog'
VERSION = versioning.read('integration_watchdog')

# Maximum number of reloads running at the same time across all supervisions.
MAX_RUNNING = 50
# A reservation older than the largest allowed reload delay belongs to a supervision
# that has not run since (disabled automation): it no longer takes a place.
STALE_RESERVATION = 3600


class Input(str):
    """A ``!input`` reference in the generated YAML."""


class Dumper(yaml.SafeDumper):
    pass


Dumper.add_representer(Input, lambda d, v: d.represent_scalar('!input', str(v)))
Dumper.add_representer(str, lambda d, v: d.represent_scalar(
    'tag:yaml.org,2002:str', '\n'.join(x.rstrip() for x in v.split('\n')), style='|' if '\n' in v else None))

DESTINATIONS = {
    'integration_watchdog.yaml': 'blueprints/automation/integration_watchdog/integration_watchdog.yaml',
    'netatmo_overkiz_automations.yaml': 'examples/integration_watchdog/netatmo_overkiz_automations.yaml',
    'watchdog_memories.yaml': 'examples/integration_watchdog/watchdog_memories.yaml',
}


def save(name, data, header=''):
    path = ROOT / DESTINATIONS[name]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('# SPDX-License-Identifier: GPL-3.0-only\n' + header
                    + yaml.dump(data, Dumper=Dumper, allow_unicode=True, sort_keys=False, width=110))


def var(**values):
    return {'variables': values}


def template(name):
    return (BASE / name).read_text()


inputs = yaml.safe_load((BASE / 'inputs.yaml').read_text())

# ----------------------------------------------------------------------------- memory
READ = template('read_memory.jinja')
READ_STEP = var(read=READ)
# Any memory problem stops the run before a reset could hide it.
READ_CHECK = {'if': '{{ read.errors | count > 0 }}', 'then': [
    var(configuration_errors='{{ read.errors }}'),
    {'sequence': Input('configuration_error_actions')},
    {'stop': 'Invalid memory; no reset.'}]}
WRITE_FAILURE = [
    var(configuration_errors=['The history could not be saved. No new reload was started.']),
    {'sequence': Input('configuration_error_actions')},
    {'stop': 'Memory write not confirmed.'}]


def write(value):
    """Write the helper and read it back. The run is the only writer of its helper."""
    return [
        var(new_memory=value),
        {'if': '{{ new_memory | length > 255 }}', 'then': WRITE_FAILURE},
        {'if': '{{ states(memory_entity) != new_memory }}', 'then': [
            {'action': 'input_text.set_value', 'target': {'entity_id': '{{ memory_entity }}'},
             'data': {'value': '{{ new_memory }}'}}]},
        {'if': '{{ states(memory_entity) != new_memory }}', 'then': WRITE_FAILURE},
    ]


# Closing of earlier work, before any validation so that a configuration error never
# keeps a finished or interrupted reload open.
#   p > 0, f > 2   reload finished: verification window.
#   p > 0, f = 0   reservation never admitted: dropped, nothing was spent.
#   p > 0, f 1-2   reload admitted or started but no run is alive (queued mode): it was
#                  cut short. Its attempt stays counted. If the entry stayed unloaded,
#                  the reload is resumed ('interrupted'); otherwise verification.
NORMALIZE = """{% set d = read.data %}
{% set window = recovery_seconds if recovery_seconds is number and recovery_seconds is not boolean and 60 <= recovery_seconds <= 3600 else 600 %}
{% if d.p > 0 and d.f > 2 %}
 {{ dict(d,p=0,h=0,n=clock_ts+window,s='verify') }}
{% elif d.p > 0 and d.f == 0 %}
 {{ dict(d,p=0,n=clock_ts,s='deferred') }}
{% elif d.p > 0 and config_entry_attr(entry_id,'state') == 'not_loaded' %}
 {{ dict(d,p=0,f=clock_ts+1,h=0,n=0,s='interrupted') }}
{% elif d.p > 0 %}
 {{ dict(d,p=0,f=clock_ts+1,h=0,n=clock_ts+window,s='verify') }}
{% else %}{{ d }}{% endif %}"""
CLOSE_EARLIER_WORK = [
    READ_STEP, READ_CHECK, var(normalized=NORMALIZE),
    {'if': "{{ read.raw not in ['', 'unknown'] and read.raw != 'iw3:' ~ (normalized | to_json) }}",
     'then': write("iw3:{{ normalized | to_json }}")},
]

# ----------------------------------------------------------------------------- admission
# Write-then-read reservation, without any shared queue. The plan has just written this
# supervision's reservation (p > 0, f = 0); its helper's last_updated is the moment of
# that write. Every contender writes before it reads, so for any two contenders the
# later one sees the earlier one: ranking by last_updated gives the same order to all.
#   running  other reloads admitted or started (f 1-2), always counted;
#   ahead    other reservations not yet admitted, written before this one;
#   tie      same write instant: everybody concerned steps back (no overshoot possible);
#   conflict another supervision of the same entry is reserving or reloading.
ADMISSION = f"""{{% set mine = as_timestamp(states[memory_entity].last_updated) %}}
{{% set ns = namespace(running=0, ahead=0, tie=false, conflict=false) %}}
{{% for s in states.input_text %}}
  {{% if s.entity_id != memory_entity and s.state.startswith('iw3:') %}}
    {{% set m = s.state[4:] | from_json({{}}) %}}
    {{% set p = m.get('p', 0) if m is mapping else 0 %}}
    {{% set f = m.get('f', 0) if m is mapping else 0 %}}
    {{% if p is number and p > 0 and f is number and f <= 2 and admitted_at - p / 1000000 < {STALE_RESERVATION} %}}
      {{% if m.get('e') == entry_key %}}{{% set ns.conflict = true %}}
      {{% elif f > 0 %}}{{% set ns.running = ns.running + 1 %}}
      {{% elif as_timestamp(s.last_updated) < mine %}}{{% set ns.ahead = ns.ahead + 1 %}}
      {{% elif as_timestamp(s.last_updated) == mine %}}{{% set ns.tie = true %}}
      {{% endif %}}
    {{% endif %}}
  {{% endif %}}
{{% endfor %}}
{{{{ {{'running': ns.running, 'ahead': ns.ahead, 'tie': ns.tie, 'conflict': ns.conflict}} }}}}"""
# The entry must still accept a reload at the moment of the call.
ENTRY_OK = ("(config_entry_attr(entry_id,'state') == 'loaded' or (plan.force and config_entry_attr(entry_id,'state') == 'not_loaded'))"
            " and config_entry_attr(entry_id,'disabled_by') is none and not config_entry_attr(entry_id,'pref_disable_polling')"
            " and issues is defined and ('homeassistant','config_entry_reauth_' ~ config_entry_attr(entry_id,'domain') ~ '_' ~ entry_id) not in issues()")
CURRENT = "{{ states(memory_entity)[4:] | from_json({}) if states(memory_entity).startswith('iw3:') else {} }}"
FINISHED = ("{% set c = states(memory_entity)[4:] | from_json({}) if states(memory_entity).startswith('iw3:') else {} %}"
            "{{ c is not mapping or c.get('p') != reservation or c.get('f', 0) > 2 }}")
NOTICE_VARIABLES = dict(integration_title='{{ name }}', attempts_used='{{ plan.attempts + 1 }}',
                        daily_attempts='{{ plan.daily + 1 }}', failed_entities='{{ plan.bad }}')
LOG = lambda level, message: {'if': '{{ logging_enabled }}', 'then': [
    # The run sets the level of its own logger: no configuration file is needed.
    {'action': 'logger.set_level', 'continue_on_error': True,
     'data': {'integration_watchdog': "{{ 'debug' if detailed_logging else 'info' }}"}},
    {'action': 'system_log.write', 'continue_on_error': True,
     'data': {'logger': 'integration_watchdog', 'level': level, 'message': message}}]}

RELOAD = [
    var(admitted_at='{{ as_timestamp(now()) | int }}', reservation='{{ plan.memory.p }}'),
    var(history="{{ plan.memory.a | select('gt', admitted_at - 86400) | list }}",
        contenders=ADMISSION),
    var(admitted=("{{ not contenders.conflict and not contenders.tie"
                  f" and contenders.running + contenders.ahead < {MAX_RUNNING}"
                  " and plan.memory.i < max_attempts and history | count < max_daily and " + ENTRY_OK + " }}")),
    {'if': '{{ admitted }}',
     # The attempt is counted when the reload is admitted, before the call.
     'then': write("iw3:{{ dict(plan.memory, f=2, i=plan.memory.i + 1, a=history + [admitted_at]) | to_json }}"),
     # Deferred: the reservation is withdrawn and nothing is spent; retry in one minute.
     'else': [*write("iw3:{{ dict(plan.memory, p=0, f=0, n=admitted_at + 60,"
                     " s=('duplicate' if contenders.conflict else 'deferred')) | to_json }}"),
              LOG('info', "{{ name }} [{{ entry_id }}]: reload postponed by one minute ({{ 'another watchdog of"
                          " this integration' if contenders.conflict else 'limit of simultaneous reloads reached' }}).")]},
    {'if': '{{ admitted }}', 'then': [{'parallel': [
        # Branch 1: the reload itself, then its end. The end is recorded only for this
        # very reservation, so a stale branch can never close another one.
        {'sequence': [
            var(reload_started='{{ as_timestamp(now()) }}'),
            {'if': '{{ ' + ENTRY_OK + ' }}', 'then': [
                {'action': 'homeassistant.reload_config_entry', 'continue_on_error': True,
                 'data': {'entry_id': '{{ entry_id }}'}}]},
            var(finished_at="{{ as_timestamp(now()) | round(0, 'ceil') | int }}",
                timed_out='{{ as_timestamp(now()) - reload_started >= reload_timeout }}',
                current=CURRENT),
            {'if': "{{ current is mapping and current.get('p') == reservation and current.get('f') == 2 }}",
             # A reload that outlived the delay was reported by branch 2: remember it, so
             # that the return to normal is announced.
             'then': write("iw3:{{ dict(current, f=finished_at, k=('timeout' if timed_out else current.k)) | to_json }}")},
        ]},
        # Branch 2: read-only guard. It never writes the memory, so it cannot race with
        # branch 1; it only alerts when the reload outlives the configured delay.
        {'sequence': [
            {'wait_template': FINISHED, 'timeout': '{{ reload_timeout }}', 'continue_on_timeout': True},
            {'if': '{{ not wait.completed }}', 'then': [
                var(status='timeout', reason=('The reload has been running for more than {{ reload_timeout }} seconds.'
                                              ' It is not cancelled; watching resumes when it ends. Check the traces and'
                                              ' the logs of the integration.'), **NOTICE_VARIABLES),
                {'sequence': Input('failure_actions')},
                LOG('warning', '{{ name }} [{{ entry_id }}]: reload not finished after {{ reload_timeout }} s.'),
            ]},
        ]},
    ]}]},
]

# ----------------------------------------------------------------------------- one evaluation
ROW = ('{{ dict(name=name,entry_id=entry_id,entities=entities,max_age=max_age,policy=policy,'
       'source_time_entity=source_time_entity,source_time_attribute=source_time_attribute,stagger_seconds=stagger_seconds) }}')
EVALUATION = [
    READ_STEP, READ_CHECK, var(memory='{{ read.data }}'),
    # "Run actions" resets the attempts for the current failure (not the 24 h history).
    # An interrupted reload keeps its status, so that it is still resumed.
    {'if': '{{ manual and repeat.index == 1 }}', 'then': [
        var(memory="{{ dict(memory,i=0,n=0,h=0,s=('interrupted' if memory.s == 'interrupted' else 'new')) }}")]},
    var(health=template('health.jinja')),
    # Reservation identifier, in microseconds, should this evaluation decide a reload.
    var(reservation_ts='{{ (as_timestamp(now()) * 1000000) | int }}'),
    var(plan=template('plan.jinja')),
    var(memory_json='iw3:{{ plan.memory | to_json }}', ack_json='iw3:{{ plan.acknowledged | to_json }}'),
    {'if': '{{ memory_json | length > 255 or ack_json | length > 255 }}', 'then': WRITE_FAILURE},
    *write('{{ memory_json }}'),
    var(integration_title='{{ name }}', reason='{{ plan.reason }}', attempts_used='{{ plan.attempts }}',
        daily_attempts='{{ plan.daily }}', failed_entities='{{ plan.bad }}', status='{{ plan.status }}'),
    {'if': "{{ plan.notice == 'failure' }}", 'then': [{'sequence': Input('failure_actions')}],
     'else': [{'if': "{{ plan.notice == 'success' }}", 'then': [{'sequence': Input('success_actions')}]}]},
    # Acknowledgement after the actions succeeded: a failed notification is retried later.
    {'if': "{{ plan.notice != 'none' }}", 'then': [
        READ_STEP, READ_CHECK,
        *write("iw3:{{ dict(read.data, k=(status if plan.notice == 'failure' else '')) | to_json }}")]},
    # Logs come after alerts and acknowledgements: a logging problem never hides an alert.
    {'if': '{{ logging_enabled and (detailed_logging or plan.reload or plan.notice != "none" or plan.status != memory.s) }}',
     'then': [LOG("{{ 'warning' if plan.notice == 'failure' else 'debug' if detailed_logging and plan.status == memory.s"
                  " and not plan.reload else 'info' }}",
                  '{{ name }} [{{ entry_id }}]: {{ status }}; incident={{ attempts_used }}, 24h={{ daily_attempts }}.'
                  ' {{ reason }}')]},
    {'if': '{{ plan.reload }}', 'then': RELOAD},
]
# A second evaluation runs only when this run has just finished a reload: it opens the
# verification window at once instead of waiting for the next check.
# The memory itself carries the signal, so no variable has to cross iterations.
JUST_RELOADED = ("{% set c = states(memory_entity)[4:] | from_json({}) if states(memory_entity).startswith('iw3:') else {} %}"
                 "{{ repeat.index == 1 or (c is mapping and c.get('o') == owner_id and c.get('p', 0) > 0"
                 " and c.get('f', 0) > 2) }}")

variables = {k: Input(k) for group in [inputs['monitoring'], inputs['recovery']]
             for k in group['input'] if k not in ['memory', 'additional_conditions']}
variables.update(
    memory_entity=Input('memory'),
    legacy_owner='w_{{ this.attributes.id | default(this.entity_id,true) }}',
    owner_id='w_{{ sha256(this.attributes.id | default(this.entity_id,true) | string)[:16] }}',
    entry_key='e_{{ sha256(entry_id | string)[:16] }}',
    # "Run actions" in the automation menu has no trigger id.
    manual='{{ trigger is not defined or trigger.id is not defined }}',
)

actions = [
    var(clock_ts='{{ as_timestamp(now()) | int }}'),
    *CLOSE_EARLIER_WORK,
    var(configuration_errors=template('validation.jinja')),
    {'if': '{{ configuration_errors | count > 0 }}', 'then': [
        {'sequence': Input('configuration_error_actions')}, {'stop': 'Invalid settings; reload endings kept.'}]},
    var(excluded="{{ entry_id in (excluded_instances | map(attribute='entry_id') | list) }}"),
    {'if': '{{ excluded }}', 'then': [{'stop': 'Configuration excluded; reload endings kept.'}]},
    {'sequence': Input('configuration_resolved_actions')},
    var(interventions_allowed=False),
    {'if': [{'condition': 'template', 'value_template': '{{ not observation_only }}'},
            {'condition': 'and', 'conditions': Input('additional_conditions')}],
     'then': [var(interventions_allowed=True)]},
    var(row=ROW),
    {'repeat': {'count': 2, 'sequence': [
        {'if': JUST_RELOADED, 'then': [
            {'if': '{{ repeat.index > 1 }}', 'then': [
                var(clock_ts='{{ as_timestamp(now()) | int }}'), *CLOSE_EARLIER_WORK]},
            *EVALUATION]}]}},
]

DESCRIPTION = ('Watches the entities of an integration and tries to reload it when it fails. The number of'
               ' attempts, the delays, the notifications and the logs can be set. Create a Text helper, then one'
               ' automation per integration configuration; no other file is needed.'
               ' Guide: https://github.com/fbonelle/home-assistant-blueprints/blob/main/docs/integration_watchdog.en.md')
blueprint = {
    'blueprint': {
        'name': f'Integration watchdog — {VERSION}',
        'description': DESCRIPTION,
        'domain': 'automation',
        'homeassistant': {'min_version': versioning.minimum_ha()},
        'input': inputs,
        'source_url': 'https://github.com/fbonelle/home-assistant-blueprints/blob/main/blueprints/automation/'
                      'integration_watchdog/integration_watchdog.yaml',
        'author': 'fbonelle',
    },
    # One run at a time: the run is the only writer of its helper. Waiting runs are
    # redundant (each one re-reads every state), so extra ones are dropped silently.
    'mode': 'queued',
    'max': 10,
    'max_exceeded': 'silent',
    'trace': {'stored_traces': 20},
    'variables': variables,
    'triggers': [
        {'trigger': 'time_pattern', 'minutes': Input('scan_minutes'), 'id': 'scan'},
        {'trigger': 'state', 'entity_id': Input('entities'), 'id': 'availability'},
        {'trigger': 'homeassistant', 'event': 'start', 'id': 'start'},
    ],
    # Value changes of the watched entities are ignored; only availability changes count.
    'conditions': [{'condition': 'template', 'value_template': (
        "{{ trigger is not defined or trigger.id != 'availability' or trigger.from_state is none or trigger.to_state is none"
        " or ((trigger.from_state.state in ['unknown','unavailable'] or trigger.from_state.attributes.get('restored',false))"
        " != (trigger.to_state.state in ['unknown','unavailable'] or trigger.to_state.attributes.get('restored',false))) }}")}],
    'actions': actions,
}
save('integration_watchdog.yaml', blueprint,
     f'# Version {VERSION} — self-contained blueprint: no shared configuration file.\n'
     '# Memory: p reservation, f 0 reserved, 1-2 admitted or started, >2 end of the reload.\n')

# Examples reuse fictitious identifiers only.
examples = yaml.safe_load((BASE / 'examples.yaml').read_text())
save('netatmo_overkiz_automations.yaml', examples,
     '# Three examples; other instances are added with the same form.\n')
save('watchdog_memories.yaml', yaml.safe_load((BASE / 'memories.yaml').read_text()))
