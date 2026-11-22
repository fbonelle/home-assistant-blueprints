# Contribuer

**Français** · [English](CONTRIBUTING.en.md)

Chaque nouveau blueprint doit avoir son propre dossier sous `blueprints/automation/` ou `blueprints/script/`, un guide français et anglais, ses exemples et ses tests. Un blueprint doit s’installer seul : pas de fichier de configuration à copier dans Home Assistant.

- Utiliser les fonctions standard de Home Assistant et documenter les fichiers nécessaires à l’installation.
- Employer des termes usuels : entités à surveiller, tentatives, historique, relance et retour à la normale. Expliquer les détails techniques dans une page séparée.
- Mettre à jour ensemble les deux langues et leurs liens de navigation.
- Utiliser uniquement des exemples fictifs ; ne publier ni identifiants de production, ni secrets, ni journaux personnels.
- Préserver les crédits et licences des travaux utilisés.
- Modifier les sources sous `src/` ou `tools/`, régénérer les YAML et inclure les fichiers générés dans le changement.
- Exécuter les tests dans un Home Assistant isolé, sans contacter de fournisseur ni d’installation de production.

```sh
.venv/bin/python tools/build.py
.venv/bin/python -m pytest -q
```

Chaque famille définit sa version dans `src/<nom>/VERSION`, au format `<version de Home Assistant>.<compteur>` (par exemple `2026.11.2.0`) ; `tools/versioning.py` en est la seule référence. La version de Home Assistant est celle fixée dans `requirements-test.txt`, avec laquelle tous les tests réussissent. Après une modification d’une famille, `.venv/bin/python tools/versioning.py bump <nom>` augmente le compteur dans `VERSION`, les README et les guides, puis l’historique décrit la modification. Le workflow « Suivi des versions de Home Assistant » (`tools/ha_release.py`) vérifie chaque jour les versions publiques de Home Assistant ; si une version plus récente réussit la génération et tous les tests, il fixe cette version, fait passer toutes les familles à `<version>.0`, complète l’historique et publie sur `main`. En cas d’échec, il ouvre une issue et ne modifie rien. `homeassistant.min_version` reste la version minimale réellement nécessaire. Un changement de nom affiché ne doit pas renommer les identifiants internes utilisés par les automatisations.
