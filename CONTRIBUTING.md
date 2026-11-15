# Contribuer

**Français** · [English](CONTRIBUTING.en.md)

Chaque nouveau blueprint doit avoir son propre dossier sous `blueprints/automation/` ou `blueprints/script/`, un guide français et anglais, ses exemples et ses tests. Les fichiers de configuration partagés vont dans `packages/`.

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

Chaque blueprint définit sa version dans `src/<nom>/VERSION`. Le générateur l’utilise pour son nom et, le cas échéant, les en-têtes de ses fichiers communs. La documentation et l’historique doivent reprendre cette version. La première version est **1.0.0** ; un changement de nom affiché ne doit pas renommer les identifiants internes utilisés par les automatisations.
