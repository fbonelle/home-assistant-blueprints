# SPDX-License-Identifier: GPL-3.0-only
"""Build the first public release from explicit templates; no runtime Python."""
from pathlib import Path
import copy,re,yaml
ROOT=Path(__file__).resolve().parent.parent
BASE=ROOT/'src'/'integration_watchdog'
VERSION=(BASE/'VERSION').read_text().strip()
assert re.fullmatch(r'(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)',VERSION), 'Invalid blueprint version'
OUT=ROOT
class Input(str):pass
class D(yaml.SafeDumper):pass
D.add_representer(Input,lambda d,v:d.represent_scalar('!input',str(v)))
D.add_representer(str,lambda d,v:d.represent_scalar('tag:yaml.org,2002:str','\n'.join(x.rstrip() for x in v.split('\n')),style='|' if '\n' in v else None))
DESTINATIONS={
 'surveillance_integrations.yaml':'blueprints/automation/integration_watchdog/surveillance_integrations.yaml',
 'package_surveillance_integrations.yaml':'packages/integration_watchdog.yaml',
 'automatisations_netatmo_overkiz.yaml':'examples/integration_watchdog/automatisations_netatmo_overkiz.yaml',
 'memoires_surveillance_integrations.yaml':'examples/integration_watchdog/memoires_surveillance_integrations.yaml',
}
def save(name,data,header=''):
 if name not in DESTINATIONS:return
 p=ROOT/DESTINATIONS[name];p.parent.mkdir(parents=True,exist_ok=True)
 p.write_text('# SPDX-License-Identifier: GPL-3.0-only\n'+header+yaml.dump(data,Dumper=D,allow_unicode=True,sort_keys=False,width=110))
def var(**kw):return {'variables':kw}
def cond(t):return {'condition':'template','value_template':t}
def script_call(expected,value,response='write_result',guard_off=''):
 return {'action':'script.surveillance_ecrire_memoire','data':{'memory_entity':'{{ memory_entity }}','expected':expected,'value':value,'guard_off':guard_off},'response_variable':response}
def template(n):return (BASE/n).read_text()
inputs=yaml.safe_load((BASE/'inputs.yaml').read_text())
si=inputs['surveillance']['input'];ri=inputs['recuperation']['input'];ni=inputs['notifications']['input']
# Empty selector dictionaries are removed by Home Assistant package merging.
# Keep an explicit default so the selector type survives that merge.
common_fields={'memory_entity':{'name':'Assistant Texte de la surveillance','required':True,'selector':{'entity':{'filter':[{'domain':'input_text'}]}}}}
# One writer serializes ALL memory updates and validates compare-and-set and readback.
writer={'alias':'Surveillance — Enregistrer l’historique','description':'Service interne de comparaison-écriture. Ne pas appeler manuellement. Une écriture concurrente est refusée ; aucun écrasement d’un état plus récent.','mode':'queued','max':1000,'max_exceeded':'warning','fields':{**common_fields,'expected':{'required':True,'selector':{'text':{'multiline':False}}},'value':{'required':True,'selector':{'text':{'multiline':False}}},'guard_off':{'default':'','selector':{'text':{'multiline':False}}}},'sequence':[
 var(result={'ok':False,'conflict':True}),
 {'if':"{{ states(memory_entity) == expected and (guard_off | default('') == '' or is_state(guard_off,'off')) }}",'then':[
  {'action':'input_text.set_value','target':{'entity_id':'{{ memory_entity }}'},'data':{'value':'{{ value }}'}},
  var(result="{{ dict(ok=(states(memory_entity) == value),conflict=false) }}")
 ]},
 {'stop':'Résultat de persistance','response_variable':'result'}]}
