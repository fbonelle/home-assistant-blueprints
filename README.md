# Blueprints Home Assistant

**Français** · [English](README.en.md)

Une collection de blueprints pour automatiser Home Assistant avec ses fonctions standard. Chaque blueprint dispose de son guide, de ses exemples et de ses tests.

## Disponible

| Blueprint | Fonction | Version | Prérequis |
|---|---|---|---|
| [Surveillance et relance des intégrations](docs/integration_watchdog.md) | Détecter une panne à partir d’entités choisies, tenter une relance et prévenir si une intervention est nécessaire. | **1.0.1** | Home Assistant 2026.10 minimum |
| [Lampe avec télécommande IKEA STYRBAR](docs/ikea_styrbar_light.md) | Marche/arrêt, maintiens rapides de luminosité et couleur, contrôle des capacités, rappel configurable. | **1.2.0** | Home Assistant 2026.10, ZHA, lampe couleur, script partagé |
| [Surveillance des piles et batteries](docs/battery_watch.md) | Signaler tout de suite chaque pile ou batterie à remplacer et chaque appareil muet, puis envoyer un récapitulatif à heure fixe. | **1.0.0** | Home Assistant 2026.10 minimum |

La version **1.0.0 est la première version publiée**. Les numéros utilisés pendant la préparation ne constituent pas des versions du projet.

## Surveillance et relance des intégrations

1. Installer le [fichier de configuration commun](packages/integration_watchdog.yaml), une seule fois.
2. [Importer le blueprint](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fintegration_watchdog%2Fsurveillance_integrations.yaml).
3. Créer un assistant Texte, puis choisir l’intégration et les entités à surveiller dans le formulaire.

[Guide d’installation](docs/integration_watchdog.md) · [Fonctionnement, tests et limites](docs/robustesse_integration_watchdog.md)

Les délais, le nombre de tentatives, les exclusions, les notifications et les journaux sont réglables. Une nouvelle intégration s’ajoute depuis le formulaire, sans recopier de scripts.

**Deux fichiers sont nécessaires au départ : le blueprint et le fichier de configuration commun.** Ce dernier est un *package* Home Assistant : un fichier YAML regroupant les scripts et automatisations utilisés par le blueprint. Aucun composant personnalisé ni code Python n’est à installer dans Home Assistant.

Les exemples Netatmo, TaHoma et Cozytouch sont fictifs et doivent être adaptés avant utilisation.

## Lampe avec télécommande IKEA STYRBAR

Un blueprint par lampe, avec un assistant Texte dédié, et un [petit script partagé](packages/ikea_styrbar_light.yaml) installé une seule fois pour les maintiens rapides. Les trois blancs de référence Home Assistant, les 20 préréglages historiques IKEA et les vitesses de luminosité et de couleur se règlent dans le formulaire. Les maintiens latéraux font défiler la palette ; le double appui en haut rappelle la couleur par défaut si le micrologiciel transmet deux événements. Un maintien latéral peut aussi être réservé au rappel.

Le diagnostic des capacités s’affiche avec **Menu → Exécuter les actions**, sans commander la lampe. Les maintiens utilisent les fondus natifs et un arrêt au niveau intermédiaire estimé lors du relâchement.

[Installation et boutons](docs/ikea_styrbar_light.md) · [Blueprint](blueprints/automation/ikea_styrbar_light/lampe_styrbar.yaml) · [Exemples](examples/ikea_styrbar_light/automations.yaml)

## Surveillance des piles et batteries

Un blueprint autonome et un assistant Texte : chaque pile ou batterie qui passe sous le seuil, chaque appareil muet depuis plusieurs heures et chaque alerte « pile faible » est signalé une seule fois, dès sa détection. Un récapitulatif part à l’heure et aux jours choisis. Téléphones, montres, ordinateurs et onduleurs sont exclus par défaut ; les exclusions se complètent par intégration, fabricant, entité, appareil ou étiquette.

[Installation et réglages](docs/battery_watch.md) · [Importer le blueprint](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fbattery_watch%2Fsurveillance_piles.yaml) · [Exemples](examples/battery_watch/automations.yaml)

## Développement

Les blueprints se trouvent dans `blueprints/`, leurs fichiers communs dans `packages/`, leurs exemples dans `examples/` et leurs guides dans `docs/`.

Pour générer les fichiers et lancer les tests, avec Python 3.14 :

```sh
python3.14 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python tools/build.py
.venv/bin/python -m pytest -q
```

La suite utilise Home Assistant 2026.10.4 et couvre les trois blueprints avec ses schémas, automatisations et services natifs. Les fournisseurs et la radio sont simulés ; aucun identifiant de production n’est nécessaire. GitHub Actions vérifie aussi que les fichiers générés sont à jour. Chaque blueprint conserve sa propre version dans `src/<nom>/VERSION`.

[Contribuer](CONTRIBUTING.md) · [Historique](CHANGELOG.md) · [Origine et licence](NOTICE.md)
