# Système de notifications

**Français** · [English](notification_system.en.md)

Quatre blueprints qui forment un système de notifications complet, avec un seul point d’entrée pour toutes les automatisations :

| Blueprint | Type | Rôle |
|---|---|---|
| [Notifications — Répartiteur](../blueprints/script/notification_system/repartiteur.yaml) | script, parallèle | Point d’entrée : choisit les canaux selon le niveau, écarte les doublons, gère la nuit, la bascule de secours et la lecture vocale. |
| [Notifications — Envoi sur un canal](../blueprints/script/notification_system/envoi_canal.yaml) | script, parallèle | Envoie sur un seul canal (application mobile, ntfy ou e-mail) et renvoie `success` si l’envoi a abouti. |
| [Notifications — Lecture vocale](../blueprints/script/notification_system/lecture_vocale.yaml) | script, file d’attente | Lit le message sur les enceintes étiquetées, une annonce après l’autre. |
| [Notifications — Relais vers le mobile](../blueprints/automation/notification_system/relais_mobile.yaml) | automatisation | Envoie les notifications persistantes de Home Assistant au répartiteur et les efface du téléphone quand elles sont supprimées. |

Pourquoi quatre et pas un : un blueprint ne produit qu’un script ou qu’une automatisation. L’envoi sur un canal est un script séparé parce que c’est la seule façon, dans Home Assistant, de savoir qu’un envoi a échoué et de basculer sur un autre canal. La lecture vocale est séparée parce qu’elle fonctionne en file d’attente, alors que le répartiteur traite plusieurs notifications à la fois.

## Installation