# Worker claims f=1 -> f=2 with CAS before calling the backend, so replayed launches
# of the same admitted reservation cannot execute the reload a second time.
job_fields={**common_fields,**{k:{'required':True,'selector':{'text':{'multiline':False}}} for k in ['entry_id','owner_id','entry_key','reservation']}}
readjob="{{ states(memory_entity)[4:] | from_json({}) if states(memory_entity).startswith('iw3:') else {} }}"
match="{{ record is mapping and record.get('o') == owner_id and record.get('e') == entry_key and record.get('p',0) == reservation and reservation | int(0) > 0 }}"
worker={'alias':'Surveillance — Relancer une intégration','description':'Exécution interne après admission. Un seul lancement par réservation. La fin est persistée avant son événement de réveil ; une fin ne prouve pas le rétablissement.','mode':'parallel','max':50,'max_exceeded':'warning','fields':job_fields,'sequence':[
 var(raw='{{ states(memory_entity) }}',record=readjob),cond(match),cond('{{ record.f == 1 }}'),
 script_call('{{ raw }}',"iw3:{{ dict(record,f=2) | to_json }}"),cond('{{ write_result is mapping and write_result.get("ok",false) }}'),
 {'if':"{{ config_entry_attr(entry_id,'state') == 'loaded' and config_entry_attr(entry_id,'disabled_by') is none and not config_entry_attr(entry_id,'pref_disable_polling') and issues is defined and ('homeassistant','config_entry_reauth_' ~ config_entry_attr(entry_id,'domain') ~ '_' ~ entry_id) not in issues() }}",'then':[{'action':'homeassistant.reload_config_entry','data':{'entry_id':'{{ entry_id }}'},'continue_on_error':True}]},
 # The event is only a wake-up optimization; the durable f is sufficient on next scan.
 var(finished_at="{{ as_timestamp(now()) | round(0,'ceil') | int }}"),
 {'repeat':{'count':5,'sequence':[
  var(raw='{{ states(memory_entity) }}',record=readjob),
  {'if':"{{ record is mapping and record.get('o') == owner_id and record.get('e') == entry_key and record.get('p') == reservation and record.get('f') == 2 }}",'then':[script_call('{{ raw }}','iw3:{{ dict(record,f=finished_at) | to_json }}')]}
 ]}},
 {'event':'integration_watchdog_completed','event_data':{'entry_id':'{{ entry_id }}','memory_entity':'{{ memory_entity }}','owner_id':'{{ owner_id }}','reservation':'{{ reservation }}'}}]}
# Short, serial admission owns worker starts. It never waits for backend completion.
# A full pool writes a durable deferral with no change to incident/daily budgets.
admission={'id':'surveillance_admission','alias':'Surveillance admission','mode':'queued','max':1000,'max_exceeded':'warning','triggers':[{'trigger':'event','event_type':'integration_watchdog_request'}],'actions':[
 var(**{k:'{{ trigger.event.data.'+k+' }}' for k in ['entry_id','memory_entity','owner_id','entry_key','reservation','max_attempts','max_daily']}),
 var(raw='{{ states(memory_entity) }}',record=readjob),cond(match),cond('{{ record.f == 0 }}'),
 var(conflicts="""{% set ns=namespace(ids=[]) %}
{% for s in states.input_text %}{% if s.entity_id != memory_entity and s.state.startswith('iw3:') %}
{% set m=s.state[4:]|from_json({}) %}{% if m is mapping and m.get('e') == entry_key %}{% set ns.ids=ns.ids+[s.entity_id] %}{% endif %}
{% endif %}{% endfor %}{{ ns.ids }}"""),
 var(capacity="{{ states('script.surveillance_recharger_instance') in ['on','off'] and state_attr('script.surveillance_recharger_instance','mode') == 'parallel' and state_attr('script.surveillance_recharger_instance','current') | int(9999) < state_attr('script.surveillance_recharger_instance','max') | int(0) }}",
     admitted_at='{{ as_timestamp(now()) | int }}'),
 var(history="{{ record.a | select('gt',admitted_at-86400) | list }}"),
 var(allowed="{{ conflicts | count == 0 and capacity and max_attempts is number and max_daily is number and 1 <= max_attempts <= 10 and 1 <= max_daily <= 6 and record.i < max_attempts and history | count < max_daily and config_entry_attr(entry_id,'state') == 'loaded' and config_entry_attr(entry_id,'disabled_by') is none and not config_entry_attr(entry_id,'pref_disable_polling') and issues is defined and ('homeassistant','config_entry_reauth_' ~ config_entry_attr(entry_id,'domain') ~ '_' ~ entry_id) not in issues() }}"),
 {'if':'{{ allowed }}','then':[
  script_call('{{ raw }}','iw3:{{ dict(record,f=1,i=record.i+1,a=history+[admitted_at]) | to_json }}'),
  {'if':'{{ write_result is mapping and write_result.get("ok",false) }}','then':[
   {'action':'script.turn_on','target':{'entity_id':'script.surveillance_recharger_instance'},'data':{'variables':{k:'{{ '+k+' }}' for k in ['entry_id','memory_entity','owner_id','entry_key','reservation']}}}
  ]}
 ],'else':[
  script_call('{{ raw }}',"iw3:{{ dict(record,p=0,f=0,n=admitted_at+60,s=('duplicate' if conflicts | count > 0 else 'deferred')) | to_json }}")
 ]},
 {'event':'integration_watchdog_completed','event_data':{'entry_id':'{{ entry_id }}','memory_entity':'{{ memory_entity }}','owner_id':'{{ owner_id }}','reservation':'{{ reservation }}'}}]}
