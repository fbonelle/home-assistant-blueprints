# Surveillance et relance des intégrations — 1.0.0

**Français** · [English](integration_watchdog.en.md) · [Accueil](../README.md)

Ce blueprint vérifie les entités que vous choisissez et tente de relancer leur intégration lorsqu’une panne est détectée. Si les tentatives ne suffisent pas, il envoie une notification pour demander une intervention.

Il utilise l’action standard `homeassistant.reload_config_entry`. L’intégration doit prendre en charge cette action. Home Assistant **2026.10 minimum** est requis ; les tests utilisent **2026.10.4**.

## 1. Installer les deux fichiers nécessaires

### Le fichier de configuration commun

Ce fichier regroupe les scripts et automatisations partagés par toutes les surveillances. Il s’installe une seule fois, quel que soit le nombre d’intégrations à surveiller.

1. Créez le dossier `/config/packages` s’il n’existe pas.
2. Enregistrez [integration_watchdog.yaml](../packages/integration_watchdog.yaml) dans ce dossier.
3. Dans `configuration.yaml`, activez les packages :

```yaml
homeassistant:
  packages: !include_dir_named packages
```

Si votre fichier contient déjà un bloc `homeassistant:`, ajoutez `packages:` à l’intérieur au lieu de créer un second bloc. Si les packages sont déjà activés, utilisez le dossier déclaré dans votre configuration.

Le fichier commun ne crée aucune surveillance automatiquement. Conservez les noms des scripts et automatisations qu’il contient.

### Le blueprint

[Importer le blueprint dans Home Assistant](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fintegration_watchdog%2Fsurveillance_integrations.yaml)

Vous pouvez aussi ouvrir **Paramètres → Automatisations et scènes → Blueprints → Importer un blueprint**, puis coller [son adresse GitHub](../blueprints/automation/integration_watchdog/surveillance_integrations.yaml).

Pour une installation manuelle, copiez ce fichier dans `/config/blueprints/automation/local/surveillance_integrations.yaml`.

Activez ensuite l’intégration **Uptime** si elle n’est pas présente, vérifiez la configuration de Home Assistant et redémarrez-le pour charger le fichier commun. Uptime fournit la date de démarrage utilisée pour laisser les intégrations se connecter avant toute tentative.

## 2. Créer une surveillance

### Créer l’assistant Texte

Dans **Paramètres → Appareils et services**, ouvrez la création des assistants (*Helpers* dans l’interface anglaise), puis choisissez **Texte**.

- Donnez-lui un nom, par exemple « Historique de surveillance Netatmo ».
- Réglez la longueur minimale à **0** et la maximale à **255**.
- Choisissez le mode **Texte**.

L’automatisation remplit cet assistant. Il conserve le nombre de tentatives et l’état de la relance après un redémarrage normal. Ne modifiez pas sa valeur manuellement.

### Remplir le formulaire

Créez une automatisation à partir du blueprint **Surveillance et relance des intégrations — 1.0.0**, puis renseignez :

| Champ | Ce qu’il faut choisir |
|---|---|
| Configuration de l’intégration à surveiller | Le compte ou la passerelle concernés. |
| Entités à surveiller | Des entités actives de cette intégration, par exemple une température ou un thermostat. |
| Assistant Texte pour conserver l’historique | L’assistant créé à l’étape précédente. |
| Capteur Uptime de Home Assistant | Le capteur fourni par l’intégration Uptime. |

Donnez un nom à la surveillance, adaptez les réglages si nécessaire et enregistrez. Vous pouvez commencer avec **Observer sans relancer l’intégration** pour vérifier le comportement dans les journaux.

Créez une seule surveillance par configuration d’intégration. Deux comptes ou deux passerelles d’une même intégration se configurent séparément : TaHoma et Cozytouch sont par exemple deux configurations Overkiz distinctes.

## 3. Ajouter d’autres intégrations

Créez un autre assistant Texte et une autre automatisation depuis le même blueprint. Il n’y a aucun script à recopier et aucun redémarrage à faire pour cet ajout.

Le blueprint ne fixe pas de nombre maximal d’intégrations surveillées. Il permet jusqu’à **50 relances simultanées**. Les demandes supplémentaires attendent une place, sans consommer de tentative.

Les [exemples Netatmo, TaHoma et Cozytouch](../examples/integration_watchdog/) contiennent des identifiants fictifs. Adaptez-les avant utilisation. Leur chemin `local/surveillance_integrations.yaml` correspond à l’installation manuelle ; si vous avez importé le blueprint depuis GitHub, utilisez le chemin affiché par Home Assistant.

