# Lampe avec télécommande IKEA STYRBAR — ZHA

**Français** · [English](ikea_styrbar_light.en.md) · [Accueil](../README.md)

Version **1.0.0**. Un seul blueprint par lampe remplace le couple « contrôleur + hook ». Il utilise les fonctions standard de Home Assistant, sans composant personnalisé ni script partagé à installer.

## Installation

1. Utiliser Home Assistant **2026.10 ou plus récent**, une STYRBAR intégrée par **ZHA** (modèle `Remote Control N2`) et une lampe prenant en charge les couleurs. Zigbee2MQTT et deCONZ ne sont pas pris en charge par ce blueprint.
2. [Importer le blueprint](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fikea_styrbar_light%2Flampe_styrbar.yaml).
3. Dans **Paramètres → Appareils et services → Entrées**, créer un assistant **Texte**, longueur minimale **0**, maximale **255**. Le réserver à cette automatisation. Chaque autre télécommande doit avoir son propre assistant.
4. Créer une automatisation depuis le blueprint, puis choisir la télécommande, la lampe et l’assistant. Régler la palette et la couleur de rappel.
5. Avant d’activer le nouveau pilotage, désactiver les anciennes automatisations contrôleur et hook de cette télécommande. Vérifier aussi qu’aucune liaison Zigbee directe ou autre automatisation ne commande simultanément la lampe.

Les [exemples d’automatisations](../examples/ikea_styrbar_light/automations.yaml) et d’[assistants YAML](../examples/ikea_styrbar_light/helpers.yaml) utilisent uniquement des identifiants fictifs. Les assistants créés depuis l’interface suffisent : le fichier YAML d’assistants est facultatif. Adapter le chemin du blueprint si Home Assistant propose un autre nom lors de l’importation.

## Boutons

| Geste | Résultat |
|---|---|
| Appui court en haut | Allumer, en conservant la couleur et la luminosité mémorisées par la lampe. Une luminosité imposée est facultative. |
| Appui court en bas | Éteindre. |
| Maintien en haut | Augmenter la luminosité ; depuis l’arrêt, commencer au minimum configuré. |
| Maintien en bas | Diminuer la luminosité jusqu’au minimum, sans éteindre. Ne rallume pas une lampe éteinte. |
| Appui court gauche / droite | Préréglage précédent / suivant, avec retour à l’autre extrémité de la liste. |
| Double appui en haut | Rappeler la couleur configurée, sans imposer de luminosité. |
| Maintien à droite | Même rappel, par défaut. Ce geste supplémentaire peut être placé à gauche ou désactivé. |
| Relâchement ou autre bouton reconnu | Arrêter la variation en cours. |

Le premier appui en haut est immédiat. Le second, s’il arrive dans le délai configuré, applique la couleur de rappel. Avec une luminosité imposée à l’allumage, le premier appui l’applique avant le rappel ; le rappel ne l’applique pas une seconde fois. Les options **Les flèches de couleur peuvent allumer la lampe** et **Le rappel de couleur peut allumer la lampe** règlent ces deux comportements lorsque la lampe est éteinte.

**Le double appui dépend du micrologiciel de la télécommande.** Certaines STYRBAR filtrent les appuis rapprochés ON/OFF avant leur transmission : si ZHA reçoit un seul événement `on`, aucun blueprint ne peut identifier deux appuis. Le maintien à droite fournit un accès au rappel sans cette dépendance. La [documentation STYRBAR](https://www.zigbee2mqtt.io/devices/E2001_E2002_E2313.html#action-mapping) décrit ce filtrage au niveau de l’appareil ; ses noms d’actions MQTT ne sont pas utilisés par notre blueprint ZHA.

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

Les pas de luminosité, les bornes de variation, la luminosité imposée à l’allumage, l’intervalle entre les pas, la durée maximale du maintien, la transition, le délai de double appui et le filtrage des événements répétés sont réglables. Les bornes de luminosité concernent la variation ; elles ne limitent pas les changements faits depuis l’application ni la luminosité imposée à l’allumage.

La variation s’exécute au plus une fois par seconde, ou plus lentement selon l’intervalle choisi. Une cadence de deux secondes peut occasionnellement apparaître avec le décalage du premier appui par rapport à l’horloge. La transition est limitée à l’intervalle entre les pas pour éviter des transitions qui s’empilent.

Activer **Journaliser les boutons et les actions** ajoute des messages INFO au journal `ikea_styrbar_light`. Pour les voir dans le journal complet, ajouter ou fusionner ce réglage dans la configuration de journalisation existante :

```yaml
logger:
  logs:
    ikea_styrbar_light: info
```

Les erreurs de configuration sont signalées lors d’un appui ou d’un rechargement. Les erreurs de commande restent signalées par Home Assistant, même si cette option est désactivée. Les contrôles périodiques invalides ne remplissent pas le journal. Aucune notification répétée n’est créée par ce blueprint.

## Robustesse et limites

- Les commandes d’une télécommande sont sérialisées (`queued`, maximum 30 exécutions). Les deux lampes restent indépendantes. Un seul appel de lampe est en cours par automatisation.
- Le bouton de relâchement arrête la variation. En cas de perte radio, la limite de maintien l’arrête également. Des paquets de maintien répétés n’accélèrent pas les pas et ne repoussent pas cette limite. Si le relâchement manque, appuyer brièvement sur un autre bouton avant de recommencer un maintien identique.
- L’état de maintien est désarmé avant chaque appel de lampe. Si l’appel échoue ou est interrompu, aucun pas automatique supplémentaire n’est lancé.
- Une lampe indisponible annule le geste. Son retour en ligne ne rejoue aucune commande. Les boutons ayant attendu plus de cinq secondes dans la file sont abandonnés ; un relâchement tardif peut toujours arrêter un geste. Les événements désordonnés sont ignorés.
- Une extinction depuis l’application arrête aussi un maintien ; la vérification périodique ne rallume pas la lampe.
- Un démarrage, un rechargement, une réactivation de l’automatisation ou un retour de l’horloge en arrière ne reprend pas un ancien maintien. Un autre réglage effectué depuis l’application invalide le repère de palette mémorisé.
- Les événements inconnus et les mises à jour de batterie n’interrompent pas un maintien. Les variantes numériques et textuelles `MoveMode.Up/Down` sont acceptées.
- L’assistant est associé à l’automatisation, à la télécommande et à la lampe. Un état illisible ou appartenant à une autre configuration arrête les commandes et est signalé, sans écrasement automatique. Pour changer cette association, arrêter l’automatisation, vider cet assistant dédié puis réactiver. Ne pas partager un assistant : cette vérification n’est pas un verrou distribué pour deux nouvelles automatisations démarrant simultanément.
- Home Assistant n’est pas un système temps réel : une commande radio lente peut retarder le relâchement jusqu’à sa fin ou son expiration côté intégration. La limite de maintien empêche les pas suivants ; elle ne peut pas annuler une commande déjà envoyée à une ampoule.

Les tests font fonctionner le blueprint dans un **Home Assistant 2026.10.4 isolé**, avec de vraies automatisations, les services natifs de lampe et des assistants Texte. Seule la radio est simulée. Ils couvrent notamment les doubles appuis, les limites de luminosité, les événements répétés ou retardés, la perte du relâchement, les erreurs de commande, les changements externes et l’indépendance de deux télécommandes. Ils ne prouvent pas la réception radio ni le rendu des couleurs sur une ampoule physique. Aucune automatisation d’une installation réelle n’est modifiée par la publication dans ce dépôt.