1. Importer les quatre blueprints :
   [Répartiteur](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fscript%2Fnotification_system%2Frepartiteur.yaml) ·
   [Envoi sur un canal](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fscript%2Fnotification_system%2Fenvoi_canal.yaml) ·
   [Lecture vocale](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fscript%2Fnotification_system%2Flecture_vocale.yaml) ·
   [Relais vers le mobile](https://my.home-assistant.io/redirect/blueprint_import/?blueprint_url=https%3A%2F%2Fgithub.com%2Ffbonelle%2Fhome-assistant-blueprints%2Fblob%2Fmain%2Fblueprints%2Fautomation%2Fnotification_system%2Frelais_mobile.yaml).
2. Créer deux aides : un **assistant Texte** de longueur maximale 255 pour la mémoire anti-doublon, et, si besoin, une **entrée booléenne** pour couper la lecture vocale.
3. Étiqueter `tts` les lecteurs multimédias qui doivent parler.
4. Créer les scripts et l’automatisation, de préférence dans un *package* : l’[exemple complet](../examples/notification_system/package.yaml) contient les aides et les quatre instances. Créer d’abord l’envoi sur un canal et la lecture vocale, puis le répartiteur, qui les désigne, puis le relais, qui désigne le répartiteur.

L’identifiant du script répartiteur est celui que les automatisations appellent, par exemple `script.notify_dispatch_global`.

## Envoyer une notification

```yaml
action: script.notify_dispatch_global
data:
  title: Fuite d’eau
  message: Eau détectée dans la cave.
  level: critical          # info (défaut), warning, critical, technical
  target: all              # principal (défaut) ou all
  entity_id: binary_sensor.fuite_cave
  tts: false               # true force la lecture vocale
  data:
    snapshot_file: /config/www/snapshots/cave.jpg
    click: /lovelace/securite
```

`data` accepte aussi `icon` (icône ntfy), `actions` (boutons), `priority` et `tags` (ntfy), `html` (ajout au corps de l’e-mail), `notif_id` (identifiant de la notification) et `skip_trace` (pas de notification persistante).

## Comportement

**Canaux par niveau** (réglables) : `info`, `warning` et `critical` vont à l’application mobile ; `technical` va à ntfy ; `critical` part aussi par e-mail. Les niveaux `warning`, `critical` et `technical` sont inscrits au journal de bord.

**Application mobile.** Chaque notification crée aussi une notification persistante `sys_disp_…` dans Home Assistant, sauf quand elle vient du relais. Le tag du téléphone est le même identifiant : supprimer la notification dans Home Assistant l’efface du téléphone. Un identifiant fourni sans préfixe reçoit `sys_disp_` une seule fois. La nuit, le son est coupé ; `critical` perce le mode silencieux (iOS, et Android si le canal y est autorisé).

**Bascule de secours.** Si ntfy échoue, y compris quand son entité est absente ou indisponible (par exemple au démarrage), le message part sur l’application mobile, titre précédé de « 🚨 FALLBACK NTFY : ». Si l’e-mail échoue, un avertissement est écrit dans le journal ; les autres canaux sont servis.

**Anti-doublon.** Un message identique (même niveau, titre et texte) n’est pas renvoyé pendant 5 minutes, même en alternance avec d’autres messages (10 derniers messages retenus). La fenêtre est fixe : une source qui flanche en continu ressort une fois toutes les 5 minutes. Une mémoire illisible n’empêche jamais un envoi. Un doublon écarté est noté au niveau INFO du journal `notification_system`, et non comme un avertissement : c’est le fonctionnement normal.

**Liens.** Sans lien explicite (`data.click`), une notification ouvre l’historique de l’entité indiquée, la page des journaux pour `technical`, sinon la page par défaut. ntfy reçoit un lien vers l’application, l’e-mail un lien web.

**Pièces jointes.** `data.snapshot_file` accepte un chemin local (`/config/www/…`, `/local/…`, `www/…`), une URL ou un URI media source. Chaque canal reçoit la forme qui lui convient : URL pour ntfy et l’application mobile, pièce jointe media source pour l’e-mail. Une image distante est citée dans l’e-mail, SMTP ne sachant pas joindre une URL.

**Lecture vocale.** `critical` est toujours lu ; `warning` est lu en journée quand quelqu’un est présent (`zone.home`) ; `tts: true` force la lecture. Les annonces passent l’une après l’autre. En `critical`, le volume monte puis l’état des enceintes est restauré. Sans enceinte étiquetée disponible, rien n’est lu et un avertissement l’indique.

**Relais.** Le niveau est déduit du titre : 🚨, « Urgence » ou « Panne » → `critical` ; ⚠️ ou « Alerte » → `warning` ; 🔧, 📡, 🔴 ou 🟢 → `technical` ; sinon `info`. Les notifications du répartiteur (`sys_disp_`) ne sont jamais relayées, ce qui empêche toute boucle. Deux listes de préfixes complètent : *jamais relayés* (la notification reste dans Home Assistant) et *supprimés automatiquement* (elle disparaît dès son apparition, sans jamais atteindre le téléphone).

## Limites

- Deux appels réellement simultanés du répartiteur peuvent lire la mémoire anti-doublon avant que l’un n’écrive : Home Assistant n’offre pas d’écriture atomique conditionnelle. Le relais, en file d’attente, sérialise le chemin le plus fréquent.
- Le relais ne voit que les notifications créées après son chargement : Home Assistant ne transmet pas aux automatisations celles déjà présentes. Les notifications persistantes ne survivent pas à un redémarrage, et les intégrations recréent les leurs ensuite.
- La durée d’une annonce critique est estimée à partir de la longueur du texte (débit réglable) avant de restaurer les enceintes.

## Tests

`tests/test_notification_system.py` crée les trois scripts et l’automatisation à partir des blueprints publiés, sur Home Assistant 2026.10.4, avec les vraies aides, notifications persistantes, étiquettes et registres. Seuls les services sortants (application mobile, ntfy, SMTP, synthèse vocale, volume, scènes, journal de bord) sont simulés, et peuvent être mis en échec. Sont vérifiés : chaque niveau, la nuit, la famille, la percée du silence, l’e-mail et ses pièces jointes, la bascule ntfy, l’échec de l’e-mail, l’anti-doublon et l’escalade de niveau, une mémoire corrompue, les identifiants, la lecture vocale (présence, nuit, silence, enceintes manquantes, restauration), et le relais (niveaux, effacement 1:1, absence de boucle, préfixes, démarrage).
