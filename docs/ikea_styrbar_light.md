# Lampe avec télécommande IKEA STYRBAR — ZHA

**Français** · [English](ikea_styrbar_light.en.md) · [Accueil](../README.md)

Version **1.2.0**. Un seul blueprint par lampe remplace le couple « contrôleur + hook ». Les maintiens rapides utilisent un petit script partagé en YAML standard, sans composant personnalisé.

## Installation

1. Utiliser Home Assistant **2026.10 ou plus récent**, une STYRBAR intégrée par **ZHA** (modèle `Remote Control N2`) et une lampe prenant en charge les couleurs. Zigbee2MQTT et deCONZ ne sont pas pris en charge par ce blueprint.
2. Installer une seule fois [packages/ikea_styrbar_light.yaml](../packages/ikea_styrbar_light.yaml) dans le dossier des packages déjà inclus par `homeassistant.packages`. Recharger les scripts. Si aucun dossier de packages n’est configuré, suivre la [documentation Home Assistant](https://www.home-assistant.io/docs/configuration/packages/) pour l’activer. Le script attendu est `script.styrbar_maintiens` ; son absence est signalée et bloque les commandes.
3. [Importer le blueprint](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fikea_styrbar_light%2Flampe_styrbar.yaml).
4. Dans **Paramètres → Appareils et services → Entrées**, créer un assistant **Texte**, longueur minimale **0**, maximale **255**. Le réserver à cette automatisation. Chaque autre télécommande doit avoir son propre assistant.
5. Créer une automatisation depuis le blueprint, puis choisir la télécommande, la lampe et l’assistant. Régler la palette et la couleur de rappel.
6. Avant d’activer le nouveau pilotage, désactiver les anciennes automatisations contrôleur et hook de cette télécommande. Vérifier aussi qu’aucune liaison Zigbee directe ou autre automatisation ne commande simultanément la lampe.

Les [exemples d’automatisations](../examples/ikea_styrbar_light/automations.yaml) et d’[assistants YAML](../examples/ikea_styrbar_light/helpers.yaml) utilisent uniquement des identifiants fictifs. Les assistants créés depuis l’interface suffisent : le fichier YAML d’assistants est facultatif. Adapter le chemin du blueprint si Home Assistant propose un autre nom lors de l’importation.

## Vérifier les capacités à la configuration

Le formulaire standard des blueprints ne permet pas d’exécuter un test dès le choix de l’ampoule ou d’empêcher l’enregistrement selon ses attributs. Le contrôle s’exécute après activation/rechargement, avant les commandes, et lorsque les capacités ou la disponibilité de la lampe changent. Une incompatibilité bloque les commandes et crée une notification Home Assistant distincte pour cette automatisation. Une indisponibilité est signalée comme un contrôle en attente, sans conclure que l’ampoule est incompatible.

Pour afficher aussi un résultat positif, ouvrir le **Menu → Exécuter les actions** de l’automatisation. Cette action affiche uniquement un diagnostic : communication, luminosité, couleurs, blancs de la palette, canal blanc distinct, mode température native et sa plage en kelvins lorsqu’elle est fournie, transitions. Elle ne commande pas la lampe et n’interrompt pas un maintien valide. Les notifications de problème sont retirées après un nouveau contrôle automatique concluant.

Une ampoule IKEA déclarant seulement `xy` peut produire les blancs de la palette via son mode couleur. L’absence de `color_temp` ne la rend donc pas incompatible. À l’inverse, une ampoule blanche réglable en kelvins sans mode couleur est refusée par ce blueprint, car ses palettes et son rappel utilisent RGB/xy. Les fondus sont facultatifs : s’ils ne sont pas déclarés, la variation fonctionne par pas et aucun paramètre de transition n’est envoyé.

Ce contrôle repose sur les informations déclarées par l’intégration. Il ne vérifie pas le rendu lumineux ni la fiabilité radio, et les capacités agrégées d’un groupe ne garantissent pas celles de chaque ampoule membre. Aucun éclairage de test n’est envoyé automatiquement à l’enregistrement.

## Boutons

| Geste | Résultat |
|---|---|
| Appui court en haut | Allumer, en conservant la couleur et la luminosité mémorisées par la lampe. Une luminosité imposée est facultative. |
| Appui court en bas | Éteindre. |
| Maintien en haut | Augmenter la luminosité ; depuis l’arrêt, commencer au minimum configuré. |
| Maintien en bas | Diminuer la luminosité jusqu’au minimum, sans éteindre. Ne rallume pas une lampe éteinte. |
| Appui court gauche / droite | Préréglage précédent / suivant, avec retour à l’autre extrémité de la liste. |
| Double appui en haut | Rappeler la couleur configurée, sans imposer de luminosité. |
| Maintien gauche / droite | Faire défiler continuellement la palette dans le sens choisi, à l’intervalle configuré. |
| Geste de rappel supplémentaire | Facultatif : remplacer le défilement d’un côté par le rappel de la couleur par défaut. Aucun côté réservé au rappel par défaut. |
| Relâchement ou autre bouton reconnu | Arrêter la variation en cours. |

Le premier appui en haut est immédiat. Le second, s’il arrive dans le délai configuré, applique la couleur de rappel. Avec une luminosité imposée à l’allumage, le premier appui l’applique avant le rappel ; le rappel ne l’applique pas une seconde fois. Les options **Les flèches de couleur peuvent allumer la lampe** et **Le rappel de couleur peut allumer la lampe** règlent ces deux comportements lorsque la lampe est éteinte.

**Le double appui dépend du micrologiciel de la télécommande.** Certaines STYRBAR filtrent les appuis rapprochés ON/OFF avant leur transmission : si ZHA reçoit un seul événement `on`, aucun blueprint ne peut identifier deux appuis. Réserver alors un maintien latéral au rappel via **Geste de rappel supplémentaire** ; ce côté ne fait plus défiler les couleurs. La [documentation STYRBAR](https://www.zigbee2mqtt.io/devices/E2001_E2002_E2313.html#action-mapping) décrit ce filtrage au niveau de l’appareil ; ses noms d’actions MQTT ne sont pas utilisés par notre blueprint ZHA.

Des micrologiciels émettent aussi une commande `on` pendant un maintien latéral. Elle peut allumer la lampe avant l’événement de maintien. Ne pas utiliser ce geste si l’exigence est de ne jamais rallumer une lampe éteinte ; cette commande radio est indistinguable d’un véritable appui ON.

## Palette et couleur de rappel

Le choix comporte **23 préréglages** : les trois blancs de référence de la capture Home Assistant et les 20 préréglages historiques IKEA (sept blancs, treize couleurs). La palette initiale contient les trois blancs Home Assistant et les treize couleurs IKEA. Les autres blancs sont disponibles dans le formulaire.

| Pastille de référence | RGB envoyé à Home Assistant |
|---|---|
| Gauche — défaut | `255, 192, 140` |
| Milieu | `255, 228, 206` |
| Droite | `255, 254, 250` |

Ces trois valeurs reproduisent les aplats de la capture fournie ; elles ne représentent pas une estimation en kelvins ni une lecture automatique de vos favoris. Les favoris Home Assistant varient selon les capacités de la lampe et les personnalisations. Une modification de vos favoris ne modifie donc pas la palette de ce blueprint.

La **Couleur de rappel** est librement réglable dans le sélecteur RGB, indépendamment de la palette. Pour les couleurs IKEA, les commandes utilisent les coordonnées **xy** issues du relevé des préréglages de l’application TRÅDFRI, et non la couleur décorative de leurs pastilles. [Valeurs de référence](https://github.com/AlCalzone/node-tradfri-client/blob/master/src/lib/predefined-colors.ts) · [Palette documentée par IKEA](https://www.ikea.com/jp/en/manuals/tradfri-starter-kit-smart-wireless-dimmable-colour-and-white-spectrum__AA-2302838-3-100.pdf).

Un changement de palette ou un rappel arrête l’effet `colorloop` si la lampe expose une commande d’effet `off`. Une couleur de rappel noire est refusée, car elle risquerait d’éteindre la lampe.

L’ordre enregistré dans la sélection est l’ordre de défilement. En YAML, réordonner directement la liste `palette`. Une liste vide, un nom inconnu ou un doublon est refusé. Après un changement depuis l’application, le prochain défilement repart de la couleur présente la plus proche dans la palette. Sans couleur disponible, la flèche droite commence au début et la gauche à la fin. Le rendu physique reste dépendant de l’ampoule et de sa gamme de couleurs.

## Réglages et journaux

Les deux vitesses sont réglées séparément :

| Réglage | Valeur initiale | Effet |
|---|---:|---|
| Vitesse de variation de luminosité | 35 points par seconde | Environ 3 secondes pour traverser toute la plage. |
| Cadence des commandes de luminosité | 0,3 seconde | Fréquence de renouvellement du fondu, indépendante de la vitesse. |
| Intervalle entre les couleurs pendant un maintien | 0,4 seconde | Un nouveau préréglage toutes les 0,4 seconde environ. |

La vitesse peut aller de 1 à 100 points par seconde, la cadence de 0,2 à 1 seconde et l’intervalle des couleurs de 0,2 à 3 secondes. La valeur 0 pour la vitesse réactive les anciens paramètres **pas / intervalle**, rangés dans la section avancée. Les bornes de luminosité concernent la variation ; elles ne limitent pas les changements faits depuis l’application ni la luminosité imposée à l’allumage.

**Lisser la variation pendant un maintien** est activé par défaut. Le premier pas est immédiat, puis le script partagé envoie des impulsions à la cadence configurée. Seule l’automatisation de la télécommande exécute les commandes de lampe, dans l’ordre. L’ampoule effectue un fondu natif pendant chaque intervalle, plafonné par le temps de maintien encore autorisé. Les appareils ou le réseau peuvent limiter la cadence réellement atteinte.

Le maintien de couleur commence aussi immédiatement et se termine au relâchement. Le dernier fondu rejoint le dernier préréglage choisi, sans passer au suivant. Sa transition est limitée à l’intervalle de défilement pour éviter d’enchaîner des fondus trop longs. L’appui court change toujours d’un seul préréglage.

Au relâchement ou au changement de sens, Home Assistant annonce souvent déjà la cible, alors que l’ampoule est encore en train d’y aller. Le blueprint estime le niveau intermédiaire à partir du dernier fondu et, au relâchement, envoie cette valeur avec une transition nulle. Cette estimation suppose un fondu linéaire : elle améliore l’arrêt mais ne remplace pas une mesure physique de luminosité. Un changement externe identifiable invalide cette estimation pour éviter de l’écraser. L’option de lissage peut être désactivée. Le réglage **Durée de transition des changements de couleur** reste indépendant de la variation de luminosité.

Activer **Journaliser les boutons et les actions** ajoute des messages INFO au journal `ikea_styrbar_light`. Pour les voir dans le journal complet, ajouter ou fusionner ce réglage dans la configuration de journalisation existante :

```yaml
logger:
  logs:
    ikea_styrbar_light: info
```

Les erreurs de configuration sont signalées lors d’un appui ou d’un rechargement. Les erreurs de commande restent signalées par Home Assistant, même si cette option est désactivée. Les contrôles périodiques invalides ne remplissent pas le journal. Aucune notification répétée n’est créée par ce blueprint.

## Robustesse et limites

- Les commandes d’une télécommande sont sérialisées (`queued`, maximum 30 exécutions). Les deux lampes restent indépendantes. Un seul appel de lampe est en cours par automatisation.
- Le script partagé ne commande aucune lampe. Chaque impulsion porte l’identité et l’horodatage du maintien ; une ancienne impulsion ou celle d’une autre télécommande est refusée. L’horloge s’arrête après un relâchement, un autre geste, une mémoire invalide ou l’expiration du délai. Une vérification par seconde subsiste comme protection complémentaire. Jusqu’à 50 horloges de maintien peuvent fonctionner simultanément.
- Le bouton de relâchement arrête la variation. En cas de perte radio, la limite de maintien l’arrête également. Des paquets de maintien répétés n’accélèrent pas les pas et ne repoussent pas cette limite. Si le relâchement manque, appuyer brièvement sur un autre bouton avant de recommencer un maintien identique.
- L’état de maintien est désarmé avant chaque appel de lampe. Si l’appel échoue ou est interrompu, aucun pas automatique supplémentaire n’est lancé.
- Une lampe indisponible annule le geste. Son retour en ligne ne rejoue aucune commande. Les boutons ayant attendu plus de cinq secondes dans la file sont abandonnés ; un relâchement tardif peut toujours arrêter un geste. Les événements désordonnés sont ignorés.
- Une extinction depuis l’application arrête aussi un maintien ; la vérification périodique ne rallume pas la lampe.
- Un démarrage, un rechargement, une réactivation de l’automatisation ou un retour de l’horloge en arrière ne reprend pas un ancien maintien. Un autre réglage effectué depuis l’application invalide le repère de palette mémorisé.
- Les événements inconnus et les mises à jour de batterie n’interrompent pas un maintien. Les variantes numériques et textuelles `MoveMode.Up/Down` sont acceptées.
- Un maintien ayant atteint une butée reste identifiable jusqu’à la fin du dernier fondu, afin qu’un relâchement puisse encore l’arrêter à mi-parcours. Un échec de commande désarme toujours les pas suivants.
- L’assistant est associé à l’automatisation, à la télécommande et à la lampe. Un état illisible ou appartenant à une autre configuration arrête les commandes et est signalé, sans écrasement automatique. Pour changer cette association, arrêter l’automatisation, vider cet assistant dédié puis réactiver. Ne pas partager un assistant : cette vérification n’est pas un verrou distribué pour deux nouvelles automatisations démarrant simultanément.
- Home Assistant n’est pas un système temps réel : une commande radio lente peut retarder le relâchement jusqu’à sa fin ou son expiration côté intégration. La limite de maintien empêche les pas suivants ; elle ne peut pas annuler une commande déjà envoyée à une ampoule.

Les tests font fonctionner le blueprint dans un **Home Assistant 2026.10.4 isolé**, avec de vraies automatisations, les services natifs de lampe et des assistants Texte. La radio et le rendu sont simulés, avec un modèle de fondu linéaire indépendant de la mémoire du blueprint. Ils couvrent notamment les capacités des différents modes, le diagnostic sans commande, l’arrêt à mi-fondu, les changements de sens, la cadence, les doubles appuis, les limites de luminosité, les événements répétés ou retardés, la perte du relâchement, les erreurs de commande, les changements externes et l’indépendance de deux télécommandes. Ils ne prouvent pas la réception radio ni le rendu des couleurs sur une ampoule physique. Aucune automatisation d’une installation réelle n’est modifiée par la publication dans ce dépôt.

Une mise à jour depuis 1.0.0 ou 1.1.0 conserve les entrées et l’assistant Texte existants. **Installer aussi le fichier de script partagé avant de recharger le blueprint 1.2.0.** Choisir **Aucun** pour le geste de rappel supplémentaire si les deux maintiens latéraux doivent faire défiler la palette. Un rechargement annule le geste en cours sans modifier l’éclairage.
