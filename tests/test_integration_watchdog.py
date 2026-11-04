# SPDX-License-Identifier: GPL-3.0-only
"""Native Home Assistant 2026.10.4 schemas, templates, Script and worker scripts.

Only the external integration reload is replaced with a controlled service.
All Home Assistant files and state belong to pytest temporary directories.
"""
import asyncio
import copy
import json
from datetime import datetime,UTC,timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest
import pytest_asyncio

from homeassistant import core,loader
from homeassistant.bootstrap import async_load_base_functionality
from homeassistant.config_entries import ConfigEntries,ConfigEntry,ConfigEntryState
from homeassistant.components.automation.config import AUTOMATION_BLUEPRINT_SCHEMA,PLATFORM_SCHEMA
from homeassistant.components.blueprint.models import Blueprint,BlueprintInputs
from homeassistant.components.script.config import SCRIPT_ENTITY_SCHEMA
from homeassistant.components.input_text import CONFIG_SCHEMA as TEXT_SCHEMA
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er,issue_registry as ir,device_registry as dr
from homeassistant.helpers import entity as entity_helper
from homeassistant.helpers.script import Script
from homeassistant.setup import async_setup_component
from homeassistant.util.yaml import load_yaml

ROOT=Path(__file__).resolve().parent.parent
EXAMPLES=ROOT/'examples'/'integration_watchdog'
BLUEPRINT=ROOT/'blueprints'/'automation'/'integration_watchdog'/'surveillance_integrations.yaml'
PACKAGE=ROOT/'packages'/'integration_watchdog.yaml'
def load_package():return load_yaml(str(PACKAGE))

class Env:
    async def setup(self,path,actual=False):
        self.hass=core.HomeAssistant(str(path))
        self.hass.config.time_zone='Europe/Paris'
        self.hass.config_entries=ConfigEntries(self.hass,{})
        loader.async_setup(self.hass)
        assert await async_load_base_functionality(self.hass)
        self.now=int(datetime.now(UTC).timestamp())
        self.base=self.now
        self.clock_patch=patch.object(core,'time',SimpleNamespace(time=lambda:float(self.now)))
        self.clock_patch.start()
        self.entity_clock_patch=patch.object(entity_helper,'timer',lambda:float(self.now))
        self.entity_clock_patch.start()
        from homeassistant.util import dt as dt_util
        self.now_patch=patch.object(dt_util,'now',lambda time_zone=None:datetime.fromtimestamp(self.now,time_zone or UTC));self.now_patch.start()
        self.utcnow_patch=patch.object(dt_util,'utcnow',lambda:datetime.fromtimestamp(self.now,UTC));self.utcnow_patch.start()
        self.calls=[];self.modes={};self.gates={};self.monitors=[]
        self.presets=load_yaml(str(EXAMPLES/'automatisations_netatmo_overkiz.yaml'))
        self.rows=[dict(a['use_blueprint']['input'],worker='script.surveillance_recharger_instance') for a in self.presets]
        self.events=[]
        self.hass.bus.async_listen('integration_watchdog_completed',lambda event:self.events.append(event))
        self.entries={}
        registry=er.async_get(self.hass)
        for row in self.rows:
            entry=ConfigEntry(domain='netatmo' if row['name']=='Netatmo' else 'overkiz',
                entry_id=row['entry_id'],title=row['name'],version=1,minor_version=1,
                data={},options={},source='user',unique_id=row['entry_id'],
                discovery_keys={},subentries_data=None,state=ConfigEntryState.LOADED)
            self.hass.config_entries._entries[entry.entry_id]=entry
            self.entries[entry.entry_id]=entry
            for entity in row['entities']:
                domain,obj=entity.split('.',1)
                registered=registry.async_get_or_create(domain,entry.domain,entity,
                    suggested_object_id=obj,config_entry=entry)
                assert registered.entity_id==entity
                self.set(entity,'20')
        self.set('sensor.uptime',(datetime.fromtimestamp(self.now-10000,UTC)).isoformat())
        self.bp=Blueprint(load_yaml(str(BLUEPRINT)),
            expected_domain='automation',schema=AUTOMATION_BLUEPRINT_SCHEMA)
        assert await async_setup_component(self.hass,'input_text',load_yaml(str(EXAMPLES/'memoires_surveillance_integrations.yaml')))
        assert await async_setup_component(self.hass,'persistent_notification',{})
        assert await async_setup_component(self.hass,'system_log',{})
        assert await async_setup_component(self.hass,'logger',{'logger':{'logs':{'integration_watchdog':'debug'}}})
        for cfg in load_package()['script'].values():
            SCRIPT_ENTITY_SCHEMA(cfg)
        TEXT_SCHEMA(load_yaml(str(EXAMPLES/'memoires_surveillance_integrations.yaml')))
        async def reload(call):
            eid=call.data['entry_id'];self.calls.append(eid)
            mode=self.modes.get(eid,'fail')
            if mode=='hold':
                await self.gates.setdefault(eid,asyncio.Event()).wait()
            elif mode=='error': raise HomeAssistantError('Controlled backend failure')
            elif mode=='unload_failure': object.__setattr__(self.entries[eid],'state',ConfigEntryState.FAILED_UNLOAD)
            elif mode=='recover':
                row=next(r for r in self.rows if r['entry_id']==eid)
                for entity in row['entities']:self.set(entity,'20')
        self.hass.services.async_register('homeassistant','reload_config_entry',reload)
        self.reload_handler=reload
        assert await async_setup_component(self.hass,'script',{'script':load_package()['script']})
        shared=load_package()['automation']
        if actual:
            target=path/'blueprints'/'automation'/'local'/'surveillance_integrations.yaml'
            target.parent.mkdir(parents=True,exist_ok=True);target.write_text((BLUEPRINT).read_text())
            shared+=self.presets
        assert await async_setup_component(self.hass,'automation',{'automation':shared})
        self.hass.services.async_register('homeassistant','reload_config_entry',reload)
        await self.hass.async_start()
        await self.hass.async_block_till_done()
        await self.drain()
        return self

    def set(self,entity,value,age=0,attrs=None):
        self.hass.states.async_set(entity,value,attrs or {})
        state=self.hass.states.get(entity)
        stamp=datetime.fromtimestamp(self.now-age,UTC)
        state.last_changed=stamp;state.last_updated=stamp;state.last_reported=stamp
        return state

    def bad(self,index=0):
        for entity in self.rows[index]['entities']:self.set(entity,'unavailable',age=1000)

    def healthy(self,index=0):
        for entity in self.rows[index]['entities']:self.set(entity,'20')

    def record(self,index=0):
        text=self.hass.states.get(self.rows[index]['memory']).state
        try:return json.loads(text[4:]) if text.startswith('iw3:') else None
        except json.JSONDecodeError:return None

    async def write_record(self,index,data):
        text='iw3:'+json.dumps(data,separators=(',',':'))
        await self.hass.services.async_call('input_text','set_value',{'entity_id':self.rows[index]['memory'],'value':text},blocking=True)

    async def monitor(self,index=0,**overrides):
        preset=copy.deepcopy(self.presets[index])
        if 'integrations' in overrides:
            rows=overrides.pop('integrations')
            overrides.update({k:v for k,v in rows[0].items() if k!='worker'})
        preset['use_blueprint']['input'].update(overrides)
        args=BlueprintInputs(self.bp,preset);args.validate()
        raw=args.async_substitute()
        raw['actions'][0]['variables']['clock_ts']='{{ injected_clock | int }}'
        expanded=PLATFORM_SCHEMA(raw)
        script=Script(self.hass,expanded['actions'],preset['alias'],'automation',
            script_mode=expanded['mode'],variables=expanded['variables'])
        self.monitors.append(script)
        return script,preset

    async def tick(self,index=0,advance=0,monitor=None,trigger=None,**overrides):
        self.now+=advance
        if monitor is None:monitor=await self.monitor(index,**overrides)
        script,preset=monitor
        this=core.State('automation.'+preset['id'],'on',{'id':preset['id']})
        if trigger is None:
            event=next((e for e in self.events if e.data.get('memory_entity')==self.rows[index]['memory']),None)
            if event is not None:
                self.events.remove(event);trigger={'id':'completed','event':event}
            else:trigger={'id':'scan'}
        await script.async_run({'injected_clock':self.now,'this':this,'trigger':trigger},context=core.Context())
        await self.drain()
        return self.record(index)

    async def drain(self):
        for _ in range(20):await asyncio.sleep(0)

    def notices(self):
        from homeassistant.components.persistent_notification import DOMAIN
        return self.hass.data[DOMAIN]

    async def close(self):
        if getattr(self,'closed',False):return
        self.closed=True
        for gate in self.gates.values():gate.set()
        await self.drain()
        for script in self.monitors:await script.async_stop()
        await self.hass.async_stop()
        self.clock_patch.stop()
        self.entity_clock_patch.stop()
        self.now_patch.stop();self.utcnow_patch.stop()