# Manual controls preserve budgets and pass through the same writer. Guard-off is
# tested inside the writer, preventing a race with a worker's claim.
confirm={'alias':'Surveillance — Confirmer la fin d’une relance','mode':'single','fields':{'memory':common_fields['memory_entity']},'sequence':[
 var(memory_entity='{{ memory }}',raw='{{ states(memory) }}',record="{{ states(memory)[4:] | from_json({}) if states(memory).startswith('iw3:') else {} }}"),
 cond("{{ record is mapping and record.get('p',0) > 0 and record.get('f',0) <= 2 }}"),
 script_call('{{ raw }}',"iw3:{{ dict(record,f=(as_timestamp(now()) | round(0,'ceil') | int)) | to_json }}",guard_off='script.surveillance_recharger_instance'),cond('{{ write_result is mapping and write_result.get("ok",false) }}'),
 {'event':'integration_watchdog_wake','event_data':{'memory_entity':'{{ memory_entity }}'}}]}
rearm={'alias':'Surveillance — Réinitialiser les tentatives pour une panne','mode':'parallel','max':50,'fields':{'memory':common_fields['memory_entity']},'sequence':[{'event':'integration_watchdog_rearm','event_data':{'memory_entity':'{{ memory }}'}}]}
scripts={'surveillance_ecrire_memoire':writer,'surveillance_recharger_instance':worker,'surveillance_confirmer_fin':confirm,'surveillance_rearmer_incident':rearm}
# The supervision is the policy owner. All its CAS updates re-read on conflict;
# confirmations are normalized before global validation or auxiliary actions.
variables={k:Input(k) for group in [inputs['surveillance'],inputs['recuperation']] for k in group['input'] if k not in ['memory','additional_conditions']}
variables.update(memory_entity=Input('memory'),legacy_owner='w_{{ this.attributes.id | default(this.entity_id,true) }}',owner_id="w_{{ sha256(this.attributes.id | default(this.entity_id,true) | string)[:16] }}",entry_key="e_{{ sha256(entry_id | string)[:16] }}")
read=template('read_memory.jinja')
readstep=var(read=read)
errcheck={'if':'{{ read.errors | count > 0 }}','then':[var(configuration_errors='{{ read.errors }}'),{'sequence':Input('configuration_error_actions')},{'stop':'Mémoire non valide ; aucune remise à zéro.'}]}
phase="""{% set d=read.data %}
{% set window = recovery_seconds if recovery_seconds is number and recovery_seconds is not boolean and 60 <= recovery_seconds <= 3600 else 600 %}
{% if d.p > 0 and d.f > 2 %}
 {{ dict(d,p=0,h=0,n=clock_ts+window,s='verify') }}
{% elif d.p > 0 and trigger is defined and trigger.id == 'start' and is_state('script.surveillance_recharger_instance','off') %}
 {{ dict(d,p=0,f=clock_ts+1,h=0,n=clock_ts+window,s='verify') }}
{% else %}{{ d }}{% endif %}"""
# A cold-start normalization is only allowed by the real native HA start trigger.
phase_loop=[readstep,errcheck,var(normalized=phase),{'if':"{{ read.raw in ['', 'unknown'] or read.raw == 'iw3:' ~ (normalized | to_json) }}",'then':[var(write_result={'ok':True})],'else':[script_call('{{ read.raw }}','iw3:{{ normalized | to_json }}',guard_off="{{ 'script.surveillance_recharger_instance' if trigger is defined and trigger.id == 'start' and read.data.p > 0 and read.data.f <= 2 else '' }}")]}]
write_failure=[var(configuration_errors=['L’historique n’a pas pu être enregistré. Aucune nouvelle relance n’a été lancée.']),{'sequence':Input('configuration_error_actions')},{'stop':'Écriture de mémoire non confirmée.'}]
row='{{ dict(name=name,entry_id=entry_id,entities=entities,max_age=max_age,policy=policy,source_time_entity=source_time_entity,source_time_attribute=source_time_attribute,stagger_seconds=stagger_seconds) }}'
policy=[readstep,errcheck,var(memory='{{ read.data }}'),
 {'if':"{{ trigger is defined and trigger.id == 'rearm' and memory.p == 0 }}",'then':[var(memory="{{ dict(memory,i=0,n=0,h=0,s='new') }}")]},
 var(health=template('health.jinja')),var(plan=template('plan.jinja')),
 var(memory_json='iw3:{{ plan.memory | to_json }}',ack_json='iw3:{{ plan.acknowledged | to_json }}'),
 {'if':'{{ memory_json | length > 255 or ack_json | length > 255 }}','then':write_failure},
 script_call('{{ read.raw }}','{{ memory_json }}')]
