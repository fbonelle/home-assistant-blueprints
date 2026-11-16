# Historique

**Français** · [English](CHANGELOG.en.md)

## Télécommandes d’éclairage — 1.0.4 — 16 novembre 2026

- Correction : l’option « Journaliser » écrivait au niveau INFO, masqué par défaut dans Home Assistant ; les messages n’apparaissaient qu’après configuration du journal. L’automatisation règle désormais elle-même le niveau du journal `lighting_remote`.
- Une erreur d’écriture du journal n’interrompt plus la commande.

## Surveillance et relance des intégrations — 2.0.0 — 15 novembre 2026

- Le blueprint s’installe seul : le fichier de configuration commun (`packages/integration_watchdog.yaml`), ses quatre scripts et ses deux automatisations sont supprimés. Après mise à jour, supprimer ce fichier de Home Assistant ; les surveillances et leurs assistants Texte sont conservés.
- La relance a lieu dans l’exécution de la surveillance, en mode file d’attente ; sa fin ouvre aussitôt la période de vérification.
- Relance trop longue : une branche parallèle envoie l’alerte au bout du délai, sans annuler la relance ; le retour à la normale est ensuite annoncé.
- Relance interrompue (arrêt de Home Assistant, surveillance modifiée ou désactivée) : détectée et close automatiquement ; si l’intégration est restée déchargée, la relance est reprise dans les limites de tentatives. La commande « Confirmer la fin d’une relance » disparaît.
- Plafond de 50 relances simultanées et surveillances en double : réservation inscrite puis comparée dans les assistants, sans file commune ni dépassement possible.
- Remise à zéro des tentatives d’une panne : « Exécuter les actions » sur l’automatisation remplace le script dédié.
- Journal `integration_watchdog` : la surveillance règle elle-même son niveau ; il est écrit après les alertes.

## Télécommandes d’éclairage — 1.0.3 — 15 novembre 2026

- Correction : quand un groupe et ses membres sont tous sur le Tap Dial, la molette pouvait agir sur le groupe après l’allumage d’un seul membre, et allumer les autres. Parmi les lampes changées presque en même temps, celle que la télécommande a commandée l’emporte.
- Tap Dial : une lampe indisponible n’est plus choisie par la molette ; un sens de rotation inconnu est ignoré au lieu d’être lu comme une rotation vers la gauche.
- Filtre des événements trop rapprochés sans assistant de mémoire : un doublon n’échappe plus au filtre quand Home Assistant enregistre l’exécution précédente quelques millisecondes après son arrivée.

## Télécommandes d’éclairage — 1.0.2 — 15 novembre 2026

- Correction : l’amplitude de la molette du Hue Tap Dial était lue en pour cent alors que la commande Zigbee l’exprime en unités de luminosité (0 à 255) ; une rotation rapide sautait directement au maximum ou au minimum. Elle est maintenant convertie : environ 3 % pour un cran lent, jusqu’à 80 % pour une rotation rapide.
- Tap Dial : filtre des événements trop rapprochés activé par défaut (100 ms). Il écarte les appuis reçus deux fois et les rapports de rotation de sens opposés émis à quelques millisecondes d’intervalle.
- Tests reprenant les valeurs relevées sur une vraie télécommande.

## Télécommandes d’éclairage — 1.0.1 — 15 novembre 2026

- Correction : la molette du Hue Tap Dial était toujours lue dans le même sens, avec un pas fixe. ZHA transmet le sens de rotation et d’autres champs sous forme d’énumérations zigpy (`StepMode.Down`), que Home Assistant 2026.11 ne savait pas relire : tous les paramètres de l’événement étaient perdus. Les valeurs sont maintenant converties en nombres, booléens ou textes avant usage, pour toutes les télécommandes.
- Test reproduisant les valeurs zigpy réelles.

## Télécommandes d’éclairage et extinction automatique — 1.0.0 — 15 novembre 2026

Première version publiée de la famille **Télécommandes d’éclairage** et du blueprint **Extinction automatique de l’éclairage**.

- Un blueprint par modèle ZHA : Philips Hue Dimmer (RWL022), Philips Hue Tap Dial (RDM002), interrupteur IKEA TRÅDFRI marche/arrêt, télécommandes IKEA TRÅDFRI 5 boutons et STYRBAR, bouton eWeLink / SONOFF.
- Retrait de l’ancien blueprint **Lampe avec télécommande IKEA STYRBAR**, de son script partagé, de ses exemples et de ses tests : la télécommande STYRBAR de la famille le remplace.
- STYRBAR : toutes les fonctions et tous les réglages par défaut de l’ancien blueprint (double appui, couleur de rappel, vitesse en %/s, cadences séparées, arrêt au niveau atteint, filtre des doublons, diagnostic), sans script partagé ; l’ancien assistant Texte est repris tel quel.
- Assistant de mémoire facultatif : double appui sur les télécommandes IKEA, position exacte dans la palette, rejet des événements désordonnés, arrêt au niveau atteint ; jamais d’écrasement d’un assistant illisible ou partagé.
- Diagnostic par « Exécuter les actions » et contrôle de la configuration pour toutes les télécommandes.
- Un moteur commun intégré à la construction : même liste d’actions pour chaque geste, mêmes réglages, action personnalisée par geste.
- Variations continues bornées par une durée maximale ; un relâchement ou un autre geste les arrête ; les événements sans action n’interrompent rien.
- Baisse de luminosité limitée à un minimum, sans extinction ; température du blanc en kelvins, bornée aux limites de chaque lampe.
- Palette de 44 préréglages envoyés dans leur format d’origine ; sans mémoire, le préréglage suivant est déduit de la couleur actuelle de la lampe.
- Tap Dial : la molette agit sur la dernière lampe allumée, sans assistant de mémoire.
- Bouton eWeLink lu dans ses commandes, jamais dans les rapports d’état.
- Extinction automatique avec ou sans assistant Minuteur, annulation à l’extinction manuelle et reprise au démarrage.
- Tests natifs Home Assistant 2026.10.4 avec de vraies lampes, de vrais minuteurs et les formats d’événements des profils zha-quirks.