@pytest_asyncio.fixture
async def env(tmp_path):
    e=await Env().setup(tmp_path)
    yield e
    await e.close()























@pytest.mark.asyncio
async def test_logging_avoids_healthy_scan_spam_and_has_a_detailed_mode(env,caplog):
    import logging
    with caplog.at_level(logging.DEBUG,logger='integration_watchdog'):
        await env.tick();count=len([r for r in caplog.records if r.name=='integration_watchdog'])
        await env.tick(advance=60)
        assert len([r for r in caplog.records if r.name=='integration_watchdog'])==count
        await env.tick(advance=60,detailed_logging=True)
        assert any(r.name=='integration_watchdog' and r.levelno==logging.DEBUG for r in caplog.records)

@pytest.mark.asyncio
async def test_logging_does_not_include_sensor_values(env,caplog):
    import logging
    env.set(env.rows[0]['entities'][0],'SENSITIVE_SENSOR_VALUE');await env.drain()
    with caplog.at_level(logging.DEBUG,logger='integration_watchdog'):await env.tick(detailed_logging=True)
    assert all('SENSITIVE_SENSOR_VALUE' not in r.getMessage() for r in caplog.records if r.name=='integration_watchdog')

@pytest.mark.asyncio
async def test_native_exclusion_prevents_reload(env):
    env.bad();await env.tick(excluded_instances=[{'entry_id':env.rows[0]['entry_id']}])
    assert env.calls==[]


@pytest.mark.asyncio
async def test_invalid_native_exclusion_is_notified(env):
    env.bad();await env.tick(excluded_instances=None)
    assert env.calls==[] and env.notices()

@pytest.mark.asyncio
async def test_native_schemas_and_healthy_monitor(env):
    for index in range(3):
        data=await env.tick(index)
        assert data is not None and data['i']==0
        assert len(env.hass.states.get(env.rows[index]['memory']).state)<=255
    assert env.calls==[]

@pytest.mark.asyncio
async def test_native_worker_dispatch_is_nonblocking(env):
    env.bad();eid=env.rows[0]['entry_id'];env.modes[eid]='hold'
    data=await env.tick()
    assert env.calls==[eid]
    assert data['s']=='running' and data['i']==1
    assert env.hass.states.get(env.rows[0]['worker']).state=='on'

@pytest.mark.asyncio
async def test_null_memory_is_a_configuration_notice(env):
    row=copy.deepcopy(env.rows[0]);row['memory']=None
    await env.tick(integrations=[row])
    assert env.calls==[] and env.notices()

@pytest.mark.asyncio
async def test_native_reauth_guard_prevents_reload(env):
    env.bad();row=env.rows[0]
    ir.async_create_issue(env.hass,'homeassistant','config_entry_reauth_netatmo_'+row['entry_id'],
        is_fixable=False,severity=ir.IssueSeverity.ERROR,translation_key='config_entry_reauth')
    data=await env.tick()
    assert data['s']=='auth' and env.calls==[]
    assert env.notices()

@pytest.mark.asyncio
async def test_failed_unload_is_notified(env):
    env.bad();env.modes[env.rows[0]['entry_id']]='unload_failure'
    await env.tick();data=await env.tick(advance=60)
    assert data['s']=='fatal'
    assert env.notices()

@pytest.mark.asyncio
@pytest.mark.parametrize('bad_value',[None,'3',0,-1,1.5,float('nan'),float('inf'),False,11])
async def test_invalid_attempt_count_is_notified_without_reloading(env,bad_value):
    env.bad();await env.tick(max_attempts=bad_value)
    assert env.calls==[] and env.notices()

@pytest.mark.asyncio
@pytest.mark.parametrize('key,value',[
 ('memory',None),('entry_id',123),('entities',None),
 ('max_age',None),('max_age',float('nan')),('stagger_seconds',-1),
 ('recovery_seconds',0),('policy','invalid'),('source_time_entity',123)])
