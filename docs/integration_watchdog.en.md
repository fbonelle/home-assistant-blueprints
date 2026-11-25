# Integration watchdog — 2026.11.3.1

[Français](integration_watchdog.md) · **English** · [Home](../README.en.md)

This blueprint checks the entities you select and tries to reload their integration when it detects a problem. If retries are not enough, it sends a notification asking for intervention.

It uses the standard `homeassistant.reload_config_entry` action. The integration must support this action. Home Assistant **2026.8 or later** is required; tests run on the tested release and on this minimum release (see the [README](../README.en.md#development)). The blueprint form currently uses French labels; the setup table below includes them.

## 1. Import the blueprint

[Import the blueprint into Home Assistant](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fintegration_watchdog%2Fintegration_watchdog.yaml)

Alternatively, open **Settings → Automations & scenes → Blueprints → Import blueprint** and paste [its GitHub URL](../blueprints/automation/integration_watchdog/integration_watchdog.yaml). For manual installation, copy the file to `/config/blueprints/automation/local/integration_watchdog.yaml`.

This is the only file to install: no configuration file, no script and no restart. Enable the **Uptime** integration if needed; it provides the startup time used to let integrations connect before any retry.

## 2. Set up monitoring

### Create a Text helper

Open **Settings → Devices & services → Helpers → Create helper → Text**.

- Give it a name, such as “Netatmo monitoring history”.
- Set the minimum length to **0** and the maximum length to **255**.
- Select **Text** mode.

The automation fills this helper. It keeps the retry count and reload state across normal restarts. Do not edit its value manually.

### Fill in the form

Create an automation using **Integration watchdog — 2026.11.3.1**, then select, in the **Integration and entities to watch** section:

| Field | What to select |
|---|---|
| Configuration of the integration to watch | The account or gateway to monitor. |
| Entities to watch | Active entities from that integration, such as a temperature sensor or thermostat. |
| Text helper that keeps the history | The Text helper you just created. |
| Home Assistant Uptime sensor | The sensor provided by the Uptime integration. |

Give the watchdog a name (**Name in notifications**), adjust settings if needed and save. You can start with **Observe without reloading the integration** and check the logs.

Create one monitoring automation per integration configuration. Separate accounts or gateways of the same integration need separate monitoring: TaHoma and Cozytouch, for example, are two separate Overkiz configurations.

## 3. Add more integrations

Create another Text helper and another automation from the same blueprint. No other file and no restart is needed.

The blueprint does not impose a fixed limit on the number of monitored integrations. It limits simultaneous reloads to **50** across all monitoring automations. An additional request tries again one minute later without consuming a retry.

The [Netatmo, TaHoma and Cozytouch examples](../examples/integration_watchdog/) contain fictional identifiers. Adapt them before use. Their `local/integration_watchdog.yaml` path matches manual installation; after a GitHub import, use the actual blueprint path shown by Home Assistant.

## Choose suitable settings

| Setting | Default |
|---|---|
| Check frequency | Every minute |
| Minimum failure duration before a reload (seconds) | 5 minutes |
| Wait after Home Assistant start-up (seconds) | 10 minutes |
| Maximum number of attempts for one failure | 3 |
| Maximum number of attempts over the last 24 hours | 6 |
| Time given to the integration to recover after a reload (seconds) | 10 minutes |
| Normal operation time before confirmation (seconds) | 3 minutes |
| Normal operation time before the attempts are reset (seconds) | 30 minutes |
| Wait before a new attempt (seconds) · Maximum wait between two attempts (seconds) | From 5 minutes to 1 hour, depending on previous failures |
| Delay before an alert when a reload does not finish (seconds) | 3 minutes |

Delays are evaluated during checks, so an action may wait until the next check. Resetting the outage retry count does not reset the limit for the last 24 hours.

**Entities in error.** With **When should the integration be reloaded?**, you can wait until all selected entities are in error (*When every entity is failing*), or act when at least one has been in error long enough (*When at least one entity is failing*). `unavailable` means the entity cannot be reached. `unknown` means Home Assistant does not know its value: it triggers a retry only when **Count the « unknown » state as a failure** is enabled, and never confirms recovery.

**Missing new data.** This check is off by default: its delay, **Maximum delay without new data (seconds)**, is **0**. Enable it for measurements sent regularly. Keep it at 0 for stationary covers or thermostats with infrequent changes, unless the integration provides a reliable measurement timestamp (**Entity giving the date of the last measurement (optional)**). Without that timestamp, the check measures reports received by Home Assistant rather than the actual age of the provider’s data.

**Recovery.** All monitored entities must work for the confirmation period, even when one entity in error is enough to trigger a retry. A brief improvement does not reset the retry count.

## Notifications and logs

By default, Home Assistant displays a notification when intervention is required and removes it after confirmed recovery. You can replace these actions with your preferred notifications in the **Notifications** section of the form (**Actions when an intervention is needed**, **Actions after recovery**).

Useful events are written to the `integration_watchdog` logger. The monitoring sets its level itself (info, or debug with **Enable detailed logs**): no configuration is needed. Detailed logging adds routine checks and can help diagnose a problem. Alerts are sent before logging, so a logging failure cannot block them.

Exclusions, observation mode and additional conditions prevent new retries. They do not cancel a reload already in progress.

## If manual intervention is needed

**Reload taking too long.** If a reload outlives the configured delay, an alert is sent. The reload is not cancelled: the monitoring waits for its end, then resumes normally and announces the return to normal. No other reload of this integration starts meanwhile; other monitoring automations keep working. Check the integration errors and the automation traces.

**Interrupted reload.** If Home Assistant stops, or the monitoring automation is edited or disabled during a reload, the reload is interrupted. The next check detects it by itself: the attempt stays counted, and if the integration was left unloaded, the reload is resumed within the retry limits. No manual action is needed.

**Retry after an intervention.** Open the monitoring automation and choose **Run actions**: the retry count for the current outage is reset, then a check runs at once. The last-24-hours count is preserved.

## Important limitations

- Detection depends on the entities you select. A cloud outage may leave those entities available.
- Integrations are selected manually; there is no automatic discovery of all cloud integrations.
- Home Assistant must remain responsive for its automations to work. An abrupt shutdown may lose the most recent history update.
- Tests simulate provider calls; they do not prove that a real Netatmo or Overkiz outage will be repaired.

[How it works, tests and limitations](integration_watchdog_robustness.en.md)

Home Assistant documentation: [Text helpers](https://www.home-assistant.io/integrations/input_text/), [importing blueprints](https://www.home-assistant.io/docs/automation/using_blueprints/).
