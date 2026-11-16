# Fonctionnement, tests et limites — 2.0.0

**Français** · [English](robustesse_integration_watchdog.en.md) · [Guide d’installation](integration_watchdog.md)

Cette page décrit les protections de la surveillance et leur vérification. Le guide d’installation suffit pour configurer une surveillance.

## Un seul fichier

Le blueprint ne dépend d’aucun fichier de configuration, script ou automatisation commune. Chaque surveillance fait tout elle-même : contrôle, décision, relance, alertes et journaux. Ses seules données sont celles de son assistant Texte.

Chaque surveillance fonctionne en mode file d’attente : une seule exécution à la fois. Elle est donc la seule à écrire dans son assistant, et chaque écriture est relue pour vérification. Les déclenchements qui arrivent pendant une exécution attendent leur tour, dans une limite de 10 ; les suivants sont ignorés sans message, car chaque exécution relit tout l’état et rien n’est perdu.

## Tentatives et délais

Une tentative est comptée lorsque la relance est acceptée, juste avant l’appel. Deux limites s’appliquent : le nombre de tentatives pour une même panne et celui des dernières 24 heures. Le retour durable à la normale remet seulement le premier compteur à zéro. Les relances lancées manuellement ou par d’autres automatisations ne sont pas comptées.

La limite de 6 tentatives sur 24 heures permet de conserver l’historique dans un seul assistant Texte de 255 caractères.

## Relance dans l’exécution

La relance a lieu dans l’exécution de la surveillance. Dès qu’elle se termine, la même exécution enregistre sa fin et ouvre la période de vérification, sans attendre le contrôle suivant.

Pendant la relance, une branche parallèle surveille le délai prévu. S’il est dépassé, elle envoie l’alerte « relance trop longue ». Elle ne fait que lire l’historique : elle ne peut donc pas entrer en conflit avec l’enregistrement de la fin. La relance n’est pas annulée. Quand elle se termine enfin, l’alerte est mémorisée, si bien que le retour à la normale est annoncé.

Une relance bloquée n’arrête que sa propre surveillance : il n’y a rien d’autre à faire pour cette intégration tant qu’elle n’est pas terminée. Les autres surveillances continuent.

## Relance interrompue

Arrêter une exécution annule l’action en cours, y compris une relance. Cela arrive si Home Assistant s’arrête, ou si la surveillance est modifiée, désactivée ou mise à jour pendant une relance. Recharger les automatisations sans modifier celle-ci ne l’interrompt pas.

L’exécution suivante le détecte sans ambiguïté : en mode file d’attente, aucune autre exécution ne peut être en cours, donc une relance marquée « lancée » a forcément été interrompue.

- La tentative reste comptée.
- Si l’intégration est chargée, la période de vérification s’ouvre normalement.
- Si l’intégration est restée déchargée, la relance est reprise aussitôt, dans les limites de tentatives. Sans cette reprise, l’intégration resterait arrêtée, car une intégration déchargée n’est jamais relancée d’office.
- Une réservation qui n’avait pas encore été acceptée est simplement abandonnée, sans tentative comptée.

Aucune commande manuelle n’est nécessaire. **Exécuter les actions** sur l’automatisation remet à zéro les tentatives de la panne en cours, sans effacer l’historique des 24 heures, puis vérifie aussitôt.

## Plafond de 50 relances et doublons

Le plafond de 50 relances simultanées et la détection des surveillances en double reposent sur une réservation dans les assistants eux-mêmes, sans file commune.

1. La surveillance qui décide une relance inscrit d’abord sa réservation dans son assistant.
2. Elle lit ensuite les réservations des autres surveillances.
3. Elle compte les relances déjà acceptées et les réservations inscrites avant la sienne, d’après l’heure d’écriture enregistrée par Home Assistant.

Comme chaque surveillance écrit avant de lire, la plus tardive de deux surveillances voit toujours la plus ancienne : toutes obtiennent le même ordre et seules les 50 premières démarrent. Si deux réservations portent exactement la même heure, toutes les surveillances concernées repassent une minute plus tard, afin qu’aucun dépassement ne soit possible. Une demande reportée ne consomme pas de tentative.

Deux surveillances de la même intégration ne relancent jamais ensemble : la réservation de l’autre suffit à reporter la demande, et la configuration en double est signalée.

Une réservation de plus d’une heure appartient à une surveillance qui ne s’est pas exécutée depuis, par exemple une automatisation désactivée. Elle ne compte plus dans le plafond.

## Arrêts normaux

L’historique est restauré après un arrêt normal de Home Assistant. Une coupure brutale peut perdre sa toute dernière mise à jour. Au démarrage, une relance interrompue est traitée comme décrit plus haut.

## Notifications et journaux

Une notification est marquée comme envoyée après réussite de son action. Elle peut être répétée si Home Assistant s’arrête avant cet enregistrement. Il n’existe pas de garantie d’envoi exactement une fois à un service externe.

Le journal `integration_watchdog` est écrit après les alertes et leur enregistrement : une erreur de journalisation ne peut pas les bloquer. La surveillance règle elle-même le niveau de ce journal (info, ou debug avec les journaux détaillés) ; les intégrations de journalisation de Home Assistant sont toujours chargées.

Les actions personnalisées doivent rester courtes : une action qui ne se termine pas bloque sa propre surveillance.

## Ce que vérifient les tests

La suite contient **85 tests** exécutés sous Home Assistant officiel **2026.10.4**, avec Python **3.14**, dans des dossiers temporaires.

Les automatisations, assistants, modèles et notifications sont réels. Seules les relances d’intégration sont remplacées par des réponses contrôlées ; les intégrations et entités utilisées sont fictives.

Les scénarios couvrent notamment :

- 51 demandes simultanées : 50 relances distinctes et une demande reportée ;
- le plafond plein, et les réservations anciennes qui ne comptent plus ;
- une relance trop longue : alerte après le délai, relance non annulée, retour à la normale annoncé ;
- une relance interrompue, avec une intégration chargée ou restée déchargée, en exécution directe et avec une vraie automatisation désactivée puis réactivée ;
- un redémarrage pendant une relance, sans remboursement de la tentative ;
- deux surveillances concurrentes de la même intégration et des exécutions simultanées de la même surveillance ;
- les limites de tentatives, les délais, les exclusions, le mode observation et la remise à zéro par **Exécuter les actions** ;
- les données incorrectes, les notifications en erreur et un journal en erreur ou absent ;
- les dates de mesure, les changements d’Uptime et un retour en arrière de l’horloge ;
- les demandes de réauthentification et les reconnexions déjà gérées par Home Assistant ;
- le réglage du niveau du journal par la surveillance elle-même.

GitHub Actions exécute les tests et vérifie que les YAML distribués correspondent à leurs sources.

## Limites à garder en tête

Une intégration peut rester disponible tout en renvoyant des données incorrectes ou en ne répondant plus à certaines commandes. Le blueprint ne peut détecter que les problèmes visibles dans les entités et dates choisies. Les changements très brefs entre deux contrôles peuvent ne pas être vus.

Les demandes de réauthentification sont détectées via les réparations standard de Home Assistant. Certains composants tiers utilisent d’autres mécanismes qui peuvent ne pas apparaître dans cette liste.

Une panne de Home Assistant lui-même, de son stockage ou de son serveur peut empêcher les contrôles. Les tests ne prouvent pas l’efficacité d’une relance sur une panne réelle chez un fournisseur.
