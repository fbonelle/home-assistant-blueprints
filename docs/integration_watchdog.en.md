# Integration monitoring and reload — 1.0.1

[Français](integration_watchdog.md) · **English** · [Home](../README.en.md)

This blueprint checks the entities you select and tries to reload their integration when it detects a problem. If retries are not enough, it sends a notification asking for intervention.

It uses the standard `homeassistant.reload_config_entry` action. The integration must support this action. **Home Assistant 2026.10 or later** is required; tests use **2026.10.4**. The blueprint form currently uses French labels; the setup table below includes them.

## 1. Install the two required files

### Shared configuration file

This file contains the scripts and automations shared by all monitoring automations. Install it once, regardless of how many integrations you want to monitor.

1. Create `/config/packages` if it does not exist.
2. Save [integration_watchdog.yaml](../packages/integration_watchdog.yaml) in that folder.
3. Enable packages in `configuration.yaml`:

```yaml
homeassistant:
  packages: !include_dir_named packages
```

If the file already contains a `homeassistant:` section, add `packages:` inside it instead of creating a second section. If packages are already enabled, use your configured folder.

The shared file does not create any monitoring automations for your integrations. Keep the names of the scripts and automations it contains.

### Blueprint

[Import the blueprint into Home Assistant](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fintegration_watchdog%2Fsurveillance_integrations.yaml)

Alternatively, open **Settings → Automations & scenes → Blueprints → Import blueprint** and paste [its GitHub URL](../blueprints/automation/integration_watchdog/surveillance_integrations.yaml).

For manual installation, copy the file to `/config/blueprints/automation/local/surveillance_integrations.yaml`.

Enable the **Uptime** integration if needed, check your Home Assistant configuration, then restart Home Assistant to load the shared file. Uptime provides the startup time used to let integrations connect before any retry.

## 2. Set up monitoring

### Create a Text helper

Open **Settings → Devices & services → Helpers → Create helper → Text**.

- Give it a name, such as “Netatmo monitoring history”.
- Set the minimum length to **0** and the maximum length to **255**.
- Select **Text** mode.

The automation fills this helper. It keeps the retry count and reload state across normal restarts. Do not edit its value manually.

### Fill in the form

Create an automation using **Surveillance et relance des intégrations — 1.0.1**, then select:

| French field label | What to select |
|---|---|
| Configuration de l’intégration à surveiller | The account or gateway to monitor. |
| Entités à surveiller | Active entities from that integration, such as a temperature sensor or thermostat. |
| Assistant Texte pour conserver l’historique | The Text helper you just created. |
| Capteur Uptime de Home Assistant | The sensor provided by the Uptime integration. |

Name the automation, adjust settings if needed and save. You can start with **Observer sans relancer l’intégration** (observe without reloading) and check the logs.

Create one monitoring automation per integration configuration. Separate accounts or gateways of the same integration need separate monitoring: TaHoma and Cozytouch, for example, are two separate Overkiz configurations.

## 3. Add more integrations

Create another Text helper and another automation from the same blueprint. No scripts need copying and no restart is required for this addition.

The blueprint does not impose a fixed limit on the number of monitored integrations. It supports **50 simultaneous reloads**. Additional requests wait for a free slot without consuming a retry.

The [Netatmo, TaHoma and Cozytouch examples](../examples/integration_watchdog/) contain fictional identifiers. Adapt them before use. Their `local/surveillance_integrations.yaml` path matches manual installation; after a GitHub import, use the actual blueprint path shown by Home Assistant.

## Choose suitable settings

| Setting | Default |
|---|---|
| Check interval | Every minute |
| Minimum outage duration before a retry | 5 minutes |
| Wait after Home Assistant starts | 10 minutes |
| Maximum retries for the same outage | 3 |
| Maximum retries in the last 24 hours | 6 |
| Time allowed to recover after a reload | 10 minutes |
| Normal operation required before confirming recovery | 3 minutes |
| Normal operation required before resetting the outage retry count | 30 minutes |
| Wait between retries | From 5 minutes to 1 hour, depending on previous failures |
| Alert if a reload has not finished | After 3 minutes |

Delays are evaluated during checks, so an action may wait until the next check. Resetting the outage retry count does not reset the limit for the last 24 hours.

**Entities in error.** You can wait until all selected entities are in error, or act when at least one has been in error long enough. `unavailable` means the entity cannot be reached. `unknown` means Home Assistant does not know its value: it triggers a retry only when the corresponding option is enabled, and never confirms recovery.

**Missing new data.** This check is off by default: its delay is **0**. Enable it for measurements sent regularly. Keep it at 0 for stationary covers or thermostats with infrequent changes, unless the integration provides a reliable measurement timestamp. Without that timestamp, the check measures reports received by Home Assistant rather than the actual age of the provider’s data.

**Recovery.** All monitored entities must work for the confirmation period, even when one entity in error is enough to trigger a retry. A brief improvement does not reset the retry count.

## Notifications and logs

By default, Home Assistant displays a notification when intervention is required and removes it after confirmed recovery. You can replace these actions with your preferred notifications in the form.

Useful events are written to the `integration_watchdog` logger. Detailed logging adds routine checks and can help diagnose a problem. A logging failure does not prevent incident notifications.

Exclusions, observation mode and additional conditions prevent new retries. They do not cancel a reload already in progress.

## If manual intervention is needed

If a reload does not finish, check the integration errors and script traces in Home Assistant. The alert does not cancel the operation: no further retry is sent until its end is known.

Once you have checked that it has finished, run **Surveillance — Confirmer la fin d’une relance** (confirm the end of a reload) and select its Text helper. This action is refused while the shared reload script is still running, even for another integration.

**Surveillance — Réinitialiser les tentatives pour une panne** (reset the outage retry count) allows another attempt after intervention. The last-24-hours count is preserved. Resetting is not allowed while a reload is pending.

## Important limitations

- Detection depends on the entities you select. A cloud outage may leave those entities available.
- Integrations are selected manually; there is no automatic discovery of all cloud integrations.
- Home Assistant must remain responsive for its automations to work. An abrupt shutdown may lose the most recent history update.
- Tests simulate provider calls; they do not prove that a real Netatmo or Overkiz outage will be repaired.

[How it works, tests and limitations](robustesse_integration_watchdog.en.md)

Home Assistant documentation: [packages](https://www.home-assistant.io/docs/configuration/packages/), [Text helpers](https://www.home-assistant.io/integrations/input_text/), [importing blueprints](https://www.home-assistant.io/docs/automation/using_blueprints/).
