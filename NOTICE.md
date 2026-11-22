# Origine et licence

**Français** · [English](NOTICE.en.md)

## Surveillance des intégrations

Le travail sur ce blueprint a commencé à partir de **Reload Integrations Automatically**, par **danimart1991** :

- [Projet d’origine](https://github.com/danimart1991/home-assistant-blueprints)
- [Blueprint d’origine](https://github.com/danimart1991/home-assistant-blueprints/blob/main/automation/reload-integrations/reload-integrations.en.yaml)
- Licence : GNU General Public License, version 3, conservée dans [LICENSE](LICENSE).

La présente implémentation a été profondément remaniée. Elle est maintenue séparément ; ses modifications ne doivent pas être attribuées à l’auteur du projet d’origine.

La **version 1.0.0** est la première version publiée dans cette collection, le 4 novembre 2026. Les exemples utilisent des identifiants fictifs et ne configurent aucune installation réelle.

## Surveillance des piles et batteries

Implémentation distincte, publiée sous la licence GPL-3.0 de cette collection. Ses fonctions de récapitulatif à heure fixe, de choix des jours et de notification persistante reprennent des idées du blueprint **Low Battery Notifications & Actions** de **Blackshome**. Aucun code n’en a été copié : ce blueprint est diffusé sans licence indiquée.

- [Blueprint d’origine](https://gist.github.com/Blackshome/4010fb83bb8c19b5fa1425526c6ff0e2)

La détection des appareils muets, la mémoire des alertes, la marge de retour et les exclusions par intégration et par fabricant sont propres à cette collection. Les exemples utilisent des identifiants fictifs.

## Système de notifications

Implémentation propre à cette collection, publiée sous la licence GPL-3.0. Elle reprend sous forme de blueprints un système de notifications personnel existant, du même auteur. Les exemples utilisent des identifiants fictifs.

## Télécommandes d’éclairage et extinction automatique

Implémentation propre à cette collection, publiée sous la licence GPL-3.0. Elle remplace des blueprints de tiers utilisés auparavant ; aucun de leur code n’a été repris. Les idées de télécommandes par modèle et de variation par maintien viennent de ces blueprints :

- [IKEA 5 boutons, blancs et préréglages](https://github.com/niro1987/homeassistant-config/tree/main/blueprints/automation/niro1987), par **niro1987** ;
- [Philips Hue Tap Dial](https://github.com/apollo1220/blueprints/blob/main/philips_zigbee_dial.yaml), par **apollo1220** ;
- [Interrupteur IKEA marche/arrêt](https://community.home-assistant.io/t/zha-ikea-tradfri-on-off-switch-incl-dimmer/255412) et [Philips Hue Dimmer RWL022](https://community.home-assistant.io/t/zha-philips-hue-v2-smart-dimmer-switch-and-remote-rwl022/353143), publiés sur le forum Home Assistant.

L’idée d’une minuterie d’extinction vient du blueprint [**Manual Light**](https://gist.github.com/Blackshome/9f9785d7aa0ba7978fa6515a2d73d192) de **Blackshome**, diffusé sans licence indiquée.

Les formats d’événements sont ceux des profils du projet [zha-quirks](https://github.com/zigpy/zha-device-handlers) (licence Apache 2.0), lus pour la compatibilité ; aucun code n’en est repris. Dans la palette, 21 couleurs sont les valeurs d’un assistant personnel de l’auteur. Trois autres sont les blancs de référence Home Assistant, en RGB, relevés sur une capture fournie par l’auteur, sans estimation en kelvins. Les coordonnées numériques des 20 préréglages TRÅDFRI proviennent du [relevé de l’application par node-tradfri-client](https://github.com/AlCalzone/node-tradfri-client/blob/master/src/lib/predefined-colors.ts), projet d’AlCalzone sous licence MIT ; seules ces valeurs de couleur sont reprises.

Les noms Philips Hue, IKEA, TRÅDFRI, STYRBAR, eWeLink, SONOFF et Aqara désignent les appareils compatibles ; ce projet n’est affilié à aucun de ces fabricants. Les exemples utilisent des identifiants fictifs.
