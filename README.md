# Blueprints Home Assistant

**Français** · [English](README.en.md)

Une collection de blueprints pour automatiser Home Assistant avec ses fonctions standard. Chaque blueprint dispose de son guide, de ses exemples et de ses tests.

## Disponible

| Blueprint | Fonction | Version | Prérequis |
|---|---|---|---|
| [Surveillance et relance des intégrations](docs/integration_watchdog.md) | Détecter une panne à partir d’entités choisies, tenter une relance et prévenir si une intervention est nécessaire. | **1.0.1** | Home Assistant 2026.10 minimum |
| [Lampe avec télécommande IKEA STYRBAR](docs/ikea_styrbar_light.md) | Marche/arrêt, luminosité, palette de blancs et couleurs IKEA, rappel d’une couleur configurable. | **1.0.0** | Home Assistant 2026.10, ZHA, lampe couleur |

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

Un blueprint par lampe, avec un assistant Texte dédié. Aucun fichier partagé à installer. Les trois blancs de référence Home Assistant, les 20 préréglages historiques IKEA et les réglages de luminosité sont disponibles dans le formulaire. Le double appui en haut dépend des événements réellement émis par le micrologiciel ; le maintien à droite rappelle également la couleur par défaut.

[Installation et boutons](docs/ikea_styrbar_light.md) · [Blueprint](blueprints/automation/ikea_styrbar_light/lampe_styrbar.yaml) · [Exemples](examples/ikea_styrbar_light/automations.yaml)

## Développement

Les blueprints se trouvent dans `blueprints/`, leurs fichiers communs dans `packages/`, leurs exemples dans `examples/` et leurs guides dans `docs/`.

Pour générer les fichiers et lancer les tests, avec Python 3.14 :

```sh
python3.14 -m venv .venv
.venv/bin/python -m pip install -r requirements-dev.txt
.venv/bin/python tools/build.py
.venv/bin/python -m pytest -q
```

La suite utilise Home Assistant 2026.10.4 et couvre les deux blueprints avec ses schémas, automatisations et services natifs. Les fournisseurs et la radio sont simulés ; aucun identifiant de production n’est nécessaire. GitHub Actions vérifie aussi que les fichiers générés sont à jour. Chaque blueprint conserve sa propre version dans `src/<nom>/VERSION`.

[Contribuer](CONTRIBUTING.md) · [Historique](CHANGELOG.md) · [Origine et licence](NOTICE.md)
