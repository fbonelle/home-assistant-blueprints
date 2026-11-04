# Historique

**Français** · [English](CHANGELOG.en.md)

## Lampe STYRBAR — 1.1.0 — 4 novembre 2026

- Contrôle des capacités à l’activation, avant les commandes et lors d’un changement de disponibilité ou de capacités.
- Diagnostic manuel depuis « Exécuter les actions », sans commande d’éclairage : luminosité, couleurs, blancs de palette, canal blanc, température native et transitions.
- Les IKEA en mode `xy` conservent les blancs de la palette ; une ampoule sans couleur est refusée et une indisponibilité reste un contrôle en attente.
- Lissage natif des maintiens, cadence alignée sur l’horloge et arrêt au niveau intermédiaire estimé lors du relâchement ou d’une inversion de sens.
- Transitions de couleur indépendantes, repli par pas si les fondus ne sont pas déclarés, mémoire 1.0.0 reprise automatiquement.
- Tests avec modèle de fondu indépendant et documentation bilingue des limites de configuration et de mesure.

## Lampe STYRBAR — 1.0.0 — 4 novembre 2026

Première version publiée de **Lampe avec télécommande IKEA STYRBAR — ZHA**.

- Un blueprint par lampe, avec un assistant Texte distinct et sans package partagé.
- Marche/arrêt, variation bornée par maintien, 23 préréglages disponibles et rappel RGB configurable.
- Trois blancs Home Assistant de référence ; couleurs et blancs historiques IKEA envoyés en xy.
- Double appui en haut si le micrologiciel transmet deux événements, maintien latéral de rappel configurable.
- Commandes sérialisées, arrêt si le relâchement manque, exclusion des commandes trop anciennes et annulation après une erreur ou une indisponibilité.
- Documentation française et anglaise, exemples fictifs et tests natifs isolés.

## Surveillance des intégrations — 1.0.1 — 4 novembre 2026

- Correction du chargement des scripts depuis un package Home Assistant : les sélecteurs restent présents après la fusion de configuration.
- Ajout d’un test qui fusionne le package avec une configuration existante puis valide chaque script.

## Surveillance des intégrations — 1.0.0 — 4 novembre 2026

Première version publiée du blueprint **Surveillance et relance des intégrations**.

- Configuration depuis le formulaire Home Assistant, avec un assistant Texte pour conserver l’historique.
- Jusqu’à 50 relances simultanées, avec attente sans tentative comptée lorsque toutes les places sont occupées.
- Nombre de tentatives et délais réglables, notifications, journaux, exclusions et mode observation.
- Protection contre les relances en double et conservation des résultats après interruption.
- Exemples fictifs Netatmo, TaHoma et Cozytouch.
- Documentation française et anglaise, 88 tests et vérification automatique sur GitHub Actions.

La version de chaque blueprint est indiquée dans son fichier `src/<nom>/VERSION`. Les révisions utilisées pendant la préparation ne sont pas des versions publiées.
