# Origine et licence

**Français** · [English](NOTICE.en.md)

## Surveillance des intégrations

Le travail sur ce blueprint a commencé à partir de **Reload Integrations Automatically**, par **danimart1991** :

- [Projet d’origine](https://github.com/danimart1991/home-assistant-blueprints)
- [Blueprint d’origine](https://github.com/danimart1991/home-assistant-blueprints/blob/main/automation/reload-integrations/reload-integrations.en.yaml)
- Licence : GNU General Public License, version 3, conservée dans [LICENSE](LICENSE).

La présente implémentation a été profondément remaniée. Elle est maintenue séparément ; ses modifications ne doivent pas être attribuées à l’auteur du projet d’origine.

La **version 1.0.0** est la première version publiée dans cette collection, le 4 novembre 2026. Les exemples utilisent des identifiants fictifs et ne configurent aucune installation réelle.

## Lampe avec télécommande IKEA STYRBAR

Implémentation distincte, publiée sous la licence GPL-3.0 de cette collection. Aucun code des blueprints contrôleur/hook précédemment utilisés n’a été copié.

Les coordonnées numériques des 20 préréglages TRÅDFRI proviennent du [relevé de l’application par node-tradfri-client](https://github.com/AlCalzone/node-tradfri-client/blob/master/src/lib/predefined-colors.ts), projet d’AlCalzone sous licence MIT. Seules ces valeurs de couleur sont reprises. Les trois couleurs RGB de référence Home Assistant correspondent aux aplats de la capture fournie, sans estimation en kelvins.

Les noms IKEA, TRÅDFRI et STYRBAR désignent les appareils compatibles ; ce projet n’est pas affilié à IKEA. Les micrologiciels, la radio et le rendu physique des ampoules ne sont pas certifiés par les tests simulés.

## Surveillance des piles

Implémentation distincte, publiée sous la licence GPL-3.0 de cette collection. Ses fonctions de récapitulatif à heure fixe, de choix des jours et de notification persistante reprennent des idées du blueprint **Low Battery Notifications & Actions** de **Blackshome**. Aucun code n’en a été copié : ce blueprint est diffusé sans licence indiquée.

- [Blueprint d’origine](https://gist.github.com/Blackshome/4010fb83bb8c19b5fa1425526c6ff0e2)

La détection des appareils muets, la mémoire des alertes, la marge de retour et les exclusions par intégration et par fabricant sont propres à cette collection. Les exemples utilisent des identifiants fictifs.