# Global parameter validation is separate from durable completion bookkeeping.
actions=[var(clock_ts='{{ as_timestamp(now()) | int }}',reservation_ts='{{ (as_timestamp(now()) * 1000000) | int }}'),
 {'repeat':{'sequence':phase_loop,'until':"{{ (write_result is mapping and write_result.get('ok',false)) or repeat.index >= 5 }}"}},
 {'if':"{{ write_result is not mapping or not write_result.get('ok',false) }}",'then':write_failure},
 var(configuration_errors=template('validation.jinja')),
 {'if':'{{ configuration_errors | count > 0 }}','then':[{'sequence':Input('configuration_error_actions')},{'stop':'Paramètres invalides ; confirmations conservées.'}]},
 # Exclusions stop policy/notifications, but never skip durable completion closure.
 var(excluded="{{ entry_id in (excluded_instances | map(attribute='entry_id') | list) }}"),
 {'if':'{{ excluded }}','then':[{'stop':'Instance exclue ; confirmations déjà persistées.'}]},
 {'sequence':Input('configuration_resolved_actions')},var(interventions_allowed=False),
 {'if':[cond('{{ not observation_only }}'),{'condition':'and','conditions':Input('additional_conditions')}],'then':[var(interventions_allowed=True)]},
 var(row=row),
 {'repeat':{'sequence':policy,'until':"{{ (write_result is mapping and write_result.get('ok',false)) or repeat.index >= 5 }}"}},
 {'if':"{{ write_result is not mapping or not write_result.get('ok',false) }}",'then':write_failure},
 {'if':'{{ plan.reload }}','then':[{'event':'integration_watchdog_request','event_data':{k:'{{ '+k+' }}' for k in ['entry_id','memory_entity','owner_id','entry_key','max_attempts','max_daily']} | {'reservation':'{{ plan.memory.p }}'}}]},
 var(integration_title='{{ name }}',reason='{{ plan.reason }}',attempts_used='{{ plan.attempts }}',daily_attempts='{{ plan.daily }}',failed_entities='{{ plan.bad }}',status='{{ plan.status }}'),
 {'if':'{{ logging_enabled and (detailed_logging or plan.reload or plan.notice != "none" or plan.status != memory.s) }}','then':[{'event':'integration_watchdog_log','event_data':{'level':"{{ 'warning' if plan.notice == 'failure' else 'debug' if detailed_logging and plan.status == memory.s and not plan.reload else 'info' }}",'message':'{{ name }} [{{ entry_id }}] : {{ status }} ; incident={{ attempts_used }}, 24h={{ daily_attempts }}. {{ reason }}'}}]},
 {'if':"{{ plan.notice == 'failure' }}",'then':[{'sequence':Input('failure_actions')}],'else':[{'if':"{{ plan.notice == 'success' }}",'then':[{'sequence':Input('success_actions')}]}]},
 # Ack with CAS: a notification may yield while the worker commits its end.
 # Never overwrite that new durable state with an older notification snapshot.
 {'if':"{{ plan.notice != 'none' }}",'then':[
  {'repeat':{'sequence':[readstep,errcheck,var(acknowledged="{{ dict(read.data,k=(status if plan.notice == 'failure' else '')) }}"),script_call('{{ read.raw }}','iw3:{{ acknowledged | to_json }}')],'until':"{{ (write_result is mapping and write_result.get('ok',false)) or repeat.index >= 5 }}"}}
 ]}]
