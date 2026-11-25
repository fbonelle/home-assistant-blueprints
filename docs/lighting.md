# Lighting remotes and automatic switch-off — télécommandes d’éclairage et extinction automatique

**Français** · [English](lighting.en.md)

Une famille de blueprints qui pilotent les lampes de la même façon, quelle que soit la télécommande ZHA, et un blueprint d’extinction automatique.

| Blueprint | Appareils | Gestes |
|---|---|---|
| [Aqara wireless button](../blueprints/automation/lighting/aqara_button.yaml) | lumi.remote.b1acn01 (WXKG11LM) | Appui simple, double appui, maintien |
| [eWeLink / SONOFF button](../blueprints/automation/lighting/ewelink_button.yaml) | WB01, SNZB-01P, CK-TLSR8656-SS5-01 | Clic simple, double clic, appui long |
| [IKEA STYRBAR remote](../blueprints/automation/lighting/ikea_styrbar_remote.yaml) | Remote Control N2 | Haut, Bas, Gauche, Droite : appui court, double appui, maintien |
| [IKEA TRÅDFRI 5-button remote](../blueprints/automation/lighting/ikea_5_button_remote.yaml) | TRADFRI remote control | Centre, Plus, Moins, Gauche, Droite : appui court, double appui, maintien |
| [IKEA TRÅDFRI on/off switch](../blueprints/automation/lighting/ikea_on_off_switch.yaml) | TRADFRI on/off switch | I et O : appui court, double appui, maintien |
| [Lighting automatic switch-off](../blueprints/automation/lighting/auto_off.yaml) | Lampes, interrupteurs, prises | — |
| [Philips Hue Dimmer remote](../blueprints/automation/lighting/hue_dimmer_remote.yaml) | RWL022 | Marche/Arrêt, Plus, Moins, Hue : appui court et maintien |
| [Philips Hue Tap Dial remote](../blueprints/automation/lighting/hue_tap_dial_remote.yaml) | RDM002 | 4 boutons (une lampe chacun) : appui court et maintien ; molette |

Les formulaires des blueprints sont en anglais ; ce guide cite leurs libellés tels qu’ils apparaissent.

## Installation

1. Importer les blueprints utiles :
   [Aqara](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flighting%2Faqara_button.yaml) ·
   [eWeLink](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flighting%2Fewelink_button.yaml) ·
   [Hue Dimmer](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flighting%2Fhue_dimmer_remote.yaml) ·
   [Hue Tap Dial](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flighting%2Fhue_tap_dial_remote.yaml) ·
   [IKEA 5-button](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flighting%2Fikea_5_button_remote.yaml) ·
   [IKEA on/off](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flighting%2Fikea_on_off_switch.yaml) ·
   [IKEA STYRBAR](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flighting%2Fikea_styrbar_remote.yaml) ·
   [Lighting automatic switch-off](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Flighting%2Fauto_off.yaml).
2. Créer une automatisation par télécommande : choisir la télécommande (**Remote**), la lampe (**Lamp**), puis l’action de chaque geste.
3. Facultatif : choisir un assistant de mémoire, **Memory helper (optional)** (voir plus bas).
4. Vérifier avec **Menu → Exécuter les actions** : une notification décrit la lampe, la mémoire et les éventuels problèmes, sans commander la lampe.

L’[exemple](../examples/lighting/automations.yaml) montre un réglage typique de chaque blueprint.

## Assistant de mémoire (facultatif)

Un **assistant Texte** de longueur maximale 255, propre à une seule automatisation.

| | Sans assistant | Avec assistant |
|---|---|---|
| Toutes les actions, maintiens bornés, filtres, diagnostic | oui | oui |
| Double appui (IKEA) | non | oui |
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
| No action | Le geste est ignoré ; il n’interrompt pas une variation en cours. |
| Toggle on/off | Allume (luminosité mémorisée par la lampe) ou éteint. |
| Toggle, turning on at the on level | Éteint, ou allume au niveau d’allumage (**On level**). |
| Turn on · Turn off | Allume · éteint. |
| Turn on at the on level | Allume au niveau d’allumage. |
| Full brightness | 100 %, couleur inchangée. |
| Full brightness and reference color | 100 % et premier préréglage de la palette ; pour une lampe à blanc réglable seulement, blanc de référence (**Reference white**). |
| Recall color (brightness kept) | La couleur de rappel choisie (**Recall color**), luminosité conservée. |
| Alternate between on level and high level | Éteinte → niveau d’allumage ; allumée sous le niveau haut → niveau haut ; au niveau haut → niveau d’allumage. |
| Brighter by one step · Dimmer by one step | Lampe éteinte : la hausse l’allume, la baisse ne fait rien. La baisse s’arrête à la luminosité minimale et n’éteint jamais. |
| Brighter continuously · Dimmer continuously *(maintiens)* | Variation jusqu’au relâchement, à la butée ou à la durée maximale. Vers le haut sur une lampe éteinte : départ à la luminosité minimale. |
| Cooler / Warmer white by one step · continuously | Température en kelvins, bornée aux limites de la lampe. |
| Next / Previous color preset · presets continuously | Voir l’assistant de mémoire pour la position. Lampe éteinte : premier préréglage. |
| Custom action | Exécute les actions saisies sous le geste ; la variable `gesture` contient le nom du geste. |

