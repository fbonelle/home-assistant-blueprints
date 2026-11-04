# How it works, tests and limitations — 1.0.0

[Français](robustesse_integration_watchdog.md) · **English** · [Installation guide](integration_watchdog.en.md)

This page describes the first version’s safeguards and how they are tested. The installation guide is enough to configure monitoring.

## Retry counts and delays

A retry is counted when the system accepts a reload request. If all 50 slots are busy, the request waits for another check after at least 60 seconds without increasing the count.

Two limits apply: retries for the same outage and retries in the last 24 hours. Sustained recovery resets only the first counter. Reloads started manually or by other automations are not counted.

The limit of 6 retries per 24 hours keeps the history within one 255-character Text helper.

## Preventing duplicate reloads

The helper is associated with one integration configuration and its automation. Another monitoring automation linked to the same configuration causes a configuration error before further reloads.

Starting a request follows several recorded steps. Receiving the same request twice cannot trigger two calls. Requests are processed in order before starting the reload scripts, which can then run in parallel.

Internal script and automation identifiers remain fixed so other components can call them. Display names can be clearer without changing those identifiers.

## Recording results without losing updates

All history updates go through one shared script. It checks that the value has not changed since it was read, writes the new value and checks the result. After a concurrent change, it reads again, for up to five attempts. If writing remains impossible, it reports the problem and requests no new reload.

A reload’s completion is recorded before sending the signal that wakes its monitoring automation. If that signal is lost, the next periodic check finds the result. A slow notification cannot replace that result with an older copy of the history.

Completion time is rounded up to the next whole second. A report received before actual completion therefore cannot be treated as newer. A report received just afterwards may also be rejected for less than a second; the next report is then needed.

## Restarts and manual actions

A change to the Uptime sensor alone cannot allow a second reload. Recovering an interrupted request uses Home Assistant’s actual startup trigger and checks that the shared reload script is stopped.

If automatic recovery could not run, the request stays blocked until manual confirmation. The confirmation command also checks that the script is stopped when recording its result, preventing a race with a new start.

History is restored after a normal Home Assistant shutdown. An abrupt power loss may lose its latest update. The scripts do not forcibly cancel a stuck call.

## Notifications and logs

Logging runs in a separate automation. An error in the logging service, or a missing service, therefore does not block outage notifications.

A notification is marked as sent after its action succeeds. It may be sent again if Home Assistant stops before recording that fact, or if recording repeatedly fails. There is no exactly-once delivery guarantee to an external service.

Custom actions should remain short. If they never finish, they can block their own monitoring automation even though reloads and logging run separately.

## What the tests cover

The suite contains **88 tests** using official Home Assistant **2026.10.4**, Python **3.14** and temporary directories.

Scripts, automations, helpers, templates, events and notifications are real. Only provider calls are replaced with controlled responses; test integrations and entities are fictional.

Scenarios include:

- 51 concurrent requests: 50 distinct reloads and one deferred request;
- retry limits, delays, exclusions and observation mode;
- restarts after interruption and lost completion signals;
- two concurrent monitors of the same integration and replayed requests;
- refused writes, invalid data and slow or failing notifications;
- measurement timestamps, Uptime changes and backward clock changes;
- reauthentication requests and reconnections already handled by Home Assistant.

GitHub Actions runs the tests and checks that distributed YAML files match their sources. Dependency deprecation warnings remain visible in the results.

## Limitations

An integration can remain available while returning incorrect data or failing to answer some commands. The blueprint can only detect problems visible in the selected entities and timestamps. Brief changes between checks may be missed.

Queues are bounded: 100 running or waiting executions per monitor and 1,000 for short shared services. Exceeding them is recorded in logs. A lost request stays blocked as a precaution, without a counted retry if it was not accepted, and later raises an alert.

Reauthentication requests are detected through Home Assistant’s standard repairs registry. Some third-party components use other mechanisms that may not appear there.

A failure of Home Assistant itself, its storage or its server can prevent checks. The tests do not prove that reloading will fix an actual provider outage.
