# Télécommandes d’éclairage et extinction automatique

**Français** · [English](lighting.en.md)

Une famille de blueprints qui pilotent les lampes de la même façon, quelle que soit la télécommande ZHA, et un blueprint d’extinction automatique.

| Blueprint | Appareils | Gestes |
|---|---|---|
| [Télécommande Philips Hue Dimmer](../blueprints/automation/lighting/telecommande_hue_dimmer.yaml) | RWL022 | Marche/Arrêt, Plus, Moins, Hue : appui court et maintien |
| [Télécommande Philips Hue Tap Dial](../blueprints/automation/lighting/telecommande_hue_tap_dial.yaml) | RDM002 | 4 boutons (une lampe chacun) : appui court et maintien ; molette |
| [Interrupteur IKEA TRÅDFRI marche/arrêt](../blueprints/automation/lighting/telecommande_ikea_marche_arret.yaml) | TRADFRI on/off switch | I et O : appui court, double appui, maintien |
| [Télécommande IKEA TRÅDFRI 5 boutons](../blueprints/automation/lighting/telecommande_ikea_5_boutons.yaml) | TRADFRI remote control | Centre, Plus, Moins, Gauche, Droite : appui court, double appui, maintien |
| [Télécommande IKEA STYRBAR](../blueprints/automation/lighting/telecommande_ikea_styrbar.yaml) | Remote Control N2 | Haut, Bas, Gauche, Droite : appui court, double appui, maintien |
| [Bouton eWeLink / SONOFF](../blueprints/automation/lighting/bouton_ewelink.yaml) | WB01, SNZB-01P, CK-TLSR8656-SS5-01 | Clic simple, double clic, appui long |
| [Extinction automatique de l’éclairage](../blueprints/automation/lighting/extinction_automatique.yaml) | Lampes, interrupteurs, prises | — |

Le blueprint STYRBAR reprend toutes les fonctions et tous les réglages par défaut de l’ancien blueprint STYRBAR de cette collection, qu’il remplace.

## Installation

1. Importer les blueprints utiles :
   [Hue Dimmer](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flighting%2Ftelecommande_hue_dimmer.yaml) ·
   [Hue Tap Dial](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flighting%2Ftelecommande_hue_tap_dial.yaml) ·
   [IKEA marche/arrêt](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flighting%2Ftelecommande_ikea_marche_arret.yaml) ·
   [IKEA 5 boutons](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flighting%2Ftelecommande_ikea_5_boutons.yaml) ·
   [IKEA STYRBAR](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flighting%2Ftelecommande_ikea_styrbar.yaml) ·
   [eWeLink](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flighting%2Fbouton_ewelink.yaml) ·
   [Extinction automatique](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flighting%2Fextinction_automatique.yaml).
2. Créer une automatisation par télécommande : choisir la télécommande, la lampe, puis l’action de chaque geste.
3. Facultatif : choisir un **assistant de mémoire** (voir plus bas).
4. Vérifier avec **Menu → Exécuter les actions** : une notification décrit la lampe, la mémoire et les éventuels problèmes, sans commander la lampe.

L’[exemple](../examples/lighting/automations.yaml) montre un réglage typique de chaque blueprint.

## Assistant de mémoire (facultatif)

Un **assistant Texte** de longueur maximale 255, propre à une seule automatisation.

| | Sans assistant | Avec assistant |
|---|---|---|
| Toutes les actions, maintiens bornés, filtres, diagnostic | oui | oui |
| Double appui | non | oui |
| Position dans la palette | préréglage le plus proche de la couleur affichée | position exacte, recalée si la couleur a été changée ailleurs |
| Relâchement d’un maintien | la variation s’arrête, la lampe finit son dernier fondu | la lampe est figée au niveau réellement atteint |
| Doublon radio | tout geste trop proche du précédent est écarté | seul un geste identique est écarté |
| Maintien répété par la télécommande | ignoré tant que la variation tourne | ignoré ; un maintien dans l’autre sens prend le relais aussitôt |
| Événement arrivé dans le désordre | — | écarté |

L’assistant est écrit au début de chaque geste. Exclure l’assistant de l’historique (`recorder`) évite de l’y enregistrer à chaque appui.

Un assistant illisible ou déjà utilisé par une autre automatisation n’est jamais modifié. Une notification le signale, et la télécommande fonctionne sans mémoire. Pour le réutiliser, le vider pendant que l’automatisation est désactivée.

## Actions disponibles pour chaque geste

