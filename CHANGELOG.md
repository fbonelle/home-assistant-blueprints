# Historique

**Français** · [English](CHANGELOG.en.md)

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
