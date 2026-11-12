---
description: Implémenter un ticket enfant en TDD par le sous-agent implementer, dans son worktree. À lancer quand le plan est validé et le ticket prêt, ou pour corriger une relecture bloquée ; pas pour planifier (/grist-plan) ni pour un simple ajustement de présentation.
argument-hint: <identifiant de la story> <identifiant du ticket>
allowed-tools:
  - Read
  - Glob
  - Agent
  - Bash
---
# grist-execute — Un ticket, par délégation

Cible : $ARGUMENTS

## Règle de cette commande
Le code est écrit par le sous-agent `implementer`, jamais par toi : cette commande n'a ni Write ni Edit, exprès. Interdits : démarrer sans plan validé ni ticket prêt, travailler depuis le dossier de base, créer ou changer la branche du ticket dans ce dossier, résumer un travail que l'agent n'a pas fait. Outil Agent indisponible : signaler l'erreur et s'arrêter.

## Avant de déléguer (on s'arrête au premier échec)
1. Retrouver `<story>` et `<ticket>` dans `docs/stories.md` et `docs/plans/<story>.md`. Ambigu : lister et s'arrêter.
2. Statut du ticket sur le tableau, par `status-get <story>/<ticket>` du script `.grist/lib/grist-board.sh` :
   - `ready` ou `in progress` : lancer `require-ready <story>/<ticket>`, puis passer le ticket en `in progress` avec `status-set` ;
   - `review` : retour en correction, remettre `in progress` (transition permise) ;
   - tout autre statut : arrêt, nommer le statut et ce qui manque (un ticket `backlog` doit d'abord passer en `ready` sur le tableau ; l'US parent n'est jamais `ready`).
3. Appeler le sous-agent `worktree-manager` pour `.worktrees/<story>/<ticket>` sur `feature/<story>/<ticket>`, depuis `next`. Continuer une fois le chemin absolu et la branche exacte confirmés.
4. Depuis ce worktree, lire `docs/plans/<story>.md` : `validated: yes` exigé. Une dépendance du ticket qui n'est ni `test` ni `shipped` : arrêt, la nommer.
5. Si la dernière ligne `Ship allowed:` de `docs/reviews/<story>/<ticket>.md` dit `no`, c'est une correction : les constats de ce dernier tour passent en premier.

## Délégation
Appeler l'outil Agent avec :
- subagent_type: implementer
- dossier de travail : le chemin absolu du worktree du ticket
- prompt : réaliser le ticket `<ticket>` de la story `<story>` d'après `docs/plans/<story>.md`, uniquement ses tâches, en suivant `docs/architecture.md` et `AGENTS.md` ; lire `docs/research/<story>.md` s'il existe. TDD strict, tâche après tâche, un seul commit en fin de ticket. Les écritures de structure Grist passent par `grist-kit`, jamais par le MCP. Pas de worktree créé, pas de changement de branche.
- en correction, ajouter en tête : corriger d'abord, test en premier, chaque constat critique ou majeur du dernier tour de `docs/reviews/<story>/<ticket>.md`.

## Compte rendu
Tâches faites, fichiers touchés, tests ajoutés, points bloquants.

Terminer par : « Implémentation faite. Suite : /grist-review <story> <ticket> »
