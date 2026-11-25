# Integration watchdog — surveillance et relance des intégrations — 2026.11.3.0

**Français** · [English](integration_watchdog.en.md) · [Accueil](../README.md)

Ce blueprint vérifie les entités que vous choisissez et tente de relancer leur intégration lorsqu’une panne est détectée. Si les tentatives ne suffisent pas, il envoie une notification pour demander une intervention. Le formulaire et les messages du blueprint sont en anglais ; ce guide cite ses libellés tels qu’ils apparaissent.

Il utilise l’action standard `homeassistant.reload_config_entry`. L’intégration doit prendre en charge cette action. Home Assistant **2026.10 minimum** est requis ; les tests tournent sur la version testée et sur cette version minimale (voir le [README](../README.md#développement)).

## 1. Importer le blueprint

[Importer le blueprint dans Home Assistant](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fintegration_watchdog%2Fintegration_watchdog.yaml)

Vous pouvez aussi ouvrir **Paramètres → Automatisations et scènes → Blueprints → Importer un blueprint**, puis coller [son adresse GitHub](../blueprints/automation/integration_watchdog/integration_watchdog.yaml). Pour une installation manuelle, copiez ce fichier dans `/config/blueprints/automation/local/integration_watchdog.yaml`.

C’est le seul fichier à installer : aucun fichier de configuration, aucun script ni redémarrage. Activez l’intégration **Uptime** si elle n’est pas présente ; elle fournit la date de démarrage utilisée pour laisser les intégrations se connecter avant toute tentative.

## 2. Créer une surveillance

### Créer l’assistant Texte

Dans **Paramètres → Appareils et services**, ouvrez la création des assistants (*Helpers* dans l’interface anglaise), puis choisissez **Texte**.

- Donnez-lui un nom, par exemple « Historique de surveillance Netatmo ».
- Réglez la longueur minimale à **0** et la maximale à **255**.
- Choisissez le mode **Texte**.

L’automatisation remplit cet assistant. Il conserve le nombre de tentatives et l’état de la relance après un redémarrage normal. Ne modifiez pas sa valeur manuellement.

### Remplir le formulaire

Créez une automatisation à partir du blueprint **Integration watchdog — 2026.11.3.0**, puis renseignez, dans la section **Integration and entities to watch** :

| Champ | Ce qu’il faut choisir |
|---|---|
| Configuration of the integration to watch | Le compte ou la passerelle concernés. |
| Entities to watch | Des entités actives de cette intégration, par exemple une température ou un thermostat. |
| Text helper that keeps the history | L’assistant créé à l’étape précédente. |
| Home Assistant Uptime sensor | Le capteur fourni par l’intégration Uptime. |

Donnez un nom à la surveillance (**Name in notifications**), adaptez les réglages si nécessaire et enregistrez. Vous pouvez commencer avec **Observe without reloading the integration** pour vérifier le comportement dans les journaux.

Créez une seule surveillance par configuration d’intégration. Deux comptes ou deux passerelles d’une même intégration se configurent séparément : TaHoma et Cozytouch sont par exemple deux configurations Overkiz distinctes.

## 3. Ajouter d’autres intégrations

Créez un autre assistant Texte et une autre automatisation depuis le même blueprint. Aucun autre fichier ni redémarrage n’est nécessaire.

Le blueprint ne fixe pas de nombre maximal d’intégrations surveillées. Il limite à **50** le nombre de relances simultanées, toutes surveillances confondues. Une demande supplémentaire réessaie une minute plus tard, sans consommer de tentative.

Les [exemples Netatmo, TaHoma et Cozytouch](../examples/integration_watchdog/) contiennent des identifiants fictifs. Adaptez-les avant utilisation. Leur chemin `local/integration_watchdog.yaml` correspond à l’installation manuelle ; si vous avez importé le blueprint depuis GitHub, utilisez le chemin affiché par Home Assistant.

## Choisir les bons réglages

| Réglage | Valeur par défaut |
|---|---|
| Check frequency | Toutes les minutes (*Every minute*) |
| Minimum failure duration before a reload (seconds) | 5 minutes |
| Wait after Home Assistant start-up (seconds) | 10 minutes |
| Maximum number of attempts for one failure | 3 |
| Maximum number of attempts over the last 24 hours | 6 |
| Time given to the integration to recover after a reload (seconds) | 10 minutes |
| Normal operation time before confirmation (seconds) | 3 minutes |
| Normal operation time before the attempts are reset (seconds) | 30 minutes |
| Wait before a new attempt (seconds) · Maximum wait between two attempts (seconds) | De 5 minutes à 1 heure, selon les échecs précédents |
| Delay before an alert when a reload does not finish (seconds) | 3 minutes |

Les délais sont évalués lors des vérifications : une action peut attendre le contrôle suivant. La limite sur les dernières 24 heures est conservée quand le compteur de la panne est remis à zéro.

**Entités en erreur.** Avec **When should the integration be reloaded?**, vous pouvez attendre que toutes soient en erreur (*When every entity is failing*), ou intervenir dès qu’au moins une l’est suffisamment longtemps (*When at least one entity is failing*). L’état `unavailable` signifie « indisponible ». L’état `unknown` signifie « inconnu » : il ne déclenche une tentative que si l’option **Count the « unknown » state as a failure** est activée, et ne confirme jamais un retour à la normale.

**Absence de nouvelles données.** Le contrôle est désactivé par défaut : son délai, **Maximum delay without new data (seconds)**, vaut **0**. Activez-le pour des mesures envoyées régulièrement. Pour un volet immobile ou un thermostat dont la valeur change peu, gardez 0 sauf si l’intégration fournit une date de mesure fiable (**Entity giving the date of the last measurement (optional)**). Sans cette date, le contrôle mesure les données reçues par Home Assistant, pas leur fraîcheur réelle chez le fournisseur.

**Retour à la normale.** Toutes les entités surveillées doivent fonctionner pendant la durée de confirmation, même si une seule entité en erreur suffit à déclencher une tentative. Une amélioration très brève ne remet pas le nombre de tentatives à zéro.

## Notifications et journaux

Par défaut, une notification apparaît dans Home Assistant lorsqu’une intervention est nécessaire. Elle est effacée après un retour confirmé à la normale. Vous pouvez remplacer ces actions par vos propres notifications dans la section **Notifications** du formulaire (**Actions when an intervention is needed**, **Actions after recovery**).

Les événements utiles sont écrits dans le journal `integration_watchdog`. La surveillance règle elle-même son niveau (info, ou debug avec **Enable detailed logs**) : aucune configuration n’est nécessaire. Les journaux détaillés ajoutent les vérifications de routine ; utilisez-les pour comprendre un problème. Les alertes sont envoyées avant l’écriture du journal, qui ne peut donc pas les bloquer.

Les exclusions, le mode observation et les conditions supplémentaires empêchent de nouvelles tentatives. Ils n’annulent pas une relance déjà en cours.

## Si une intervention manuelle est nécessaire

**Relance trop longue.** Si une relance dépasse le délai prévu, une alerte est envoyée. La relance n’est pas annulée : la surveillance attend sa fin, puis reprend normalement et annonce le retour à la normale. Aucune autre relance de cette intégration n’est lancée entre-temps ; les autres surveillances continuent. Vérifiez les erreurs de l’intégration et les traces de l’automatisation.

**Relance interrompue.** Si Home Assistant s’arrête, ou si la surveillance est modifiée ou désactivée pendant une relance, celle-ci est interrompue. La vérification suivante le détecte d’elle-même : la tentative reste comptée, et si l’intégration est restée déchargée, la relance est reprise dans les limites de tentatives. Aucune action manuelle n’est nécessaire.

**Réessayer après une intervention.** Ouvrez l’automatisation de surveillance et choisissez **Exécuter les actions** : le nombre de tentatives pour la panne en cours est remis à zéro, puis une vérification a lieu aussitôt. Le nombre de tentatives des dernières 24 heures reste conservé.

## À connaître

- Le bon fonctionnement dépend des entités choisies. Une panne cloud peut ne pas rendre ces entités indisponibles.
- La sélection des intégrations est manuelle ; il n’y a pas de détection automatique de toutes les intégrations cloud.
- Home Assistant doit rester réactif pour que ses automatisations fonctionnent. Un arrêt brutal peut perdre la toute dernière mise à jour de l’historique.
- Les tests simulent les appels aux fournisseurs ; ils ne prouvent pas qu’une panne réelle Netatmo ou Overkiz sera réparée.

[Fonctionnement détaillé, tests et limites](integration_watchdog_robustness.md)

Documentation Home Assistant : [assistant Texte](https://www.home-assistant.io/integrations/input_text/), [importation d’un blueprint](https://www.home-assistant.io/docs/automation/using_blueprints/).