Les actions *continuously* ne sont proposées que pour les maintiens (**Hold**). Le double appui (**Double press**) des télécommandes IKEA demande l’assistant de mémoire, car leur micrologiciel ne le signale pas lui-même : le premier appui agit tout de suite, le second exécute l’action de double appui. Les boutons eWeLink et Aqara signalent eux-mêmes leur double appui, sans assistant.

## Réglages communs

Dans la section repliée **Dimming and color settings**. Les valeurs entre parenthèses sont les valeurs par défaut propres à certains modèles.

| Réglage | Défaut | Rôle |
|---|---|---|
| Brightness step | 10 % (IKEA 5 boutons : 20 %) | Appuis « d’un pas ». |
| Dimming speed during a hold | 0 (STYRBAR : 35 %/s) | En %/s ; 0 utilise le pas pendant un maintien. |
| Brightness step during a hold | 10 % | Utilisé si la vitesse vaut 0. |
| Brightness tick during a hold | 0,5 s (STYRBAR : 0,3 s ; IKEA marche/arrêt : 1 s) | Intervalle des commandes de luminosité d’un maintien. |
| Color and white tick during a hold | 0,5 s (STYRBAR : 0,4 s) | Intervalle des préréglages ou pas de température d’un maintien. |
| Maximum hold duration | 10 s (STYRBAR : 15 s) | Arrêt si le relâchement radio est perdu. |
| Smooth dimming during a hold | oui | Chaque pas est un fondu jusqu’au suivant. |
| Minimum brightness · Maximum brightness of dimming | 1 % · 100 % | Butées de la variation. |
| On level · High level | 50 % · 100 % (eWeLink : 25 % · 100 %) | Allumage à niveau fixe et alternance. |
| Brightness transition | 0 s (Tap Dial, IKEA marche/arrêt : 1 s ; IKEA 5 boutons : 0,5 s) | Allumages, extinctions, pas uniques. |
| Color transition | 0 s (STYRBAR : 0,3 s ; IKEA 5 boutons : 0,5 s) | Couleurs, blancs, rappel. |
| White temperature step · Reference white | 250 K · 2 500 K | — |
| Color presets | 21 préréglages (STYRBAR : les 16 de l’ancien blueprint) | Ordre de défilement parmi 44 ; le premier est la couleur de référence. |
| Recall color | RGB 255, 192, 140 | — |
| Color and white changes may switch the lamp on · Color recall may switch the lamp on | oui · oui | Sinon, sans effet sur une lampe éteinte. |
| Maximum double press delay | 800 ms | Assistant de mémoire nécessaire. |
| Ignore events too close together | 0 (STYRBAR : 50 ms ; Tap Dial : 100 ms) | Doit rester inférieur au délai du double appui. |
| Log gestures and actions | non | Niveau INFO, journal `lighting_remote`. L’automatisation règle elle-même ce niveau : aucune configuration n’est nécessaire. |

Sur le Tap Dial, la molette transmet une amplitude qui grandit avec la vitesse de rotation : environ 3 % pour un cran lent, jusqu’à 80 % pour une rotation rapide. **Dial sensitivity** la multiplie (1 par défaut). Le filtre de 100 ms écarte les appuis reçus deux fois et les rapports de rotation contradictoires émis à quelques millisecondes d’intervalle. Sans assistant de mémoire, il mesure l’écart depuis le début du traitement du geste précédent : si Home Assistant est très chargé, un vrai geste qui suit le précédent de très près peut aussi être écarté.

Une configuration incohérente (minimum au-dessus du maximum, palette inconnue, couleur de rappel noire, filtre plus long que le double appui, assistant trop court) bloque toute commande. Elle est signalée par une notification et dans le journal.

## Fonctionnement