async def test_invalid_rows_are_rejected_safely(env,key,value):
    row=copy.deepcopy(env.rows[0]);row[key]=value
    await env.tick(integrations=[row])
    assert env.calls==[] and env.notices()

@pytest.mark.asyncio
async def test_unavailable_uptime_alerts_and_does_not_reload(env):
    env.bad();env.set('sensor.uptime','unavailable');await env.tick()
    assert env.calls==[] and env.notices()

@pytest.mark.asyncio
async def test_initial_fatal_state_is_notified(env):
    env.bad();object.__setattr__(env.entries[env.rows[0]['entry_id']],'state',ConfigEntryState.MIGRATION_ERROR)
    data=await env.tick()
    assert data['s']=='fatal' and env.calls==[] and env.notices()

@pytest.mark.asyncio
async def test_autonomous_recovery_dismisses_alarm_after_stability(env):
    index=1;row=env.rows[index]
    object.__setattr__(env.entries[row['entry_id']],'state',ConfigEntryState.MIGRATION_ERROR)
    await env.tick(index)
    notice='integration_watchdog_'+row['entry_id']
    assert notice in env.notices()
    object.__setattr__(env.entries[row['entry_id']],'state',ConfigEntryState.LOADED)
    env.healthy(index)
    await env.tick(index,advance=60)
    for _ in range(3):data=await env.tick(index,advance=60)
    assert data['s']=='healthy' and data['k']==''
    assert notice not in env.notices() and env.calls==[]

@pytest.mark.asyncio
async def test_transient_recovery_does_not_declare_success(env):
    index=1;row=copy.deepcopy(env.rows[index]);row['stagger_seconds']=0
    env.bad(index);env.modes[row['entry_id']]='recover'
    await env.tick(index,integrations=[row])
    await env.tick(index,advance=60,integrations=[row])
    await env.tick(index,advance=60,integrations=[row])
    env.bad(index)
    data=await env.tick(index,advance=60,integrations=[row])
    assert data['s']!='healthy' and data['i']==1
    assert env.calls==[row['entry_id']]

@pytest.mark.asyncio
async def test_blocked_worker_alerts_while_other_workers_start(env):
    for i,row in enumerate(env.rows):env.bad(i);env.modes[row['entry_id']]='hold'
    monitors=[await env.monitor(i,integrations=[dict(row,stagger_seconds=0)]) for i,row in enumerate(env.rows)]
    await asyncio.gather(*(env.tick(i,monitor=m) for i,m in enumerate(monitors)))
    assert set(env.calls)=={r['entry_id'] for r in env.rows}
    assert all(env.hass.states.get(r['worker']).state=='on' for r in env.rows)
    env.now+=240
    for i,m in enumerate(monitors):
        data=await env.tick(i,monitor=m)
        assert data['s']=='timeout'
    assert len(env.calls)==3
    assert all('integration_watchdog_'+r['entry_id'] in env.notices() for r in env.rows)

@pytest.mark.asyncio
async def test_same_instance_is_not_reloaded_while_worker_is_active(env):
    env.bad();eid=env.rows[0]['entry_id'];env.modes[eid]='hold'
    for i in range(6):await env.tick(advance=60 if i else 0)
    assert env.calls==[eid] and env.record()['i']==1

@pytest.mark.asyncio
async def test_incident_budget_suspends_indefinite_cycles(env):
    index=1;row=dict(env.rows[index],stagger_seconds=0,recovery_seconds=180)
    env.bad(index)
    for _ in range(3):
        await env.tick(index,integrations=[row])
        await env.tick(index,advance=60,integrations=[row])
        data=await env.tick(index,advance=180,integrations=[row])
        if data['s']!='suspended':env.now=data['n']
    assert data['s']=='suspended' and len(env.calls)==3
    await env.tick(index,advance=86401,integrations=[row])
    assert len(env.calls)==3 and env.record(index)['s']=='suspended'

@pytest.mark.asyncio
async def test_rolling_24h_budget_does_not_reset_on_midnight(env):
    index=1;row=dict(env.rows[index],stagger_seconds=0)
    await env.tick(index)
    data=env.record(index);data.update(a=[env.now-100-i for i in range(6)],i=0,s='healthy',h=0)
    await env.write_record(index,data);env.bad(index)
    data=await env.tick(index,integrations=[row])
    assert data['s']=='limited' and env.calls==[]
    await env.tick(index,advance=86401,integrations=[row])
    assert env.calls==[row['entry_id']]

@pytest.mark.asyncio
async def test_full_history_stays_within_native_memory_capacity(env):
    for index,row in enumerate(env.rows):
        await env.tick(index)
        data=env.record(index)
        data.update(a=[env.now-i for i in range(6)],i=3,n=env.now+3600,p=env.now,f=env.now,h=env.now,t=env.now,s='suspended',k='suspended')
        await env.write_record(index,data)
        assert len(env.hass.states.get(row['memory']).state)<=255
        assert env.record(index)['a']==data['a']

@pytest.mark.asyncio
async def test_corrupted_memory_is_not_reset(env):
    row=env.rows[0]
    await env.hass.services.async_call('input_text','set_value',{'entity_id':row['memory'],'value':'iw3:{broken'},blocking=True)
    env.bad();await env.tick()
    assert env.hass.states.get(row['memory']).state=='iw3:{broken'
    assert env.calls==[] and env.notices()

@pytest.mark.asyncio
async def test_owner_prevents_reusing_same_memory_in_another_automation(env):
    await env.tick();monitor=await env.monitor();monitor[1]['id']='another_owner'
    env.bad();await env.tick(monitor=monitor)
    assert env.calls==[] and env.notices()

@pytest.mark.asyncio
async def test_long_gap_does_not_count_as_observed_stability(env):
    await env.tick(1);data=await env.tick(1,advance=1800)
    assert data['s']!='healthy' and data['h']==env.now



@pytest.mark.asyncio
async def test_worker_direct_invocation_still_checks_authentication(env):
    row=env.rows[0];env.bad()
    ir.async_create_issue(env.hass,'homeassistant','config_entry_reauth_netatmo_'+row['entry_id'],
        is_fixable=False,severity=ir.IssueSeverity.ERROR,translation_key='config_entry_reauth')
    await env.hass.services.async_call('script','turn_on',{'entity_id':row['worker'],'variables':{'expected_entry_id':row['entry_id']}},blocking=True)
    await env.drain()
    assert env.calls==[]