bp={'blueprint':{'name':f'Surveillance et relance des intégrations — {VERSION}','description':'Surveille les entités d’une intégration et tente de la relancer en cas de panne. Le nombre de tentatives, les délais, les notifications et les journaux sont réglables. Installer le fichier de configuration commun fourni, puis créer une automatisation et un assistant Texte par configuration d’intégration.','domain':'automation','homeassistant':{'min_version':'2026.10.0'},'input':inputs},'mode':'queued','max':100,'max_exceeded':'warning','trace':{'stored_traces':20},'variables':variables,'triggers':[{'trigger':'time_pattern','minutes':Input('scan_minutes'),'id':'scan'},{'trigger':'state','entity_id':Input('entities'),'id':'availability'},{'trigger':'homeassistant','event':'start','id':'start'},{'trigger':'event','event_type':['integration_watchdog_completed','integration_watchdog_wake'],'event_data':{'memory_entity':Input('memory')},'id':'completed'},{'trigger':'event','event_type':'integration_watchdog_rearm','event_data':{'memory_entity':Input('memory')},'id':'rearm'}],'conditions':[cond("{{ trigger is not defined or trigger.id != 'availability' or trigger.from_state is none or trigger.to_state is none or ((trigger.from_state.state in ['unknown','unavailable'] or trigger.from_state.attributes.get('restored',false)) != (trigger.to_state.state in ['unknown','unavailable'] or trigger.to_state.attributes.get('restored',false))) }}")],'actions':actions}
bp['blueprint']['source_url']='https://github.com/fbonelle/home-assistant-blueprints/blob/main/blueprints/automation/integration_watchdog/surveillance_integrations.yaml'
bp['blueprint']['author']='fbonelle'
save('surveillance_integrations.yaml',bp,f'# Version {VERSION} — marqueurs f=0 réservé, 1 admis, 2 démarré, >2 fin conservatrice.\n# Toutes les écritures internes passent par le même service comparé ; événements = réveils uniquement.\n')
save('scripts_rechargement_integrations.yaml',scripts,'# Services natifs communs ; installer une seule fois, aucun ajout par intégration.\n')
logging_automation={'id':'surveillance_journaux','alias':'Surveillance journaux','mode':'queued','max':1000,'triggers':[{'trigger':'event','event_type':'integration_watchdog_log'}],'actions':[{'action':'system_log.write','continue_on_error':True,'data':{'logger':'integration_watchdog','level':"{{ trigger.event.data.level if trigger.event.data.level in ['debug','info','warning'] else 'warning' }}",'message':'{{ trigger.event.data.message }}'}}]}
save('automatisation_admission.yaml',[admission,logging_automation],'# Admission courte et sérialisée ; seul point autorisé à démarrer le script commun.\n')
# Reuse only the user's fixture identifiers, not runtime code from the older version.
examples=yaml.safe_load((BASE/'examples.yaml').read_text())
for a in examples:a['use_blueprint']['input'].pop('dispatcher',None)
helpers=yaml.safe_load((BASE/'memoires.yaml').read_text())
logger={'logs':{'integration_watchdog':'debug'}}
save('automatisations_netatmo_overkiz.yaml',examples,'# Trois exemples ; autres instances ajoutées par le même formulaire.\n')
save('memoires_surveillance_integrations.yaml',helpers)
save('journalisation_surveillance.yaml',{'logger':logger,'system_log':{}})
save('package_surveillance_integrations.yaml',dict(script=scripts,automation=[admission,logging_automation],logger=logger,system_log={}), f'# Version {VERSION} — fichier de configuration commun à installer une seule fois.\n')
print(OUT)