- **Un relâchement arrête la variation.** Les automatisations sont en mode *restart* : un relâchement ou un autre geste reconnu arrête la variation en cours. Les événements sans action sont écartés avant de démarrer et n’interrompent jamais rien : relâchement d’un appui court, rapport d’état, doublon de scène du Tap Dial, événement de plus de 5 secondes.
- **Les télécommandes Philips répètent le maintien.** Chaque répétition produit un seul pas. Les télécommandes IKEA n’envoient qu’un début et une fin : la variation tourne alors à la cadence réglée.
- **L’état de la lampe est relu à chaque pas.** Une lampe éteinte pendant un maintien n’est pas rallumée par lui. Une lampe devenue indisponible arrête la variation. Un changement fait ailleurs est respecté, et le relâchement ne l’écrase pas.
- **Les couleurs arrêtent un effet en cours** (colorloop), si la lampe le permet.
- **La molette du Tap Dial** agit sur la dernière lampe allumée parmi les quatre. Si toutes sont éteintes, elle agit sur la dernière actionnée ; une lampe indisponible n’est jamais choisie. Quand des lampes se suivent, comme un groupe et ses membres, celle que la télécommande a commandée l’emporte : bouton de la lampe du haut puis molette agit sur la lampe du haut seule, bouton du groupe puis molette agit sur le groupe. Une lampe allumée autrement plus de 2 secondes après reste prioritaire.
- **Le bouton eWeLink** est lu dans ses commandes (simple, double, long). Les rapports d’état `attribute_updated` sont ignorés : le bouton peut en émettre sans aucun appui.
- **Le bouton Aqara** signale lui-même l’appui simple, le double appui, le début et la fin d’un maintien. Il ne répète pas le maintien : la variation tourne à la cadence réglée jusqu’au relâchement, ou jusqu’à la durée maximale si le relâchement radio est perdu. Par défaut, seul l’appui simple a une action (basculer).

## Extinction automatique

- Choisir les éclairages (**Lighting to switch off**), la durée (**On time**) et, si besoin, un assistant Minuteur dédié (**Timer helper (optional)**).
- Chaque allumage, par n’importe quel moyen, relance le décompte. Éteindre tous les éclairages à la main l’annule. À la fin du décompte, les éclairages encore allumés sont éteints.
- Au démarrage de Home Assistant, un éclairage resté allumé sans décompte actif relance le décompte.
- Avec un assistant Minuteur, le temps restant est visible. Activer son option *Restaurer* pour qu’il survive à un redémarrage.
- Sans assistant, l’automatisation attend elle-même. Un redémarrage interrompt l’attente, qui est reprise au démarrage suivant.

## Passer des anciens blueprints

| Ancien réglage | Nouveau réglage |
|---|---|
| Automatisation Aqara sur le déclencheur d’appareil « appui simple » | Valeurs par défaut du blueprint Aqara ; reprendre le fondu de l’ancienne automatisation dans *Brightness transition*. |
| Automatisation eWeLink sur `attribute_updated` | Clic simple : basculer au niveau d’allumage 25 % ; double clic : alterner 25 % / 100 %. |
| Hue Dimmer : Power → `light.toggle` · Up/Down → `brightness_increase`/`decrease` · Hue → 100 % | Valeurs par défaut du blueprint Hue Dimmer. Bouton Hue sans action : *Short press* = *No action*. |
| IKEA 5 boutons « blancs » | Gauche : blanc plus chaud, Droite : blanc plus froid (appui et maintien), blanc de référence 2 500 K. L’ancien blueprint utilisait le paramètre `color_temp` en mireds, remplacé ici par `color_temp_kelvin`. |
| IKEA 5 boutons « préréglages » + `input_select` | Valeurs par défaut ; la palette remplace l’`input_select`. |
| IKEA marche/arrêt : fondu 1 s, maintien 10 × 10 % par seconde | Fondu 1 s, cadence 1 s, pas 10 %, durée maximale 10 s. |
| Minuterie d’éclairage (manual light) | *Lighting automatic switch-off* avec le même assistant Minuteur et la même durée. |
| STYRBAR : assistant Texte, script `styrbar_maintiens` | Mêmes réglages par défaut. Garder le même assistant pour le double appui : son ancien contenu est remplacé au premier geste. Désactiver d’abord l’ancienne automatisation. Le script n’est plus nécessaire. *Rappel par maintien à droite / à gauche* : choisir *Recall color (brightness kept)* pour ce maintien. *Luminosité imposée en haut* : action *Turn on at the on level*. |
| Tap Dial : 4 lampes, assistant `input_text` de lampe courante, échelle | Les 4 lampes et la sensibilité (**Dial sensitivity**). L’assistant n’est plus utilisé. |

## Limites

- Les formats d’événements viennent des profils zha-quirks (version 2.4.1 pour les télécommandes Philips, IKEA et eWeLink ; profil SwitchAQ3B, inchangé depuis, pour le bouton Aqara) et des traces de la maison. Un micrologiciel différent peut nommer autrement un geste : le geste est alors ignoré, jamais mal interprété.
- Sans assistant de mémoire, la position dans la palette est déduite de la couleur affichée. Une ampoule qui rend mal une couleur peut l’afficher plus près d’un préréglage voisin ; la flèche suivante sauterait alors un préréglage. Un essai de toute la palette sur la lampe le montre : l’assistant de mémoire supprime ce risque.
- Sans assistant de mémoire, un nouveau maintien est ignoré tant que le précédent tourne encore, par exemple après un relâchement radio perdu. Un appui court sur un bouton qui a une action l’arrête.
- Le niveau figé au relâchement est estimé d’après le fondu demandé ; le rendu réel de chaque ampoule peut s’en écarter légèrement.
- Les tests simulent la radio. Le rendu réel des lampes et la cadence des répétitions de maintien ne sont pas certifiés.