| Action | Effet |
|---|---|
| Aucune action | Le geste est ignoré ; il n’interrompt pas une variation en cours. |
| Basculer marche/arrêt | Allume (luminosité mémorisée par la lampe) ou éteint. |
| Basculer, en allumant au niveau d’allumage | Éteint, ou allume au **niveau d’allumage**. |
| Allumer · Éteindre | — |
| Allumer au niveau d’allumage | — |
| Pleine luminosité | 100 %, couleur inchangée. |
| Pleine luminosité et couleur de référence | 100 % et premier préréglage de la palette ; pour une lampe à blanc réglable seulement, **blanc de référence**. |
| Couleur de rappel | La **couleur de rappel** choisie, luminosité conservée. |
| Alterner entre niveau d’allumage et niveau haut | Éteinte → niveau d’allumage ; allumée sous le niveau haut → niveau haut ; au niveau haut → niveau d’allumage. |
| Augmenter / Baisser la luminosité d’un pas | Lampe éteinte : Plus l’allume, Moins ne fait rien. La baisse s’arrête à la luminosité minimale et n’éteint jamais. |
| … en continu *(maintiens)* | Variation jusqu’au relâchement, à la butée ou à la durée maximale. Vers le haut sur une lampe éteinte : départ à la luminosité minimale. |
| Blanc plus froid / plus chaud, d’un pas ou en continu | Température en kelvins, bornée aux limites de la lampe. |
| Préréglage de couleur suivant / précédent, d’un pas ou en continu | Voir l’assistant de mémoire pour la position. Lampe éteinte : premier préréglage. |
| Action personnalisée | Exécute les actions saisies sous le geste ; la variable `gesture` contient le nom du geste. |

Les actions « en continu » ne sont proposées que pour les maintiens. Le **double appui** n’existe que sur les télécommandes IKEA, dont le micrologiciel ne le signale pas lui-même : le premier appui agit tout de suite, le second exécute l’action de double appui.

## Réglages communs

Dans la section repliée **Réglages de variation et de couleur**. Les valeurs entre parenthèses sont les valeurs par défaut propres à certains modèles.

| Réglage | Défaut | Rôle |
|---|---|---|
| Pas de luminosité | 10 % (IKEA 5 boutons : 20 %) | Appuis « d’un pas ». |
| Vitesse de variation pendant un maintien | 0 (STYRBAR : 35 %/s) | En %/s ; 0 utilise le pas pendant un maintien. |
| Pas de luminosité pendant un maintien | 10 % | Utilisé si la vitesse vaut 0. |
| Cadence de la luminosité | 0,5 s (STYRBAR : 0,3 s ; IKEA marche/arrêt : 1 s) | Intervalle des commandes de luminosité d’un maintien. |
| Cadence des couleurs et des blancs | 0,5 s (STYRBAR : 0,4 s) | Intervalle des préréglages ou pas de température d’un maintien. |
| Durée maximale d’un maintien | 10 s (STYRBAR : 15 s) | Arrêt si le relâchement radio est perdu. |
| Lisser la variation | oui | Chaque pas est un fondu jusqu’au suivant. |
| Luminosité minimale · maximale | 1 % · 100 % | Butées de la variation. |
| Niveau d’allumage · Niveau haut | 50 % · 100 % (eWeLink : 25 % · 100 %) | Allumage à niveau fixe et alternance. |
| Fondu de la luminosité | 0 s (Tap Dial, IKEA marche/arrêt : 1 s ; IKEA 5 boutons : 0,5 s) | Allumages, extinctions, pas uniques. |
| Fondu des couleurs | 0 s (STYRBAR : 0,3 s ; IKEA 5 boutons : 0,5 s) | Couleurs, blancs, rappel. |
| Pas de température · Blanc de référence | 250 K · 2 500 K | — |
| Préréglages de couleur | 21 préréglages (STYRBAR : les 16 de l’ancien blueprint) | Ordre de défilement parmi 44 ; le premier est la couleur de référence. |
| Couleur de rappel | RGB 255, 192, 140 | — |
| Les couleurs peuvent allumer · Le rappel peut allumer | oui · oui | Sinon, sans effet sur une lampe éteinte. |
| Délai du double appui | 800 ms | Assistant de mémoire nécessaire. |
| Ignorer les événements trop rapprochés | 0 (STYRBAR : 50 ms ; Tap Dial : 100 ms) | Doit rester inférieur au délai du double appui. |
| Journaliser | non | Niveau INFO, journal `lighting_remote`. |

Sur le Tap Dial, la molette transmet une amplitude qui grandit avec la vitesse de rotation : environ 3 % pour un cran lent, jusqu’à 80 % pour une rotation rapide. **Sensibilité de la molette** la multiplie (1 par défaut). Le filtre de 100 ms écarte les appuis reçus deux fois et les rapports de rotation contradictoires émis à quelques millisecondes d’intervalle.

Une configuration incohérente (minimum au-dessus du maximum, palette inconnue, couleur de rappel noire, filtre plus long que le double appui, assistant trop court) bloque toute commande. Elle est signalée par une notification et dans le journal.

## Fonctionnement

