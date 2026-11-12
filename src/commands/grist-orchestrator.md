---
description: Enchaîner le cadrage d'une story, ou le cycle complet d'un ticket, en gardant les points de validation humains. À lancer pour chaîner les phases d'une story ou d'un ticket ; pas pour une seule phase (lancer sa commande) ni pour une version.
argument-hint: <identifiant de la story> [identifiant du ticket]
allowed-tools:
  - Read
  - Glob
  - Grep
  - Write
  - AskUserQuestion
  - Agent
  - Bash
---
# grist-orchestrator — Chef d'orchestre

Cible : $ARGUMENTS

Tu diriges : tu ne fais jamais en direct le travail d'une phase qu'un sous-agent possède, et tu n'écris jamais de code d'application. Les points de validation sont de vrais AskUserQuestion. Ce n'est pas un pilote automatique.

Premier argument : la story, retrouvée dans `docs/stories.md`. Second argument, s'il existe : le ticket, retrouvé dans `docs/plans/<story>.md`. Sans second argument, mode A ; avec, mode B.

## Mode A : cadrage d'une story

**Phase 0, prérequis.** `docs/prd.md`, `docs/stories.md`, `docs/architecture.md` doivent exister ; sinon arrêt avec la commande à lancer (`/grist-prd`, ou `/grist-continue` si du code existe déjà hors de `docs/` avec plus d'un commit ; `/grist-stories` ; `/grist-architect`). Avertir, sans bloquer, si `docs/reviews/stories.md` manque ou dit `Stories prêtes : non`. Appeler le sous-agent `worktree-manager` pour `.worktrees/<story>` sur `feature/<story>` depuis `next` : toutes les phases s'y déroulent.

**Phase 1, recherche.** Suivre `/grist-research` si `docs/research/<story>.md` manque.

**Phase 2, design.** Suivre `/grist-design` si la story a un écran et que `docs/designs/<story>.md` manque ; arrêt si `docs/design-system.md` manque.

**Phase 3, plan et validation.** Suivre `/grist-plan`. Question : « Valider ce plan ? » (valider, ou relire d'abord). À la validation : `validated: yes` et une issue enfant par ticket, comme dans `/grist-plan`.

**Phase 4, docs.** Suivre `/grist-docs` : `docs/product/<story>.md`, sans publication.

**Phase 5, passage de relais.** Lister les tickets encore en `backlog` (plan, plus un `status-all` si `.grist/config.json` existe) et demander de passer le suivant en `ready`, puis de lancer le mode B ou `/grist-execute`. Finir sur cette liste : ne pas démarrer l'exécution en mode A.

## Mode B : cycle d'un ticket

**Phase 0.** Le plan doit porter `validated: yes` et la page produit exister (sinon avertir de lancer `/grist-docs`). Le ticket doit être `ready` ou `in progress` : `require-ready <story>/<ticket>` du script `.grist/lib/grist-board.sh`. Worktree : `.worktrees/<story>/<ticket>`, branche `feature/<story>/<ticket>`.

**Phase 1, exécution.** Comme `/grist-execute` : ticket en `in progress`, sous-agent `implementer` pour ce seul ticket.

**Phase 2, relecture.** Comme `/grist-review`. Si le dernier tour dit `Ship allowed: no`, boucle de correction par l'exécution (deux fois au plus), chaque relecture ajoutant un tour. Un verdict positif passe le ticket en `review`.

**Phase 3, point de livraison.** Demander : « Livrer maintenant ? » (livrer, ou pas maintenant). Seul un « livrer » explicite lance `/grist-ship` (PR avec `--base next` ; après `MERGED`, ticket en `test` et `parent-sync`).

Terminer par l'issue de la livraison de ce ticket (URL de la PR, ou fusionné et tableau en `test`).