## Système de notifications — 1.0.0 — 15 novembre 2026

Première version publiée du **Système de notifications**, en quatre blueprints : répartiteur, envoi sur un canal, lecture vocale et relais vers le mobile.

- Point d’entrée unique aux champs title, message, level, target, entity_id, tts et data ; canaux par niveau réglables (application mobile, ntfy, e-mail) et journal de bord.
- Chaque canal est envoyé par un script séparé qui renvoie « success » : bascule de ntfy vers l’application mobile, avertissement si l’e-mail échoue, sans bloquer les autres canaux.
- Anti-doublon sur une fenêtre fixe et 10 messages retenus, escalade de niveau toujours transmise, mémoire illisible jamais bloquante.
- Nuit silencieuse, percée du mode silencieux en critique (iOS et Android), liens et pièces jointes adaptés à chaque canal, identifiants sys_disp_ normalisés une seule fois pour l’effacement 1:1.
- Lecture vocale en file d’attente sur les enceintes étiquetées, volume et restauration en critique, interrupteur de silence.
- Relais des notifications persistantes avec niveau déduit du titre, sans boucle, préfixes jamais relayés et préfixes supprimés automatiquement.
- Tests natifs Home Assistant 2026.10.4 avec les quatre blueprints réunis.

## Surveillance des piles et batteries — 1.0.0 — 12 novembre 2026

Première version publiée de **Surveillance des piles et batteries**.

- Alerte immédiate, une seule fois par appareil : pile sous le seuil, appareil muet au-delà d’un délai, alerte « pile faible » binaire.
- Mémoire dans une liste de tâches locale, sans limite de taille : pas de nouvelle alerte quand une pile continue de baisser, oscille autour du seuil ou devient indisponible pendant un redémarrage. Un élément coché quitte le récapitulatif jusqu’au remplacement ; les éléments ajoutés à la main sont ignorés.
- Récapitulatif à l’heure et aux jours choisis, envoi manuel par « Exécuter les actions », notification persistante tenue à jour.
- Exclusions par défaut des téléphones, montres, ordinateurs et onduleurs (mobile_app, icloud, icloud3, nut, Apple), complétées par entité, appareil ou étiquette.
- Actions de notification libres avec titre, message et listes fournis ; conditions supplémentaires facultatives.
- Tests natifs Home Assistant 2026.10.4 : registres réels, mémoire, exclusions, récapitulatif, éléments cochés et 80 appareils simultanés.

## Lampe STYRBAR — 1.0.0 — 4 novembre 2026

Première version publiée de **Lampe avec télécommande IKEA STYRBAR — ZHA**.

- Un blueprint par lampe, avec un assistant Texte distinct, et un petit script partagé en YAML natif pour les impulsions rapides. Installer `packages/ikea_styrbar_light.yaml` avant le blueprint ; aucun composant personnalisé.
- Marche/arrêt, 23 préréglages disponibles et rappel RGB configurable. Trois blancs Home Assistant de référence ; couleurs et blancs historiques IKEA envoyés en xy.
- Vitesse de luminosité explicite en points par seconde, initialement 35 : environ 3 secondes sur toute la plage. Anciens paramètres pas/intervalle dans une section avancée pour la vitesse 0.
- Défilement continu de la palette par maintien gauche/droite, avec un intervalle de couleur indépendant, initialement 0,4 seconde. Le double appui en haut conserve le rappel ; le rappel latéral est facultatif, car il remplace le défilement de ce côté.
- Contrôle des capacités à l’activation, avant les commandes et lors d’un changement de disponibilité ou de capacités. Diagnostic manuel depuis « Exécuter les actions », sans commande d’éclairage. Les IKEA en mode `xy` conservent les blancs de la palette ; une ampoule sans couleur est refusée et une indisponibilité reste un contrôle en attente.
- Lissage natif des maintiens, cadence alignée sur l’horloge et arrêt au niveau intermédiaire estimé lors du relâchement ou d’une inversion de sens. Transitions de couleur indépendantes, repli par pas si les fondus ne sont pas déclarés.
- Commandes sérialisées, rejet des impulsions anciennes ou étrangères, arrêt au relâchement ou à l’expiration du maintien, annulation après une erreur ou une indisponibilité. Le script partagé ne commande aucune lampe.
- Documentation française et anglaise, exemples fictifs et tests natifs isolés, avec modèle de fondu indépendant et script partagé réel.

## Surveillance des intégrations — 1.0.0 — 4 novembre 2026

Première version publiée du blueprint **Surveillance et relance des intégrations**.

- Configuration depuis le formulaire Home Assistant, avec un assistant Texte pour conserver l’historique.
- Jusqu’à 50 relances simultanées, avec attente sans tentative comptée lorsque toutes les places sont occupées.
- Nombre de tentatives et délais réglables, notifications, journaux, exclusions et mode observation.
- Protection contre les relances en double et conservation des résultats après interruption.
- Scripts communs chargés depuis un package Home Assistant, sélecteurs conservés après la fusion de configuration.
- Exemples fictifs Netatmo, TaHoma et Cozytouch.
- Documentation française et anglaise, 89 tests et vérification automatique sur GitHub Actions.

La version de chaque blueprint est indiquée dans son fichier `src/<nom>/VERSION`. Les révisions utilisées pendant la préparation ne sont pas des versions publiées.