@pytest.mark.asyncio
async def test_restart_restores_the_reservation_and_budget(env,tmp_path):
    env.bad();await env.tick();before=env.record()
    assert before['i']==1 and len(before['a'])==1
    await env.close()
    restarted=await Env().setup(tmp_path)
    try:
        restored=restarted.record()
        assert restored['i']==1 and restored['a']==before['a']
        restarted.set('sensor.uptime',datetime.fromtimestamp(restarted.now,UTC).isoformat())
        await restarted.tick()
        assert restarted.record()['i']==1 and restarted.calls==[]
    finally:await restarted.close()

@pytest.mark.asyncio
async def test_failed_notification_is_retried_before_acknowledgement(env):
    row=env.rows[0];env.bad()
    object.__setattr__(env.entries[row['entry_id']],'state',ConfigEntryState.FAILED_UNLOAD)
    sent=[]
    async def notify(call):
        sent.append(call.data)
        if len(sent)==1:raise HomeAssistantError('Controlled notification failure')
    env.hass.services.async_register('test','notify',notify)
    args={'failure_actions':[{'action':'test.notify'}]}
    with pytest.raises(HomeAssistantError):await env.tick(**args)
    assert env.record()['k']==''
    await env.tick(advance=60,**args)
    assert len(sent)==2 and env.record()['k']=='fatal'

@pytest.mark.asyncio
async def test_maintenance_stops_interventions_but_not_observation(env):
    env.bad()
    data=await env.tick(additional_conditions=[{'condition':'template','value_template':'{{ false }}'}])
    assert data['s']=='paused' and env.calls==[]

@pytest.mark.asyncio
async def test_native_retry_is_respected(env):
    env.bad();object.__setattr__(env.entries[env.rows[0]['entry_id']],'state',ConfigEntryState.SETUP_RETRY)
    data=await env.tick()
    assert data['s']=='native' and env.calls==[]

@pytest.mark.asyncio
async def test_long_native_retry_alerts_without_forcing_a_reload(env):
    env.bad();object.__setattr__(env.entries[env.rows[0]['entry_id']],'state',ConfigEntryState.SETUP_RETRY)
    await env.tick()
    data=await env.tick(advance=1801)
    assert data['s']=='native' and data['k']=='native' and env.calls==[] and env.notices()

@pytest.mark.asyncio
async def test_native_retry_deadline_is_not_reused_as_a_recovery_pause(env):
    env.bad();entry=env.entries[env.rows[0]['entry_id']]
    object.__setattr__(entry,'state',ConfigEntryState.SETUP_RETRY);await env.tick()
    object.__setattr__(entry,'state',ConfigEntryState.LOADED);data=await env.tick(advance=60)
    assert data['s']=='running' and len(env.calls)==1

@pytest.mark.asyncio
async def test_disabled_entry_is_respected(env):
    from homeassistant.config_entries import ConfigEntryDisabler
    env.bad();object.__setattr__(env.entries[env.rows[0]['entry_id']],'disabled_by',ConfigEntryDisabler.USER)
    data=await env.tick()
    assert data['s']=='disabled' and env.calls==[]

@pytest.mark.asyncio
async def test_report_during_reload_alone_is_not_sufficient(env):
    env.bad();env.modes[env.rows[0]['entry_id']]='recover'
    await env.tick();await env.tick(advance=60)
    for _ in range(4):data=await env.tick(advance=60)
    assert data['s']=='verify' and data['h']==0 and len(env.calls)==1

@pytest.mark.asyncio
async def test_post_reload_fresh_report_and_stability_are_required(env):
    env.bad();env.modes[env.rows[0]['entry_id']]='recover'
    await env.tick();await env.tick(advance=60)
    env.now+=60;env.healthy();await env.drain()
    await env.tick()
    for _ in range(3):data=await env.tick(advance=60)
    assert data['s']=='healthy' and data['i']==1
    assert len(env.calls)==1

@pytest.mark.asyncio
async def test_real_source_timestamp_can_detect_frozen_data(env):
    env.set('sensor.source_time',datetime.fromtimestamp(env.now-3600,UTC).isoformat())
    row=dict(env.rows[0],source_time_entity='sensor.source_time')
    await env.tick(integrations=[row])
    assert env.calls==[row['entry_id']]

@pytest.mark.asyncio
async def test_invalid_source_timestamp_is_not_reloaded_blindly(env):
    env.set('sensor.source_time','unknown')
    row=dict(env.rows[0],source_time_entity='sensor.source_time')
    data=await env.tick(integrations=[row])
    assert data['s']=='fatal' and env.calls==[] and env.notices()

@pytest.mark.asyncio
async def test_quick_relapse_keeps_incident_budget(env):
    index=1;row=dict(env.rows[index],stagger_seconds=0)
    env.bad(index);env.modes[row['entry_id']]='recover'
    await env.tick(index,integrations=[row]);await env.tick(index,advance=60,integrations=[row])
    for _ in range(3):data=await env.tick(index,advance=60,integrations=[row])
    assert data['s']=='healthy' and data['i']==1
    env.bad(index);await env.drain()
    data=await env.tick(index,advance=60,integrations=[row])
    assert data['i']==2 and len(env.calls)==2

@pytest.mark.asyncio
async def test_stable_recovery_rearms_incident_but_keeps_daily_history(env):
    index=1;row=dict(env.rows[index],stagger_seconds=0)
    env.bad(index);env.modes[row['entry_id']]='recover'
    await env.tick(index,integrations=[row]);await env.tick(index,advance=60,integrations=[row])
    for _ in range(31):data=await env.tick(index,advance=60,integrations=[row])
    assert data['s']=='healthy' and data['i']==0 and len(data['a'])==1


@pytest.mark.asyncio
async def test_simultaneous_supervision_runs_do_not_duplicate_requests(env):
    env.bad();monitor=await env.monitor()
    await asyncio.gather(env.tick(monitor=monitor),env.tick(monitor=monitor))
    assert len(env.calls)==1 and env.record()['i']==1 and len(env.record()['a'])==1




