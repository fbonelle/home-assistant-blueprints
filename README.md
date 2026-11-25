# Blueprints Home Assistant

**Français** · [English](README.en.md)

Une collection de blueprints pour automatiser Home Assistant avec ses fonctions standard. Chaque blueprint dispose de son guide, de ses exemples et de ses tests. Les formulaires, les messages et les noms des blueprints sont en anglais ; les guides en français citent les libellés tels qu’ils apparaissent.

## Disponible

| Blueprint | Fonction | Version | Prérequis |
|---|---|---|---|
| [Battery watch](docs/battery_watch.md) | Signaler tout de suite chaque pile ou batterie à remplacer et chaque appareil muet, puis envoyer un récapitulatif à heure fixe. | **2026.11.3.0** | Home Assistant 2026.10 minimum |
| [Integration watchdog](docs/integration_watchdog.md) | Détecter une panne à partir d’entités choisies, tenter une relance et prévenir si une intervention est nécessaire. | **2026.11.3.0** | Home Assistant 2026.10 minimum |
| [Lighting remotes and automatic switch-off](docs/lighting.md) | Une action au choix pour chaque geste des télécommandes Aqara, eWeLink, Hue Dimmer, Hue Tap Dial, IKEA 5 boutons, IKEA marche/arrêt et IKEA STYRBAR ; extinction après une durée d’allumage. | **2026.11.3.0** | Home Assistant 2026.10 minimum, ZHA ; assistant facultatif |
| [Notification system](docs/notification_system.md) | Un point d’entrée unique : canaux par niveau (mobile, ntfy, e-mail), anti-doublon, nuit, bascule de secours, lecture vocale et relais des notifications persistantes. | **2026.11.3.0** | Home Assistant 2026.10 minimum, quatre blueprints |

Chaque version est celle de Home Assistant avec laquelle le blueprint a été validé, suivie d’un compteur de modifications du projet : **2026.11.3.0** a réussi tous les tests avec Home Assistant 2026.11.3. À chaque nouvelle version publique de Home Assistant, les tests sont relancés automatiquement ; s’ils réussissent, tous les blueprints passent à la nouvelle version. Le prérequis indique la version minimale réellement nécessaire.

## Battery watch

Un blueprint autonome et une liste de tâches locale, sans limite de taille : chaque pile ou batterie qui passe sous le seuil, chaque appareil muet depuis plusieurs heures et chaque alerte « pile faible » est signalé une seule fois, dès sa détection, et ajouté à la liste ; cocher un élément le retire du récapitulatif jusqu’au remplacement. Un récapitulatif part à l’heure et aux jours choisis. Téléphones, montres, ordinateurs et onduleurs sont exclus par défaut ; les exclusions se complètent par intégration, fabricant, entité, appareil ou étiquette.

[Installation et réglages](docs/battery_watch.md) · [Importer le blueprint](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fbattery_watch%2Fbattery_watch.yaml) · [Exemples](examples/battery_watch/automations.yaml)

## Integration watchdog

1. [Importer le blueprint](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fintegration_watchdog%2Fintegration_watchdog.yaml).
2. Créer un assistant Texte, puis choisir l’intégration et les entités à surveiller dans le formulaire.

[Guide d’installation](docs/integration_watchdog.md) · [Fonctionnement, tests et limites](docs/integration_watchdog_robustness.md)

Les délais, le nombre de tentatives, les exclusions, les notifications et les journaux sont réglables. Une nouvelle intégration s’ajoute depuis le formulaire, sans recopier de scripts.

**Le blueprint est le seul fichier à installer.** Aucun fichier de configuration, script, composant personnalisé ni redémarrage n’est nécessaire.

Les exemples Netatmo, TaHoma et Cozytouch sont fictifs et doivent être adaptés avant utilisation.

## Lighting remotes and automatic switch-off

Un blueprint par modèle de télécommande ZHA (boutons Aqara et eWeLink, Philips Hue Dimmer et Tap Dial, télécommandes IKEA 5 boutons et STYRBAR, interrupteur IKEA marche/arrêt), avec les mêmes actions et les mêmes réglages partout : basculer, niveaux fixes, alternance, variation d’un pas ou en continu, température du blanc, palette de 44 préréglages, couleur de rappel, action personnalisée. Les variations continues s’arrêtent au relâchement ou après une durée maximale. Un assistant Texte facultatif ajoute le double appui sur les télécommandes IKEA, la position exacte dans la palette et l’arrêt au niveau atteint. Un dernier blueprint éteint des éclairages après une durée d’allumage, avec ou sans assistant Minuteur.

[Actions, réglages et passage depuis les anciens blueprints](docs/lighting.md) · [Exemples](examples/lighting/automations.yaml) · Importer : [Aqara](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flighting%2Faqara_button.yaml), [eWeLink](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flighting%2Fewelink_button.yaml), [Hue Dimmer](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flighting%2Fhue_dimmer_remote.yaml), [Hue Tap Dial](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flighting%2Fhue_tap_dial_remote.yaml), [IKEA 5-button](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flighting%2Fikea_5_button_remote.yaml), [IKEA on/off](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flighting%2Fikea_on_off_switch.yaml), [IKEA STYRBAR](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flighting%2Fikea_styrbar_remote.yaml), [Lighting automatic switch-off](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flighting%2Fauto_off.yaml)

## Notification system

Quatre blueprints qui fonctionnent ensemble : un répartiteur (**Dispatcher**), point d’entrée appelé par toutes les automatisations, un envoi sur un canal (**Channel sender**) qui isole chaque canal pour détecter ses pannes, une lecture vocale en file d’attente (**Text-to-speech**) et un relais (**Mobile relay**) qui envoie les notifications persistantes au téléphone et les en efface. Toutes les adresses, appareils, horaires et règles se règlent dans les formulaires ; seules deux aides sont à créer.

[Installation et comportement](docs/notification_system.md) · [Exemple de package](examples/notification_system/package.yaml) · Importer : [Channel sender](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fscript%2Fnotification_system%2Fchannel_sender.yaml), [Dispatcher](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fscript%2Fnotification_system%2Fdispatcher.yaml), [Mobile relay](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fnotification_system%2Fmobile_relay.yaml), [Text-to-speech](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fscript%2Fnotification_system%2Ftext_to_speech.yaml)

## Développement

Les blueprints se trouvent dans `blueprints/`, leurs exemples dans `examples/` et leurs guides dans `docs/`.

Pour générer les fichiers et lancer les tests, avec Python 3.14 :

```sh
python3.14 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python tools/build.py
.venv/bin/python -m pytest -q
```

La suite tourne sur deux versions de Home Assistant : la version testée, qui forme le début du numéro de version des blueprints, et la version minimale annoncée (dernier correctif de ce mois). Elle couvre tous les blueprints avec ses schémas, automatisations et services natifs. Les fournisseurs et la radio sont simulés ; aucun identifiant de production n’est nécessaire. Home Assistant n’installe aucun paquet pendant les tests. GitHub Actions vérifie aussi que les fichiers générés sont à jour. Chaque blueprint conserve sa propre version dans `src/<nom>/VERSION`.

[Contribuer](CONTRIBUTING.md) · [Historique](CHANGELOG.md) · [Origine et licence](NOTICE.md)
