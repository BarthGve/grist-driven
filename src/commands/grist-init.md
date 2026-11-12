---
description: Mettre en place le flux du projet déjà installé — branches main/next, dépôt distant, tableau GitHub, wiki, VERSION. À lancer une fois, après /grist-prd ; ne recrée pas le projet (c'est install.sh) et n'adopte pas du code existant (/grist-continue).
argument-hint: (aucun)
allowed-tools:
  - Read
  - Bash
  - AskUserQuestion
---
# grist-init — Flux, tableau et wiki

`install.sh` a déjà posé le gabarit du projet, les commandes et `grist-kit`. Cette commande n'y touche pas : elle ne crée que ce qui concerne le suivi du travail.

## Conditions d'arrêt
- `docs/prd.md` absent : s'arrêter et renvoyer à `/grist-prd`.
- `.grist/lib/grist-init.sh` absent : le projet n'a pas été installé (ou l'a été sans le flux git) ; renvoyer à `install.sh`.
- `gh auth status` en échec : demander à l'utilisateur de lancer `gh auth login`.

## À confirmer (AskUserQuestion, une question à la fois)
1. Créer un dépôt distant ? Sinon, tout reste local.
2. Nom du dépôt (par défaut, le dossier courant), propriétaire (compte ou organisation), visibilité (privé par défaut).
3. Titre du tableau GitHub.

Rien n'est créé avant la confirmation.

## Exécution
```bash
bash .grist/lib/grist-init.sh run --repo <nom> --owner <login> --private --title "<titre>" --yes
```
(`--public` pour un dépôt public, `--no-remote` pour rester en local.) Le script crée `next` à côté de `main`, le tableau avec ses six statuts, le wiki, le fichier `VERSION` et `.grist/config.json`. Il est idempotent : ce qui existe est reconnu, seuls les manques sont comblés. Les GitHub Actions restent coupées : les contrôles tournent en local par les hooks git.

Conclure en listant ce qui a été créé ou reconnu (dépôt, `next`, tableau, wiki, `VERSION`), puis : « Suite : /grist-stories »
