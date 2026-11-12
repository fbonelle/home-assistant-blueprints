# Surveillance des piles et batteries

**Français** · [English](battery_watch.en.md) · [Accueil](../README.md)

Version **1.0.0**. Un blueprint autonome qui signale tout de suite chaque pile ou batterie à remplacer, puis envoie un récapitulatif à l’heure choisie. Aucun fichier commun ni composant personnalisé n’est nécessaire.

## Installation

1. Utiliser Home Assistant **2026.10 ou plus récent**.
2. [Importer le blueprint](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fbattery_watch%2Fsurveillance_piles.yaml).
3. Dans **Paramètres → Appareils et services → Entrées**, créer un assistant **Texte**, longueur minimale **0**, maximale **255**. Le réserver à cette automatisation.
4. Créer une automatisation depuis le blueprint, choisir l’assistant, puis renseigner les **Actions d’alerte immédiate** et les **Actions du récapitulatif** (par exemple une notification sur un téléphone ou un script de notification existant).
5. Désactiver l’ancienne automatisation qui envoyait le même récapitulatif, pour ne pas recevoir deux messages.

Les [exemples d’automatisation](../examples/battery_watch/automations.yaml) et d’[assistant YAML](../examples/battery_watch/helpers.yaml) utilisent uniquement des identifiants fictifs. L’assistant créé depuis l’interface suffit. Adapter le chemin du blueprint si Home Assistant propose un autre nom lors de l’importation.

## Ce qui est signalé

| Situation | Message |
|---|---|
| Niveau de pile strictement inférieur au seuil (20 % par défaut) | `• Télécommande salon — 18 %` |
| Appareil indisponible depuis plus du délai réglé (6 heures par défaut) | `• Détecteur de fumée — muet depuis 7 h` |
| Alerte « pile faible » remontée par l’appareil (capteur binaire de classe batterie à « on ») | `• Détecteur de fuite — alerte pile faible` |

Une pile vide rend souvent l’appareil muet au lieu d’annoncer un niveau bas : c’est pourquoi l’indisponibilité prolongée est signalée. Le délai écarte les coupures passagères d’une passerelle ou d’un service cloud, qui rendent tous ses appareils indisponibles en même temps. L’état « inconnu », transitoire au démarrage, est ignoré. Régler le délai à 0 désactive cette règle.

Seules les entités de classe **batterie** sont examinées : capteurs (`sensor`) et, si l’option est active, capteurs binaires (`binary_sensor`).

## Appareils exclus par défaut

Les téléphones, montres, ordinateurs et onduleurs sont rechargés au quotidien ou suivis ailleurs. Ils sont exclus par défaut :

- intégrations `mobile_app`, `icloud`, `icloud3` et `nut` ;
- appareils du fabricant **Apple**.

L’intégration est lue sur la configuration à laquelle chaque entité est rattachée. Une entité qu’une intégration ne recense plus, mais qui reste rattachée à sa configuration, est donc aussi exclue. Les exclusions se complètent par entité, par appareil ou par étiquette : les entités et appareils portant une étiquette exclue sont ignorés.

## Alerte immédiate et mémoire

La vérification a lieu toutes les 5 minutes par défaut. Chaque appareil qui **entre** dans la liste des piles à vérifier déclenche les **Actions d’alerte immédiate**, une seule fois. L’assistant Texte retient les appareils déjà signalés, y compris après un redémarrage :

- une pile qui continue de baisser (18 %, 15 %, 9 %…) n’est pas signalée à nouveau ;
- un appareil signalé n’est considéré comme réparé qu’au-dessus du **seuil plus la marge de retour** (5 points par défaut), ou lorsque son alerte binaire repasse à « off » ; une pile qui oscille autour du seuil ne produit donc pas de nouvelles alertes ;
- un appareil signalé qui devient muet ou inconnu, par exemple pendant un redémarrage, reste mémorisé et n’est pas signalé une seconde fois ;
- une pile remplacée puis à nouveau faible plus tard est signalée de nouveau.

**Première vérification.** Lorsque l’assistant est vide, la première vérification enregistre la situation existante sans alerte immédiate ; le récapitulatif et la notification persistante la présentent. Ensuite, seules les nouvelles entrées déclenchent une alerte immédiate.

**Capacité.** Chaque appareil occupe une empreinte de 6 caractères dans l’assistant : jusqu’à **36 appareils** en alerte simultanément sont mémorisés. Au-delà, les suivants n’apparaissent que dans le récapitulatif et la notification persistante, et un avertissement est écrit dans le journal `battery_watch`.

## Récapitulatif et notification persistante

À l’heure et aux jours choisis, les **Actions du récapitulatif** reçoivent la liste complète des piles à vérifier. Le récapitulatif n’est envoyé que s’il y a quelque chose à signaler, sauf si l’option **Envoyer aussi le récapitulatif lorsque tout va bien** est active. **Menu → Exécuter les actions** envoie le récapitulatif immédiatement, ce qui permet de tester les actions.

Une notification persistante Home Assistant, propre à cette automatisation, est mise à jour à chaque changement de la liste et retirée lorsque plus rien n’est à vérifier. Elle peut être désactivée.

Les **Conditions supplémentaires** (par exemple : personne à la maison) s’appliquent aux alertes et au récapitulatif. La mémoire et la notification persistante restent à jour même lorsque ces conditions échouent ; un appareil détecté pendant ce temps n’est pas signalé une seconde fois.

## Variables disponibles dans les actions

| Variable | Contenu |
|---|---|
| `battery_title` | Titre prêt à l’emploi : `🔋 Pile ou batterie à remplacer (2)` ou `Piles et batteries à vérifier (3)`. |
| `battery_message` | Une ligne par appareil, triée par nom : les nouveaux appareils pour l’alerte, tous les appareils pour le récapitulatif. |
| `battery_new` | Liste des nouveaux appareils. |
| `battery_all` | Liste de tous les appareils à vérifier. |
| `battery_count` | Nombre d’appareils à vérifier. |

Chaque élément de liste contient `e` (entité), `n` (nom), `r` (raison : `level`, `silent` ou `alert`), `v` (niveau en %, pour `level`) et `h` (heures d’indisponibilité, pour `silent`).

Exemple avec un script de notification existant :

```yaml
alert_actions:
  - action: script.notification_maison
    data:
      title: "{{ battery_title }}"
      message: "{{ battery_message }}"
```

## Configuration incorrecte

Un assistant absent, partagé ou de longueur maximale différente de 255, ou un réglage hors limites, bloque l’automatisation sans modifier la mémoire. Le problème est affiché dans une notification persistante et écrit dans le journal `battery_watch`.

## Limites

- Le blueprint lit les niveaux annoncés par les intégrations ; il ne mesure pas l’état réel des piles.
- Un appareil indisponible pour une autre raison qu’une pile vide (prise débranchée, passerelle en panne au-delà du délai) est aussi signalé comme muet.
- Les exclusions par fabricant comparent le nom déclaré par l’intégration, sans tenir compte des majuscules.

[Historique](../CHANGELOG.md) · [Origine et licence](../NOTICE.md)
