# Contribuer

**Français** · [English](CONTRIBUTING.en.md)

Chaque nouveau blueprint doit avoir son propre dossier sous `blueprints/automation/` ou `blueprints/script/`, un guide français et anglais, ses exemples et ses tests. Un blueprint doit s’installer seul : pas de fichier de configuration à copier dans Home Assistant.

- Utiliser les fonctions standard de Home Assistant et documenter les fichiers nécessaires à l’installation.
- Employer des termes usuels : entités à surveiller, tentatives, historique, relance et retour à la normale. Expliquer les détails techniques dans une page séparée.
- Mettre à jour ensemble les deux langues et leurs liens de navigation.
- Écrire en anglais le code, les commentaires, les identifiants, les noms de fichiers, les noms des blueprints, les formulaires, les messages, la lecture vocale et les journaux. Les guides restent en français et en anglais et citent les libellés anglais tels qu’ils apparaissent.
- Trier par ordre alphabétique les tableaux qui listent des éléments (blueprints, familles, anciens réglages) ; les tableaux d’actions et de réglages suivent l’ordre du formulaire.
- Utiliser uniquement des exemples fictifs ; ne publier ni identifiants de production, ni secrets, ni journaux personnels.
- Préserver les crédits et licences des travaux utilisés.
- Modifier les sources sous `src/` ou `tools/`, régénérer les YAML et inclure les fichiers générés dans le changement.
- Exécuter les tests dans un Home Assistant isolé, sans contacter de fournisseur ni d’installation de production. Home Assistant n’installe aucun paquet pendant les tests (`tests/conftest.py`) : une dépendance d’intégration absente ou dans une autre version fait échouer le test qui la charge. `.venv/bin/python tools/ha_release.py sync-requirements` réécrit alors ces dépendances dans `requirements-test.txt` d’après la version de Home Assistant installée.

```sh
.venv/bin/python tools/build.py
.venv/bin/python -m pytest -q
```

La CI exécute aussi la suite sur la version minimale (`homeassistant==` suivi de `python tools/versioning.py min`, puis `pip install $(python tools/ha_release.py integration-requirements)`).

Chaque famille définit sa version dans `src/<nom>/VERSION`, au format `<version de Home Assistant>.<compteur>` (par exemple `2026.11.2.0`) ; `tools/versioning.py` en est la seule référence. La version de Home Assistant est celle fixée dans `requirements-test.txt`, avec laquelle tous les tests réussissent. Après une modification d’une famille, `.venv/bin/python tools/versioning.py bump <nom>` augmente le compteur dans `VERSION`, les README et les guides, puis l’historique décrit la modification. Le workflow « Follow Home Assistant releases » (`tools/ha_release.py`) vérifie chaque jour les versions publiques de Home Assistant ; si une version plus récente réussit la génération et tous les tests, il fixe cette version, fait passer toutes les familles à `<version>.0`, complète l’historique et publie sur `main`. En cas d’échec, il ouvre une issue et ne modifie rien. `homeassistant.min_version` reste la version minimale prise en charge : le mois de la version courante validée moins trois mois calendaires (version `.0` de ce mois, testée en CI). Un changement de nom affiché ne doit pas renommer les identifiants internes utilisés par les automatisations.