## Choisir les bons réglages

| Réglage | Valeur par défaut |
|---|---|
| Fréquence de vérification | Toutes les minutes |
| Durée minimale de la panne avant une tentative | 5 minutes |
| Attente après le démarrage de Home Assistant | 10 minutes |
| Tentatives maximales pour une même panne | 3 |
| Tentatives maximales sur les dernières 24 heures | 6 |
| Temps laissé à l’intégration après une relance | 10 minutes |
| Fonctionnement normal avant confirmation | 3 minutes |
| Fonctionnement normal avant remise à zéro des tentatives de la panne | 30 minutes |
| Attente entre deux nouvelles tentatives | De 5 minutes à 1 heure, selon les échecs précédents |
| Délai avant alerte si une relance ne se termine pas | 3 minutes |

Les délais sont évalués lors des vérifications : une action peut attendre le contrôle suivant. La limite sur les dernières 24 heures est conservée quand le compteur de la panne est remis à zéro.

**Entités en erreur.** Vous pouvez attendre que toutes soient en erreur, ou intervenir dès qu’au moins une l’est suffisamment longtemps. L’état `unavailable` signifie « indisponible ». L’état `unknown` signifie « inconnu » : il ne déclenche une tentative que si son option est activée, et ne confirme jamais un retour à la normale.

**Absence de nouvelles données.** Le contrôle est désactivé par défaut : son délai vaut **0**. Activez-le pour des mesures envoyées régulièrement. Pour un volet immobile ou un thermostat dont la valeur change peu, gardez 0 sauf si l’intégration fournit une date de mesure fiable. Sans cette date, le contrôle mesure les données reçues par Home Assistant, pas leur fraîcheur réelle chez le fournisseur.

**Retour à la normale.** Toutes les entités surveillées doivent fonctionner pendant la durée de confirmation, même si une seule entité en erreur suffit à déclencher une tentative. Une amélioration très brève ne remet pas le nombre de tentatives à zéro.

## Notifications et journaux

Par défaut, une notification apparaît dans Home Assistant lorsqu’une intervention est nécessaire. Elle est effacée après un retour confirmé à la normale. Vous pouvez remplacer ces actions par vos propres notifications dans le formulaire.

Les événements utiles sont écrits dans le journal `integration_watchdog`. Les journaux détaillés ajoutent les vérifications de routine ; utilisez-les pour comprendre un problème. Une erreur d’écriture du journal ne bloque pas l’envoi des alertes.

Les exclusions, le mode observation et les conditions supplémentaires empêchent de nouvelles tentatives. Ils n’annulent pas une relance déjà en cours.

## Si une intervention manuelle est nécessaire

Si une relance ne se termine pas, vérifiez les erreurs de l’intégration et les traces du script dans Home Assistant. L’alerte n’annule pas l’opération : aucune autre tentative n’est envoyée tant que sa fin n’est pas connue.

Après avoir vérifié qu’elle est terminée, lancez **Surveillance — Confirmer la fin d’une relance** et choisissez l’assistant Texte concerné. Cette action reste bloquée si le script de relance tourne encore, y compris pour une autre intégration.

**Surveillance — Réinitialiser les tentatives pour une panne** permet de réessayer après une intervention. Le nombre de tentatives des dernières 24 heures reste conservé. Cette remise à zéro n’est pas possible pendant une relance en cours.

## À connaître

- Le bon fonctionnement dépend des entités choisies. Une panne cloud peut ne pas rendre ces entités indisponibles.
- La sélection des intégrations est manuelle ; il n’y a pas de détection automatique de toutes les intégrations cloud.
- Home Assistant doit rester réactif pour que ses automatisations fonctionnent. Un arrêt brutal peut perdre la toute dernière mise à jour de l’historique.
- Les tests simulent les appels aux fournisseurs ; ils ne prouvent pas qu’une panne réelle Netatmo ou Overkiz sera réparée.

[Fonctionnement détaillé, tests et limites](robustesse_integration_watchdog.md)

Documentation Home Assistant : [packages](https://www.home-assistant.io/docs/configuration/packages/), [assistant Texte](https://www.home-assistant.io/integrations/input_text/), [importation d’un blueprint](https://www.home-assistant.io/docs/automation/using_blueprints/).