@pytest.mark.asyncio
async def test_actual_automation_entity_loads_blueprint_and_dispatches_worker(env,tmp_path):
    target=tmp_path/'blueprints'/'automation'/'local'/'surveillance_integrations.yaml'
    target.parent.mkdir(parents=True)
    target.write_text((BLUEPRINT).read_text())
    from homeassistant.components.automation import _async_process_config
    from homeassistant.helpers.entity_component import DATA_INSTANCES
    from homeassistant.components.automation.config import async_validate_config
    validated=await async_validate_config(env.hass,{'automation':load_package()['automation']+env.presets})
    await _async_process_config(env.hass,validated,env.hass.data[DATA_INSTANCES]['automation'])
    await env.hass.async_block_till_done()
    # Keep the external integration boundary mocked even if another component
    # has registered the native core service while setting up automation.
    env.hass.services.async_register('homeassistant','reload_config_entry',env.reload_handler)
    entity=next(s.entity_id for s in env.hass.states.async_all('automation') if s.attributes.get('id')==env.presets[0]['id'])
    env.bad();env.modes[env.rows[0]['entry_id']]='hold';await env.drain()
    await env.hass.services.async_call('automation','trigger',{'entity_id':entity},blocking=True)
    await env.drain()
    assert env.calls==[env.rows[0]['entry_id']]
    await env.hass.services.async_call('automation','trigger',{'entity_id':entity},blocking=True)
    await env.drain()
    assert len(env.calls)==1 and env.record()['i']==1

async def add_automation_entities(env,tmp_path):
    target=tmp_path/'blueprints'/'automation'/'local'/'surveillance_integrations.yaml'
    target.parent.mkdir(parents=True,exist_ok=True)
    target.write_text((BLUEPRINT).read_text())
    from homeassistant.components.automation import _async_process_config
    from homeassistant.helpers.entity_component import DATA_INSTANCES
    from homeassistant.components.automation.config import async_validate_config
    validated=await async_validate_config(env.hass,{'automation':load_package()['automation']+env.presets})
    await _async_process_config(env.hass,validated,env.hass.data[DATA_INSTANCES]['automation'])
    await env.hass.async_block_till_done()
    env.hass.services.async_register('homeassistant','reload_config_entry',env.reload_handler)
    return {s.attributes.get('id'):s.entity_id for s in env.hass.states.async_all('automation')}

@pytest.mark.asyncio
async def test_fourth_unlisted_integration_needs_only_helper_and_form_inputs(env):
    from homeassistant.components.input_text import InputText,STORAGE_FIELDS
    from homeassistant.helpers.entity_component import DATA_INSTANCES
    import probatio
    cfg=probatio.Schema(STORAGE_FIELDS)({'name':'Surveillance exemple supplémentaire','max':255})
    helper=InputText.from_storage(dict(cfg,id='surveillance_quatrieme'))
    helper.entity_id='input_text.surveillance_quatrieme'
    await env.hass.data[DATA_INSTANCES]['input_text'].async_add_entities([helper])
    eid='fourth_unlisted_entry';entity='sensor.quatrieme_temperature'
    entry=ConfigEntry(domain='tuya',entry_id=eid,title='Quatrième intégration',version=1,minor_version=1,data={},options={},source='user',unique_id=eid,discovery_keys={},subentries_data=None,state=ConfigEntryState.LOADED)
    env.hass.config_entries._entries[eid]=entry;env.entries[eid]=entry
    er.async_get(env.hass).async_get_or_create('sensor','tuya',entity,suggested_object_id='quatrieme_temperature',config_entry=entry)
    row={'name':'Quatrième intégration','entry_id':eid,'entities':[entity],'memory':helper.entity_id,'uptime_entity':'sensor.uptime','max_age':0,'stagger_seconds':0}
    env.rows.append(row)
    env.presets.append({'id':'surveillance_quatrieme','alias':'Surveillance — Quatrième','use_blueprint':{'path':'local/surveillance_integrations.yaml','input':row}})
    scripts_before=set(env.hass.states.async_entity_ids('script'))
    env.bad(3)
    data=await env.tick(3)
    assert env.calls==[eid] and data['i']==1
    assert set(env.hass.states.async_entity_ids('script'))==scripts_before
    assert not any('quatrieme' in s for s in scripts_before)
    assert env.hass.states.get(helper.entity_id).attributes['editable'] is True

@pytest.mark.asyncio
async def test_worker_backend_error_still_opens_verification_without_claiming_success(env):
    env.bad();env.modes[env.rows[0]['entry_id']]='error'
    await env.tick();data=await env.tick(advance=60)
    assert data['s']=='verify' and data['i']==1 and data['p']==0
    assert env.calls==[env.rows[0]['entry_id']]

@pytest.mark.asyncio
@pytest.mark.parametrize('change',[{'owner_id':'wrong'},{'reservation':1}])
async def test_wrong_completion_cannot_unlock_a_pending_reload(env,change):
    env.bad();env.modes[env.rows[0]['entry_id']]='hold';await env.tick()
    before=env.record();payload={'owner_id':before['o'],'reservation':before['p']};payload.update(change)
    data=await env.tick(advance=60,trigger={'id':'completed','event':core.Event('integration_watchdog_completed',payload)})
    assert data['p']==before['p'] and data['i']==1 and data['s']=='running' and len(env.calls)==1

@pytest.mark.asyncio
async def test_lost_completion_event_is_recovered_from_durable_memory(env):
    env.bad();await env.tick();env.events.clear()
    data=await env.tick(advance=240)
    assert data['s']=='verify' and data['p']==0 and data['f']>2 and len(env.calls)==1

@pytest.mark.asyncio
async def test_manual_confirmation_refuses_any_still_running_shared_worker(env):
    env.bad();env.modes[env.rows[0]['entry_id']]='hold';await env.tick()
    events=[];env.hass.bus.async_listen('integration_watchdog_wake',lambda e:events.append(e))
    await env.hass.services.async_call('script','surveillance_confirmer_fin',{'memory':env.rows[0]['memory']},blocking=True)
    await env.drain();assert events==[]

@pytest.mark.asyncio
async def test_manual_rearm_preserves_daily_history_and_refuses_pending_requests(env):
    index=1;await env.tick(index)
    before=env.record(index);before.update(i=3,a=[env.now-100],s='suspended')
    await env.write_record(index,before)
    trigger={'id':'rearm','event':core.Event('integration_watchdog_rearm',{'memory_entity':env.rows[index]['memory']})}
    data=await env.tick(index,trigger=trigger)
    assert data['i']==0 and data['a']==before['a']
    env.bad(index);env.modes[env.rows[index]['entry_id']]='hold'
    row=dict(env.rows[index],stagger_seconds=0)
    await env.tick(index,integrations=[row]);before=env.record(index)
    data=await env.tick(index,trigger=trigger,integrations=[row])
    assert data['i']==before['i']==1 and data['p']==before['p']

