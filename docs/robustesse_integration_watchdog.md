# Fonctionnement, tests et limites — 1.0.1

**Français** · [English](robustesse_integration_watchdog.en.md) · [Guide d’installation](integration_watchdog.md)

Cette page décrit les protections de la première version et leur vérification. Le guide d’installation suffit pour configurer une surveillance.

## Tentatives et délais

Une tentative est comptée lorsque le système accepte de lancer une relance. Si les 50 places sont occupées, la demande attend une nouvelle vérification après au moins 60 secondes, sans augmenter le compteur.

Deux limites s’appliquent : le nombre de tentatives pour une même panne et celui des dernières 24 heures. Le retour durable à la normale remet seulement le premier compteur à zéro. Les relances lancées manuellement ou par d’autres automatisations ne sont pas comptées.

La limite de 6 tentatives sur 24 heures permet de conserver l’historique dans un seul assistant Texte de 255 caractères.

## Éviter les relances en double

L’assistant est associé à une seule configuration d’intégration et à son automatisation. Une autre surveillance liée à la même configuration provoque une erreur de configuration avant de nouvelles relances.

Le lancement d’une demande suit plusieurs étapes enregistrées. Une demande reçue deux fois ne peut pas déclencher deux appels. Les demandes sont traitées dans l’ordre avant le démarrage des scripts, qui peuvent ensuite fonctionner en parallèle.

Les identifiants internes des scripts et des automatisations restent fixes pour permettre leur appel. Les noms affichés peuvent être plus explicites sans changer ces identifiants.

## Conserver les résultats sans perdre une mise à jour

Toutes les écritures de l’historique passent par un script commun. Il vérifie que la valeur n’a pas changé depuis sa lecture, écrit la nouvelle valeur et contrôle le résultat. En cas de modification concurrente, il relit l’état, jusqu’à cinq essais. Si l’écriture reste impossible, une alerte est envoyée et aucune nouvelle relance n’est demandée.

La fin d’une relance est enregistrée avant l’envoi du signal qui réveille sa surveillance. Si ce signal est perdu, le contrôle périodique retrouve le résultat. Une notification lente ne peut pas remplacer ce résultat par une ancienne copie de l’historique.

La date de fin est arrondie à la seconde supérieure. Un rapport reçu avant la fin réelle ne peut donc pas être considéré comme postérieur. Un rapport reçu juste après cette fin peut aussi être écarté pendant moins d’une seconde ; il faut alors attendre le suivant.

## Arrêts et opérations manuelles

Un simple changement du capteur Uptime ne permet pas d’autoriser une deuxième relance. La reprise d’une demande interrompue utilise le véritable déclencheur de démarrage de Home Assistant et vérifie que le script commun est arrêté.

Si cette reprise n’a pas pu se faire, la demande reste bloquée jusqu’à une confirmation manuelle. La commande de confirmation vérifie aussi l’arrêt du script au moment d’enregistrer le résultat, pour éviter un démarrage simultané.

L’historique est restauré après un arrêt normal de Home Assistant. Une coupure brutale peut perdre sa toute dernière mise à jour. Les scripts ne tentent pas d’annuler de force un appel bloqué.

## Notifications et journaux

L’enregistrement des journaux s’effectue dans une automatisation séparée. Une erreur du service de journalisation, ou son absence, ne bloque donc pas les notifications de panne.

Une notification est marquée comme envoyée après réussite de son action. Elle peut être répétée si Home Assistant s’arrête avant cet enregistrement, ou si l’enregistrement échoue plusieurs fois. Il n’existe pas de garantie d’envoi exactement une fois à un service externe.

Les actions personnalisées doivent rester courtes. Si elles ne se terminent pas, elles peuvent bloquer leur propre automatisation, même si les relances et les journaux ont été séparés.

## Ce que vérifient les tests

La suite contient **89 tests** exécutés sous Home Assistant officiel **2026.10.4**, avec Python **3.14**, dans des dossiers temporaires.

Les scripts, automatisations, assistants, modèles, événements et notifications sont réels. Seuls les appels aux fournisseurs sont remplacés par des réponses contrôlées ; les intégrations et entités utilisées sont fictives.

Les scénarios couvrent notamment :

- 51 demandes simultanées : 50 relances distinctes et une demande reportée ;
- les limites de tentatives, les délais, les exclusions et le mode observation ;
- les redémarrages après interruption et les signaux de fin perdus ;
- deux surveillances concurrentes de la même intégration et le renvoi d’une même demande ;
- les écritures refusées, les données incorrectes et les notifications lentes ou en erreur ;
- les dates de mesure, les changements d’Uptime et un retour en arrière de l’horloge ;
- les demandes de réauthentification et les reconnexions déjà gérées par Home Assistant.

GitHub Actions exécute les tests et vérifie que les YAML distribués correspondent à leurs sources. Les avertissements de dépréciation des dépendances sont visibles dans les résultats.

## Limites à garder en tête

Une intégration peut rester disponible tout en renvoyant des données incorrectes ou en ne répondant plus à certaines commandes. Le blueprint ne peut détecter que les problèmes visibles dans les entités et dates choisies. Les changements très brefs entre deux contrôles peuvent ne pas être vus.

Les files d’attente sont limitées : 100 exécutions ou attentes par surveillance et 1 000 pour les services communs courts. Leur dépassement apparaît dans les journaux. Une demande perdue reste bloquée par précaution, sans tentative comptée si elle n’a pas été acceptée, puis provoque une alerte.

Les demandes de réauthentification sont détectées via les réparations standard de Home Assistant. Certains composants tiers utilisent d’autres mécanismes qui peuvent ne pas apparaître dans cette liste.

Une panne de Home Assistant lui-même, de son stockage ou de son serveur peut empêcher les contrôles. Les tests ne prouvent pas l’efficacité d’une relance sur une panne réelle chez un fournisseur.
