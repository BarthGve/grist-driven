---
description: Déployer le projet sur le document Grist réel dans l'ordre exact (schéma, formules, ACL, amorçage, pages, widgets), avec dry-run, version et vérification finale. À lancer après la relecture d'un ticket qui touche Grist ou avant une mise en service ; pas pour fusionner le code (/grist-ship).
argument-hint: [--doc <identifiant du document>] [widget ...]
allowed-tools:
  - Read
  - Glob
  - Grep
  - Write
  - Edit
  - AskUserQuestion
  - Bash
---
# grist-deploy — Mettre en ligne

Cible : $ARGUMENTS (sans `--doc`, le document de `GRIST_DOC_ID`).

Lire le skill `grist-deploy`. Tout passe par `grist-kit`, sur le document réel, jamais par le MCP : il ne touche pas à la structure. Chaque étape est idempotente et se joue d'abord avec `--dry-run`.

## Avant
Tests verts, branche propre. Demander à l'utilisateur la version (patch, minor ou major), inscrire l'entrée en tête du journal des versions, puis relancer l'inliner (il régénère `CHANGELOG.md`). Notes pour l'utilisateur final, sans jargon. Pas de version, pas de déploiement.

## Ordre (il compte)
1. `python -m grist_kit apply-schema`
2. `python -m grist_kit maj-formules` : en `--dry-run`, la liste des `divergentes` se traite à la main. Toute ligne inattendue arrête le déploiement.
3. `python -m grist_kit apply-acl`
4. `python -m grist_kit amorcer` (une seule fois)
5. `python -m grist_kit creer-page` pour chaque widget neuf
6. `python -m grist_kit deployer <widget>`

Pour chaque étape : `--dry-run`, lecture du plan à voix haute, accord de l'utilisateur, exécution réelle. Un widget qui lit une table absente affiche « Chargement impossible » : les étapes 1 à 4 passent avant la 6.

## Après
`python -m grist_kit deployer <widget> --check` pour chaque widget, puis `python -m grist_kit pages` pour retirer les pages de tables brutes. Un 403 du pare-feu : ne pas insister, voir le skill ; un 413 : bundle trop gros.

Terminer par le récapitulatif (version, étapes passées, contrôles). Suite : /grist-recette.