@pytest.mark.asyncio
async def test_package_and_form_are_generic(env):
    package=load_package()
    assert len(package['automation'])==2 and 'input_text' not in package
    assert package['script']==load_package()['script']
    worker=str(package['script']['surveillance_recharger_instance'])
    assert all(row['entry_id'] not in worker for row in env.rows)
    assert 'template' not in package
    form=env.bp.data['blueprint']['input']['surveillance']['input']
    assert all(k not in form for k in ['worker','health_guard','integrations'])
    assert all(k in form for k in ['entry_id','entities','memory'])

@pytest.mark.asyncio
async def test_actual_automation_consumes_fast_completion_in_its_queue(env,tmp_path):
    entities=await add_automation_entities(env,tmp_path)
    env.bad();await env.drain()
    await env.hass.services.async_call('automation','trigger',{'entity_id':entities[env.presets[0]['id']]},blocking=True)
    await env.hass.async_block_till_done()
    data=env.record()
    assert data['p']==0 and data['f']>0 and data['s']=='verify' and data['i']==1
    assert len(env.calls)==1

@pytest.mark.asyncio
async def test_actual_availability_trigger_resets_stability_without_a_probe(env,tmp_path):
    entities=await add_automation_entities(env,tmp_path)
    target=entities[env.presets[1]['id']]
    await env.hass.services.async_call('automation','trigger',{'entity_id':target},blocking=True)
    await env.hass.async_block_till_done()
    data=env.record(1);data['h']-=179
    await env.write_record(1,data)
    entity=env.rows[1]['entities'][0]
    env.set(entity,'unavailable')
    await env.hass.async_block_till_done()
    assert env.record(1)['h']==0
    env.set(entity,'20');await env.hass.async_block_till_done()
    assert env.record(1)['h']>=data['h']+170
    assert env.record(1)['s']!='healthy' and env.calls==[]

@pytest.mark.asyncio
async def test_actual_value_changes_do_not_reset_availability_stability(env,tmp_path):
    entities=await add_automation_entities(env,tmp_path)
    target=entities[env.presets[1]['id']]
    await env.hass.services.async_call('automation','trigger',{'entity_id':target},blocking=True)
    await env.hass.async_block_till_done()
    data=env.record(1);data['h']-=100
    await env.write_record(1,data)
    env.set(env.rows[1]['entities'][0],'30');await env.hass.async_block_till_done()
    assert env.record(1)['h']==data['h']

@pytest.mark.asyncio
async def test_repair_completion_cannot_unlock_a_still_running_dispatcher(env):
    env.bad();env.modes[env.rows[0]['entry_id']]='hold';await env.tick()
    before=env.record()
    event=core.Event('integration_watchdog_completion_repair',{'owner_id':before['o'],'reservation':before['p']})
    data=await env.tick(advance=60,trigger={'id':'completed','event':event})
    assert data['p']==before['p'] and data['s']=='running' and len(env.calls)==1

@pytest.mark.asyncio
async def test_actual_manual_rearm_is_processed_by_the_owner_automation(env,tmp_path):
    entities=await add_automation_entities(env,tmp_path)
    target=entities[env.presets[1]['id']]
    await env.hass.services.async_call('automation','trigger',{'entity_id':target},blocking=True)
    await env.hass.async_block_till_done()
    before=env.record(1);before.update(i=3,a=[env.now-100],s='suspended')
    await env.write_record(1,before)
    await env.hass.services.async_call('script','surveillance_rearmer_incident',{'memory':env.rows[1]['memory']},blocking=True)
    await env.hass.async_block_till_done()
    assert env.record(1)['i']==0 and env.record(1)['a']==before['a']

@pytest.mark.asyncio
async def test_uptime_reconstruction_never_releases_pending_reload(env):
    env.bad();env.modes[env.rows[0]['entry_id']]='hold';await env.tick()
    before=env.record();env.now+=10
    env.set('sensor.uptime',datetime.fromtimestamp(env.now,UTC).isoformat())
    for advance in [60,1000]:
        data=await env.tick(advance=advance)
        assert data['p']==before['p'] and len(env.calls)==1

@pytest.mark.asyncio
async def test_full_worker_pool_defers_without_blocking_or_spending_budget(env):
    from homeassistant.helpers.entity_component import DATA_INSTANCES
    worker=env.hass.data[DATA_INSTANCES]['script'].get_entity('script.surveillance_recharger_instance')
    worker.script.max_runs=1
    env.bad();env.modes[env.rows[0]['entry_id']]='hold';await env.tick()
    env.bad(1);row=dict(env.rows[1],stagger_seconds=0)
    await asyncio.wait_for(env.tick(1,integrations=[row]),2)
    data=env.record(1)
    assert data['p']==0 and data['i']==0 and data['a']==[] and len(env.calls)==1
    env.gates[env.rows[0]['entry_id']].set();await env.drain()
    await env.tick(1,advance=61,integrations=[row])
    assert env.calls==[env.rows[0]['entry_id'],env.rows[1]['entry_id']]
    assert env.record(1)['i']==1

@pytest.mark.asyncio
async def test_logging_error_and_missing_service_do_not_suppress_alerts(env):
    object.__setattr__(env.entries[env.rows[0]['entry_id']],'state',ConfigEntryState.FAILED_UNLOAD)
    async def bad_log(call):raise HomeAssistantError('Controlled log failure')
    env.hass.services.async_register('system_log','write',bad_log)
    await env.tick()
    notice='integration_watchdog_'+env.rows[0]['entry_id']
    assert notice in env.notices() and env.record()['k']=='fatal'
    env.hass.services.async_remove('system_log','write')
    data=env.record();data['k']='';await env.write_record(0,data)
    await env.tick(advance=60)
    assert notice in env.notices() and env.record()['k']=='fatal'

