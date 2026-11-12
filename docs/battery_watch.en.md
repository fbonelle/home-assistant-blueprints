# Battery monitoring

[Français](battery_watch.md) · **English** · [Home](../README.en.md)

Version **1.0.0**. A standalone blueprint that reports each battery to replace as soon as it is detected, then sends a summary at the time you choose. No shared file or custom component is required.

## Installation

1. Use Home Assistant **2026.10 or later**.
2. [Import the blueprint](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fbattery_watch%2Fsurveillance_piles.yaml).
3. In **Settings → Devices & services → Add integration**, add **Local To-do** and create a dedicated list, for example “Batteries”. Reserve it for this automation.
4. Create an automation from the blueprint, select the list, then fill in the **Immediate alert actions** and the **Summary actions** (for example a phone notification or an existing notification script).
5. Disable the previous automation that sent the same summary, to avoid receiving two messages.

The [automation example](../examples/battery_watch/automations.yaml) only uses fictitious identifiers. A Local To-do list is created from the UI; it cannot be declared in YAML. Adjust the blueprint path if Home Assistant suggests another name when importing.

## What is reported

| Situation | Message |
|---|---|
| Battery level strictly below the threshold (20 % by default) | `• Living room remote — 18 %` |
| Device unavailable for longer than the configured delay (6 hours by default) | `• Smoke detector — muet depuis 7 h` |
| “Battery low” alert raised by the device (battery binary sensor `on`) | `• Leak sensor — alerte pile faible` |

An empty battery often makes the device silent instead of reporting a low level, which is why a long unavailability is reported. The delay ignores short outages of a gateway or cloud service, which make all its devices unavailable at the same time. The `unknown` state, transient at startup, is ignored. Setting the delay to 0 disables this rule.

Only entities of the **battery** device class are examined: sensors (`sensor`) and, when the option is enabled, binary sensors (`binary_sensor`). Messages are written in French.

## Devices excluded by default

Phones, watches, computers and UPS units are charged daily or monitored elsewhere. They are excluded by default:

- integrations `mobile_app`, `icloud`, `icloud3` and `nut`;
- devices made by **Apple**.

The integration is read from the configuration entry each entity belongs to. An entity that an integration no longer lists, but that is still attached to its configuration entry, is therefore excluded as well. Additional exclusions can be set by entity, device or label: entities and devices carrying an excluded label are ignored.

## Immediate alert and battery list

The check runs every 5 minutes by default. Each device that **enters** the list of batteries to check triggers the **Immediate alert actions**, once, and becomes an item of the to-do list: `Living room remote — 18 %`. The list acts as memory, including across restarts, and has no size limit:

- a battery that keeps dropping (18 %, 15 %, 9 %…) is not reported again; the item label is simply updated;
- a reported device is only considered fixed above the **threshold plus the recovery margin** (5 points by default), or when its binary alert returns to `off`; its item is then removed automatically. A battery oscillating around the threshold therefore does not produce new alerts;
- a reported device that becomes silent or unknown, for example during a restart, stays in the list and is not reported a second time;
- a battery that was replaced and later becomes low again is reported again.

**Checking an item** marks the battery as taken care of (ordered, replacement planned): the device leaves the summary and the persistent notification, without a new alert. The item stays checked with an up-to-date label until the battery is replaced, then it is removed. Unchecking it brings it back to the summary.

Items added manually to the list are ignored: only those created by the automation, recognizable by their `battery_watch:<entity>` description, are managed. Do not edit that description.

**First check.** With an empty list, the first check reports all devices already concerned in a single alert.

## Summary and persistent notification

At the selected time and days, the **Summary actions** receive the full list of batteries to check. The summary is only sent when something needs attention, unless **Also send the summary when everything is fine** is enabled. **Menu → Run actions** sends the summary immediately, which lets you test the actions.

A Home Assistant persistent notification, specific to this automation, is updated whenever the list changes and removed when nothing needs attention. It can be disabled.

**Additional conditions** (for example: someone is home) apply to the alerts and the summary. The memory and the persistent notification stay up to date even when these conditions fail; a device detected meanwhile is added to the list and not reported a second time.

## Variables available in the actions

| Variable | Content |
|---|---|
| `battery_title` | Ready-to-use title: `🔋 Pile ou batterie à remplacer (2)` or `Piles et batteries à vérifier (3)`. |
| `battery_message` | One line per device, sorted by name: new devices for the alert, all devices for the summary. |
| `battery_new` | List of new devices. |
| `battery_all` | List of devices to check, excluding checked items. |
| `battery_acknowledged` | List of devices whose item is checked. |
| `battery_count` | Number of devices to check, excluding checked items. |

Each list item contains `e` (entity), `n` (name), `r` (reason: `level`, `silent` or `alert`), `v` (level in %, for `level`) and `h` (hours unavailable, for `silent`).

Example with an existing notification script:

```yaml
alert_actions:
  - action: script.home_notification
    data:
      title: "{{ battery_title }}"
      message: "{{ battery_message }}"
```

## Invalid configuration

A missing or unavailable to-do list, a list that cannot add, update, remove and describe items, or an out-of-range setting stops the automation without changing the list. The problem is shown in a persistent notification and written to the `battery_watch` log.

## Limits

- The blueprint reads the levels reported by integrations; it does not measure the actual battery condition.
- A device unavailable for another reason than an empty battery (unplugged, gateway down beyond the delay) is also reported as silent.
- Manufacturer exclusions compare the name declared by the integration, ignoring case.

[Changelog](../CHANGELOG.en.md) · [Attribution and license](../NOTICE.en.md)
