# How it works, tests and limitations

[Français](integration_watchdog_robustness.md) · **English** · [Installation guide](integration_watchdog.en.md)

This page describes the monitoring safeguards and how they are tested. The installation guide is enough to configure monitoring.

## A single file

The blueprint depends on no shared configuration file, script or automation. Each monitoring automation does everything itself: check, decision, reload, alerts and logs. Its only data is its Text helper.

Each monitoring automation runs in queued mode: one run at a time. It is therefore the only writer of its helper, and every write is read back. Triggers arriving during a run wait their turn, up to 10; further ones are dropped silently, since every run re-reads the whole state and nothing is lost.

## Retries and delays

A retry is counted when the reload is accepted, just before the call. Two limits apply: retries for the same outage and retries over the last 24 hours. A lasting recovery resets only the first counter. Reloads started manually or by other automations are not counted.

The limit of 6 retries over 24 hours keeps the history within one 255-character Text helper.

## Reload inside the run

The reload runs inside the monitoring run. As soon as it ends, the same run records its end and opens the verification period, without waiting for the next check.

During the reload, a parallel branch watches the configured delay. If it is exceeded, the branch sends the “reload taking too long” alert. It only reads the history, so it cannot conflict with the recording of the end. The reload is not cancelled. When it finally ends, the alert is remembered, so the return to normal is announced.

A stuck reload only holds its own monitoring automation: there is nothing else to do for that integration until it ends. Other monitoring automations keep working.

## Interrupted reload

Stopping a run cancels the running action, including a reload. This happens when Home Assistant stops, or when the monitoring automation is edited, disabled or updated during a reload. Reloading automations without changing this one does not interrupt it.

The next run detects it unambiguously: in queued mode no other run can be in progress, so a reload marked “started” was necessarily interrupted.

- The retry stays counted.
- If the integration is loaded, the verification period opens normally.
- If the integration was left unloaded, the reload is resumed at once, within the retry limits. Without this, the integration would stay stopped, since an unloaded integration is never reloaded otherwise.
- A reservation not yet accepted is simply dropped, with no retry counted.

No manual command is needed. **Run actions** on the automation resets the retry count of the current outage, keeps the 24-hour history, then checks at once.

## Cap of 50 reloads and duplicates

The cap of 50 simultaneous reloads and the duplicate detection rely on a reservation in the helpers themselves, with no shared queue.

1. The monitoring automation that decides a reload first writes its reservation in its helper.
2. It then reads the other automations’ reservations.
3. It counts the reloads already accepted and the reservations written before its own, according to the write time recorded by Home Assistant.

Since each automation writes before reading, the later of two always sees the earlier one: all get the same order and only the first 50 start. If two reservations carry exactly the same time, every automation concerned tries again one minute later, so no overshoot is possible. A deferred request does not consume a retry.

Two monitoring automations of the same integration never reload together: the other’s reservation is enough to defer the request, and the duplicate configuration is reported.

A reservation older than one hour belongs to a monitoring automation that has not run since, for example a disabled one. It no longer counts against the cap.

## Normal shutdowns

The history is restored after a normal Home Assistant shutdown. An abrupt power cut may lose its latest update. At startup, an interrupted reload is handled as described above.

## Notifications and logs

A notification is marked as sent once its action succeeds. It may be repeated if Home Assistant stops before that record. Exactly-once delivery to an external service is not guaranteed.

The `integration_watchdog` log is written after the alerts and their record: a logging error cannot block them. The monitoring sets this logger’s level itself (info, or debug with detailed logging); Home Assistant’s logging integrations are always loaded.

Custom actions must stay short: an action that never ends holds its own monitoring automation.

## What the tests check

The suite runs on official Home Assistant (tested and minimum releases, see the [README](../README.en.md#development)), with Python **3.14**, in temporary folders.

Automations, helpers, templates and notifications are real. Only integration reloads are replaced by controlled responses; the integrations and entities used are fictitious.

Scenarios include:

- 51 simultaneous requests: 50 distinct reloads and one deferred request;
- a full cap, and old reservations that no longer count;
- a reload taking too long: alert after the delay, reload not cancelled, return to normal announced;
- an interrupted reload, with the integration loaded or left unloaded, as a direct run and with a real automation disabled then enabled again;
- a restart during a reload, without refunding the retry;
- two concurrent monitoring automations of the same integration and simultaneous runs of the same one;
- retry limits, delays, exclusions, observation mode and the reset through **Run actions**;
- invalid data, failing notifications and a failing or missing log service;
- measurement timestamps, Uptime changes and a clock moving backwards;
- reauthentication requests and reconnections already handled by Home Assistant;
- the log level set by the monitoring itself.

GitHub Actions runs the tests and checks that the distributed YAML files match their sources.

## Limitations to keep in mind

An integration can remain available while returning wrong data or ignoring some commands. The blueprint can only detect problems visible in the selected entities and timestamps. Very brief changes between two checks may go unnoticed.

Reauthentication requests are detected through Home Assistant’s standard repairs. Some third-party components use other mechanisms that may not appear there.

A failure of Home Assistant itself, its storage or its server can prevent checks. The tests do not prove that a reload repairs a real provider outage.