@pytest.mark.asyncio
async def test_configuration_notification_error_preserves_completion(env):
    env.bad();await env.tick()
    async def bad_notice(call):raise HomeAssistantError('Controlled auxiliary failure')
    env.hass.services.async_register('test','failure',bad_notice)
    with pytest.raises(HomeAssistantError):
        await env.tick(advance=60,configuration_resolved_actions=[{'action':'test.failure'}])
    assert env.record()['p']==0 and env.record()['s']=='verify'
    assert (await env.tick(advance=240))['s']!='timeout'

@pytest.mark.asyncio
async def test_exclusion_preserves_completion_and_budget(env):
    env.bad();await env.tick()
    await env.tick(advance=60,excluded_instances=[{'entry_id':env.rows[0]['entry_id']}])
    data=env.record()
    assert data['p']==0 and data['i']==1 and len(data['a'])==1
    assert (await env.tick(advance=240))['s']!='timeout'

@pytest.mark.asyncio
async def test_invalid_minimum_is_reported_without_claiming_memory(env):
    from homeassistant.helpers.entity_component import DATA_INSTANCES
    helper=env.hass.data[DATA_INSTANCES]['input_text'].get_entity(env.rows[0]['memory'])
    helper._attr_native_min=255;helper.async_write_ha_state();env.bad()
    await env.tick()
    assert env.notices() and env.record() is None and not env.calls

@pytest.mark.asyncio
async def test_writer_checks_actual_write_and_does_not_overwrite_newer_state(env):
    await env.tick();before=env.hass.states.get(env.rows[0]['memory']).state
    response=await env.hass.services.async_call('script','surveillance_ecrire_memoire',{'memory_entity':env.rows[0]['memory'],'expected':'stale','value':'wrong'},blocking=True,return_response=True)
    assert response['ok'] is False and response['conflict'] is True
    assert env.hass.states.get(env.rows[0]['memory']).state==before
    from homeassistant.helpers.entity_component import DATA_INSTANCES
    helper=env.hass.data[DATA_INSTANCES]['input_text'].get_entity(env.rows[0]['memory'])
    helper._attr_native_min=255
    response=await env.hass.services.async_call('script','surveillance_ecrire_memoire',{'memory_entity':env.rows[0]['memory'],'expected':before,'value':'too short'},blocking=True,return_response=True)
    assert response['ok'] is False and response['conflict'] is False
    assert env.hass.states.get(env.rows[0]['memory']).state==before

@pytest.mark.asyncio
async def test_subsecond_pre_completion_reports_are_not_fresh(env):
    env.bad();env.modes[env.rows[0]['entry_id']]='hold';await env.tick()
    env.now+=60
    for entity in env.rows[0]['entities']:
        state=env.set(entity,'20');state.last_reported=datetime.fromtimestamp(env.now+0.2,UTC)
    env.now+=0.9;env.gates[env.rows[0]['entry_id']].set();await env.drain()
    await env.tick()
    for _ in range(4):data=await env.tick(advance=60)
    assert data['s']=='verify' and data['h']==0
    env.healthy();await env.tick(advance=1)
    for _ in range(3):data=await env.tick(advance=60)
    assert data['s']=='healthy'

@pytest.mark.asyncio
async def test_replaying_request_and_worker_does_not_repeat_reload(env):
    env.bad();env.modes[env.rows[0]['entry_id']]='hold';await env.tick()
    d=env.record()
    args={'entry_id':env.rows[0]['entry_id'],'memory_entity':env.rows[0]['memory'],'owner_id':d['o'],'entry_key':d['e'],'reservation':d['p']}
    for _ in range(3):
        env.hass.bus.async_fire('integration_watchdog_request',dict(args,max_attempts=3,max_daily=6))
        await env.hass.services.async_call('script','turn_on',{'entity_id':'script.surveillance_recharger_instance','variables':args},blocking=True)
    await env.drain()
    assert env.calls==[env.rows[0]['entry_id']] and env.record()['i']==1 and len(env.record()['a'])==1

@pytest.mark.asyncio
async def test_duplicate_supervisor_is_detected_and_never_admitted_twice(env):
    from homeassistant.components.input_text import InputText,STORAGE_FIELDS
    from homeassistant.helpers.entity_component import DATA_INSTANCES
    import probatio
    cfg=probatio.Schema(STORAGE_FIELDS)({'name':'Copie mémoire','max':255})
    helper=InputText.from_storage(dict(cfg,id='surveillance_copie'));helper.entity_id='input_text.surveillance_copie'
    await env.hass.data[DATA_INSTANCES]['input_text'].async_add_entities([helper])
    env.bad();env.modes[env.rows[0]['entry_id']]='hold'
    a=await env.monitor();b=await env.monitor(memory=helper.entity_id);b[1]['id']='another_supervisor'
    await asyncio.gather(env.tick(monitor=a),env.tick(monitor=b))
    await env.tick(monitor=a);await env.tick(monitor=b)
    assert len(env.calls)<=1 and env.notices()

@pytest.mark.asyncio
async def test_notification_ack_preserves_worker_completion_written_during_notification(env):
    env.bad();env.modes[env.rows[0]['entry_id']]='hold';await env.tick()
    async def slow_notify(call):
        env.gates[env.rows[0]['entry_id']].set();await env.drain()
        assert env.record()['f']>2
    env.hass.services.async_register('test','slow_notify',slow_notify)
    await env.tick(advance=240,failure_actions=[{'action':'test.slow_notify'}])
    assert env.record()['f']>2
    data=await env.tick(advance=60)
    assert data['p']==0 and data['s']=='verify'

@pytest.mark.asyncio
async def test_default_notifications_have_all_template_variables_and_no_template_warnings(env,caplog):
    object.__setattr__(env.entries[env.rows[0]['entry_id']],'state',ConfigEntryState.FAILED_UNLOAD)
    await env.tick()
    assert not any('Template variable warning' in r.message for r in caplog.records)
    notice=env.notices()['integration_watchdog_'+env.rows[0]['entry_id']]
    assert 'Netatmo' in str(notice) and 'failed_unload' in str(notice)

@pytest.mark.asyncio
async def test_existing_helper_cannot_be_retargeted_to_another_instance(env):
    await env.tick();before=env.record()
    row=dict(env.rows[1],memory=env.rows[0]['memory'])
    await env.tick(1,integrations=[row])
    assert env.record()==before and env.notices() and not env.calls

