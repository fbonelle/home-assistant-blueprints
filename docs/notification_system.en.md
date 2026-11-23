# Notification system

[Français](notification_system.md) · **English**

Four blueprints that make up a complete notification system, with a single entry point for every automation.

| Blueprint | Type | Role |
|---|---|---|
| [Notifications — Channel sender](../blueprints/script/notification_system/channel_sender.yaml) | script, parallel | Sends on one channel (mobile app, ntfy or e-mail) and returns `success` when the send went through. |
| [Notifications — Dispatcher](../blueprints/script/notification_system/dispatcher.yaml) | script, parallel | Entry point: picks channels by level, drops duplicates, handles night time, fallback and speech. |
| [Notifications — Mobile relay](../blueprints/automation/notification_system/mobile_relay.yaml) | automation | Sends Home Assistant persistent notifications to the dispatcher and clears them from the phone when they are dismissed. |
| [Notifications — Text-to-speech](../blueprints/script/notification_system/text_to_speech.yaml) | script, queued | Speaks the message on labelled speakers, one announcement after another. |

Why four rather than one: a blueprint produces a single script or automation. The channel sender is a separate script because, in Home Assistant, that is the only way to know a send failed and fall back to another channel. Speech is separate because it runs queued, while the dispatcher handles several notifications at once.

## Installation

1. Import the four blueprints:
   [Channel sender](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fscript%2Fnotification_system%2Fchannel_sender.yaml) ·
   [Dispatcher](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fscript%2Fnotification_system%2Fdispatcher.yaml) ·
   [Mobile relay](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fnotification_system%2Fmobile_relay.yaml) ·
   [Text-to-speech](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fscript%2Fnotification_system%2Ftext_to_speech.yaml).
2. Create two helpers: a **text** helper with a maximum length of 255 for the duplicate memory and, if needed, a **toggle** to mute speech.
3. Label the media players that should speak `tts`.
4. Create the scripts and the automation, preferably in a *package*: the [complete example](../examples/notification_system/package.yaml) holds the helpers and the four instances. Create the channel sender and speech first, then the dispatcher, which points to them, then the relay, which points to the dispatcher.

The dispatcher script ID is what automations call, for example `script.notify_dispatch_global`.

## Sending a notification

```yaml
action: script.notify_dispatch_global
data:
  title: Water leak
  message: Water detected in the cellar.
  level: critical          # info (default), warning, critical, technical
  target: all              # main (default) or all
  entity_id: binary_sensor.cellar_leak
  tts: false               # true forces speech
  data:
    snapshot_file: /config/www/snapshots/cellar.jpg
    click: /lovelace/security
```

`data` also accepts `icon` (ntfy icon), `actions` (buttons), `priority` and `tags` (ntfy), `html` (added to the e-mail body), `notif_id` (notification ID) and `skip_trace` (no persistent notification).

## Behaviour

**Channels by level** (configurable in that section): `info`, `warning` and `critical` go to the mobile app; `technical` goes to ntfy; `critical` is also e-mailed. `warning`, `critical` and `technical` are written to the logbook.

**Mobile app.** Every notification also creates a `sys_disp_…` persistent notification in Home Assistant, except when it comes from the relay. The phone tag is the same ID: dismissing the notification in Home Assistant clears it from the phone. An ID supplied without the prefix gets `sys_disp_` exactly once. At night the sound is muted; `critical` breaks through silent mode (iOS, and Android when the channel is allowed to).

**Fallback.** An ntfy entity that has just become unavailable, as at Home Assistant start-up, is waited for at most 120 seconds after it became unavailable (**Wait for an ntfy entity that has just become unavailable** in the channel sender, 0 for no wait). If ntfy fails, including when its entity is missing or stays unavailable, the message goes to the mobile app with “🚨 FALLBACK NTFY: ” before the title. If the e-mail fails, a warning is logged; the other channels are served.

**Duplicate filter.** An identical message (same level, title and text) is not sent again for 5 minutes, even interleaved with other messages (last 10 messages remembered). The window is fixed: a source that keeps flapping comes back once every 5 minutes. An unreadable memory never blocks a send. A dropped duplicate is logged at INFO level in the `notification_system` logger, not as a warning: it is normal operation.

**Links.** Without an explicit link (`data.click`), a notification opens the history of the given entity, the logs page for `technical`, otherwise the default page. ntfy gets an app link, the e-mail a web link.

**Attachments.** `data.snapshot_file` accepts a local path (`/config/www/…`, `/local/…`, `www/…`), a URL or a media source URI. Each channel receives the form it needs: a URL for ntfy and the mobile app, a media source attachment for the e-mail. A remote image is referenced in the e-mail, since SMTP cannot attach a URL.

**Speech.** `critical` is always spoken; `warning` is spoken during the day when someone is home (`zone.home`); `tts: true` forces speech. Announcements play one after another. For `critical`, the volume is raised, then the speakers are restored. With no labelled speaker available, nothing is spoken and a warning says so.

**Relay.** The level comes from the title (**Level deduced from the title** section): 🚨, “Emergency” or “Failure” → `critical`; ⚠️ or “Alert” → `warning`; 🔧, 📡, 🔴 or 🟢 → `technical`; otherwise `info`. Dispatcher notifications (`sys_disp_`) are never relayed, which prevents loops. Two prefix lists complete this: **Prefixes never forwarded** (the notification stays in Home Assistant) and **Prefixes dismissed automatically** (it disappears as soon as it appears and never reaches the phone). Titles written in another language need adapted markers.

## Limits

- Two truly simultaneous dispatcher calls can read the duplicate memory before either writes: Home Assistant offers no atomic conditional write. The relay, being queued, serialises the most frequent path.
- The relay only sees notifications created after it is loaded: Home Assistant does not pass existing ones to automations. Persistent notifications do not survive a restart, and integrations recreate theirs afterwards.
- The length of a critical announcement is estimated from the text length (configurable rate) before the speakers are restored.

## Tests

`tests/test_notification_system.py` creates the three scripts and the automation from the published blueprints on Home Assistant (tested and minimum releases, see the [README](../README.en.md#development)), with real helpers, persistent notifications, labels and registries. Only outbound services (mobile app, ntfy, SMTP, speech, volume, scenes, logbook) are doubles, and they can be made to fail. Covered: every level, night time, family target, breaking silence, e-mail and its attachments, ntfy fallback and waiting for ntfy at start-up, e-mail failure, duplicates and level escalation, a corrupt memory, IDs, speech (presence, night, mute, missing speakers, restore) and the relay (levels, 1:1 clearing, no loop, prefixes, startup).