- **Un relâchement arrête la variation.** Les automatisations sont en mode *restart* : un relâchement ou un autre geste reconnu arrête la variation en cours. Les événements sans action sont écartés avant de démarrer et n’interrompent jamais rien : relâchement d’un appui court, rapport d’état, doublon de scène du Tap Dial, événement de plus de 5 secondes.
- **Les télécommandes Philips répètent le maintien.** Chaque répétition produit un seul pas. Les télécommandes IKEA n’envoient qu’un début et une fin : la variation tourne alors à la cadence réglée.
- **L’état de la lampe est relu à chaque pas.** Une lampe éteinte pendant un maintien n’est pas rallumée par lui. Une lampe devenue indisponible arrête la variation. Un changement fait ailleurs est respecté, et le relâchement ne l’écrase pas.
- **Les couleurs arrêtent un effet en cours** (colorloop), si la lampe le permet.
- **La molette du Tap Dial** agit sur la dernière lampe allumée parmi les quatre. Si toutes sont éteintes, elle agit sur la dernière actionnée ; une lampe indisponible n’est jamais choisie. Quand des lampes se suivent, comme un groupe et ses membres, celle que la télécommande a commandée l’emporte : bouton de la lampe du haut puis molette agit sur la lampe du haut seule, bouton du groupe puis molette agit sur le groupe. Une lampe allumée autrement plus de 2 secondes après reste prioritaire.
- **Le bouton eWeLink** est lu dans ses commandes (simple, double, long). Les rapports d’état `attribute_updated` sont ignorés : le bouton peut en émettre sans aucun appui.

## Extinction automatique

- Choisir les éclairages, la durée et, si besoin, un **assistant Minuteur** dédié.
- Chaque allumage, par n’importe quel moyen, relance le décompte. Éteindre tous les éclairages à la main l’annule. À la fin du décompte, les éclairages encore allumés sont éteints.
- Au démarrage de Home Assistant, un éclairage resté allumé sans décompte actif relance le décompte.
- Avec un assistant Minuteur, le temps restant est visible. Activer son option *Restaurer* pour qu’il survive à un redémarrage.
- Sans assistant, l’automatisation attend elle-même. Un redémarrage interrompt l’attente, qui est reprise au démarrage suivant.

## Passer des anciens blueprints

| Ancien réglage | Nouveau réglage |
|---|---|
| Hue Dimmer : Power → `light.toggle` · Up/Down → `brightness_increase`/`decrease` · Hue → 100 % | Valeurs par défaut du blueprint Hue Dimmer. Bouton Hue sans action : *Appui court* = Aucune action. |
| Tap Dial : 4 lampes, assistant `input_text` de lampe courante, échelle | Les 4 lampes et la sensibilité. L’assistant n’est plus utilisé. |
| IKEA marche/arrêt : fondu 1 s, maintien 10 × 10 % par seconde | Fondu 1 s, cadence 1 s, pas 10 %, durée maximale 10 s. |
| IKEA 5 boutons « préréglages » + `input_select` | Valeurs par défaut ; la palette remplace l’`input_select`. |
| IKEA 5 boutons « blancs » | Gauche : blanc plus chaud, Droite : blanc plus froid (appui et maintien), blanc de référence 2 500 K. L’ancien blueprint utilisait le paramètre `color_temp` en mireds, que Home Assistant 2026.10 n’accepte plus. |
| STYRBAR : assistant Texte, script `styrbar_maintiens` | Mêmes réglages par défaut. Garder le même assistant pour le double appui : son ancien contenu est remplacé au premier geste. Désactiver d’abord l’ancienne automatisation. Le script n’est plus nécessaire. *Rappel par maintien à droite / à gauche* : choisir *Couleur de rappel* pour ce maintien. *Luminosité imposée en haut* : action *Allumer au niveau d’allumage*. |
| Automatisation eWeLink sur `attribute_updated` | Clic simple : basculer au niveau d’allumage 25 % ; double clic : alterner 25 % / 100 %. |
| Minuterie d’éclairage (manual light) | Extinction automatique avec le même assistant Minuteur et la même durée. |

## Limites

- Les formats d’événements viennent des profils zha-quirks 2.4.1 et des traces de la maison. Un micrologiciel différent peut nommer autrement un geste : le geste est alors ignoré, jamais mal interprété.
- Sans assistant de mémoire, la position dans la palette est déduite de la couleur affichée. Une ampoule qui rend mal une couleur peut l’afficher plus près d’un préréglage voisin ; la flèche suivante sauterait alors un préréglage. Un essai de toute la palette sur la lampe le montre : l’assistant de mémoire supprime ce risque.
- Sans assistant de mémoire, un nouveau maintien est ignoré tant que le précédent tourne encore, par exemple après un relâchement radio perdu. Un appui court sur un bouton qui a une action l’arrête.
- Le niveau figé au relâchement est estimé d’après le fondu demandé ; le rendu réel de chaque ampoule peut s’en écarter légèrement.
- Les tests simulent la radio. Le rendu réel des lampes et la cadence des répétitions de maintien ne sont pas certifiés.