@pytest.mark.asyncio
async def test_capacity_all_memory_fields_with_six_attempts_is_checked_by_real_planner(env):
    await env.tick();d=env.record()
    d.update(a=[env.now-i for i in range(6)],i=3,n=env.now+3600,p=env.now*1000000,f=2,h=env.now,t=env.now,s='timeout',k='timeout')
    await env.write_record(0,d)
    data=await env.tick(advance=60)
    assert data['i']==3 and len(data['a'])==6 and data['p']>0
    assert len(env.hass.states.get(env.rows[0]['memory']).state)<=255

@pytest.mark.asyncio
async def test_clock_rollback_stops_without_resetting_budgets(env):
    env.bad();await env.tick();before=env.record();env.now-=120
    await env.tick()
    assert env.record()==before and len(env.calls)==1 and env.notices()

@pytest.mark.asyncio
async def test_disabled_admission_is_reported_without_pending_reservation(env):
    await env.hass.services.async_call('automation','turn_off',{'entity_id':'automation.surveillance_admission'},blocking=True)
    env.bad();await env.tick()
    assert env.record() is None and not env.calls and env.notices()

@pytest.mark.asyncio
async def test_legacy_migration_preserves_daily_and_incident_budgets(env):
    legacy={'v':2,'o':'w_'+env.presets[0]['id'],'a':[env.now-100],'i':2,'n':0,'p':0,'f':0,'h':0,'t':env.now,'s':'suspended','k':'suspended'}
    await env.hass.services.async_call('input_text','set_value',{'entity_id':env.rows[0]['memory'],'value':'iw2:'+json.dumps(legacy,separators=(',',':'))},blocking=True)
    await env.tick()
    d=env.record()
    assert d['v']==3 and d['i']==2 and d['a']==legacy['a'] and d['e'].startswith('e_')

@pytest.mark.asyncio
async def test_fifty_one_real_native_requests_admit_fifty_and_defer_one(env):
    from homeassistant.components.input_text import InputText,STORAGE_FIELDS
    from homeassistant.helpers.entity_component import DATA_INSTANCES
    import probatio
    for number in range(48):
        slug='surveillance_stress_'+str(number)
        cfg=probatio.Schema(STORAGE_FIELDS)({'name':slug,'max':255})
        helper=InputText.from_storage(dict(cfg,id=slug));helper.entity_id='input_text.'+slug
        await env.hass.data[DATA_INSTANCES]['input_text'].async_add_entities([helper])
        eid='stress_entry_'+str(number);entity='sensor.stress_'+str(number)
        entry=ConfigEntry(domain='overkiz',entry_id=eid,title=slug,version=1,minor_version=1,data={},options={},source='user',unique_id=eid,discovery_keys={},subentries_data=None,state=ConfigEntryState.LOADED)
        env.hass.config_entries._entries[eid]=entry;env.entries[eid]=entry
        er.async_get(env.hass).async_get_or_create('sensor','overkiz',entity,suggested_object_id='stress_'+str(number),config_entry=entry)
        row={'name':slug,'entry_id':eid,'entities':[entity],'memory':helper.entity_id,'uptime_entity':'sensor.uptime','max_age':0,'stagger_seconds':0}
        env.rows.append(row);env.presets.append({'id':slug,'alias':slug,'use_blueprint':{'path':'local/surveillance_integrations.yaml','input':row}})
    for index,row in enumerate(env.rows):env.bad(index);env.modes[row['entry_id']]='hold'
    monitors=[await env.monitor(i,stagger_seconds=0) for i in range(51)]
    await asyncio.wait_for(asyncio.gather(*(env.tick(i,monitor=m) for i,m in enumerate(monitors))),10)
    async def settled():
        while not (len(env.calls)==50 and sum(env.record(i)['p']==0 for i in range(51))==1):await asyncio.sleep(0.001)
    await asyncio.wait_for(settled(),5)
    assert len(set(env.calls))==50
    records=[env.record(i) for i in range(51)]
    assert sum(d['i'] for d in records)==50 and sum(len(d['a']) for d in records)==50
    assert sum(d['s']=='deferred' for d in records)==1

@pytest.mark.asyncio
async def test_actual_restart_recovers_interrupted_work_without_refunding_budget(env,tmp_path):
    env.bad();env.modes[env.rows[0]['entry_id']]='hold';await env.tick()
    before=env.record()
    await env.hass.services.async_call('script','turn_off',{'entity_id':'script.surveillance_recharger_instance'},blocking=True)
    assert env.record()['p']>0 and env.record()['f']==2
    await env.close()
    restarted=await Env().setup(tmp_path,actual=True)
    try:
        await restarted.hass.async_block_till_done()
        d=restarted.record()
        assert d['p']==0 and d['i']==before['i']==1 and d['a']==before['a']
        assert d['s']=='verify' and restarted.calls==[]
    finally:await restarted.close()

@pytest.mark.asyncio
async def test_automation_disabled_during_finish_recovers_from_durable_result(env,tmp_path):
    targets=await add_automation_entities(env,tmp_path)
    target=targets[env.presets[0]['id']]
    env.bad();env.modes[env.rows[0]['entry_id']]='hold';await env.drain()
    await env.hass.services.async_call('automation','trigger',{'entity_id':target},blocking=True)
    await env.drain();assert len(env.calls)==1
    await env.hass.services.async_call('automation','turn_off',{'entity_id':target},blocking=True)
    env.gates[env.rows[0]['entry_id']].set();await env.drain()
    assert env.record()['p']>0 and env.record()['f']>2
    await env.hass.services.async_call('automation','turn_on',{'entity_id':target},blocking=True)
    await env.hass.services.async_call('automation','trigger',{'entity_id':target},blocking=True)
    await env.hass.async_block_till_done()
    assert env.record()['p']==0 and env.record()['i']==1 and env.record()['s']=='verify'

@pytest.mark.asyncio
async def test_package_merge_preserves_all_script_field_selectors(env):
    """Exercise HA's package merge, which drops empty mapping leaves."""
    from homeassistant.config import merge_packages_config
    from homeassistant.components.script.config import async_validate_config_item
    package=load_package();errors=[]
    base={'script':{'existing_example':{'alias':'Existing script','sequence':[{'delay':1}]}}}
    merged=await merge_packages_config(env.hass,base,{'integration_watchdog':package},lambda *args:errors.append(args[-1]))
    assert not errors
    assert 'existing_example' in merged['script']
    for key in package['script']:
        result=await async_validate_config_item(env.hass,key,merged['script'][key])
        assert result is not None and result.validation_error is None
