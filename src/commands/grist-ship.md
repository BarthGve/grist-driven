---
description: Ouvrir la PR d'un ticket vers next et la fusionner selon la stratégie du projet (manuelle par défaut), puis nettoyer. À lancer quand le dernier tour de relecture dit Ship allowed yes ; pas pour la production (/grist-release).
argument-hint: <identifiant de la story> <identifiant du ticket>
allowed-tools:
  - Read
  - Bash
---
# grist-ship — Livrer un ticket dans next

Cible : $ARGUMENTS. Clé complète du travail : `<story>/<ticket>`.

Travailler depuis `.worktrees/<story>/<ticket>`, dont la branche doit être exactement `feature/<story>/<ticket>`. Absent, mauvaise branche, HEAD détaché ou dossier de base : arrêt, et jamais de checkout de la branche dans le dossier de base.

## Portes (aucune n'est contournable)
1. `docs/reviews/<story>/<ticket>.md` existe et son **dernier** verdict est positif : `grep '^Ship allowed:' docs/reviews/<story>/<ticket>.md | tail -n 1` doit donner `Ship allowed: yes`. Sinon : « Livraison bloquée, relecture absente ou négative : /grist-review <story> <ticket>. »
2. Le ticket est `review` sur le tableau (`status-get <story>/<ticket>` de `.grist/lib/grist-board.sh`). Un ticket resté `in progress` n'a pas passé la relecture.
3. `docs/product/<story>.md` existe, sinon : « Page produit requise : /grist-docs <story>. »

## Déroulé
1. Commiter le fichier de relecture sur la branche vérifiée s'il ne l'est pas (la PR porte sa relecture), puis lancer la vérification `full` du tableau « Vérifications » d'`AGENTS.md`. Un test en échec arrête tout.
2. Si une PR existe déjà pour la branche : `MERGED` mène directement au nettoyage, `OPEN` se poursuit. Sinon pousser et ouvrir la PR avec `gh pr create --base next`, jamais vers `main` : titre net, description structurée (quoi, pourquoi, comment tester) et verdict de la relecture (gravité max, résumé des constats).
3. Lire la stratégie dans la section « Stratégie de livraison » d'`AGENTS.md` ; faute de mention explicite `auto`, c'est le mode manuel.

## Fusion
Toujours en `--squash` : un ticket égale un commit sur `next`.
- **manuel** : ne pas fusionner. Dire : « PR ouverte : <url> (base : next). La fusion vous revient (relecture humaine, branche protégée, CI) : squash. Après fusion, relancer /grist-ship <story> <ticket> pour nettoyer. »
- **auto** : `gh pr merge <url> --squash --delete-branch=false`, puis nettoyage.

Même tout au vert, jamais de fusion en mode manuel : la porte autorise, l'humain décide. Aucune PR vers `main` ici ; la production est `/grist-release`. Aucun déploiement sur Grist non plus : voir `/grist-deploy`.

## Nettoyage, seulement après une fusion prouvée
1. Preuve : `gh pr view feature/<story>/<ticket> --json state --jq .state` doit répondre exactement `MERGED`. Une PR ouverte, fermée sans fusion ou « sur le point d'être fusionnée » ne compte pas : aucun nettoyage. N'utiliser ni `merge-base --is-ancestor` (un squash réécrit les commits, le test échouerait toujours) ni rien d'autre que cet état.
2. Worktree propre (sinon arrêt, jamais de `--force`) ; exécuter la ligne `isolation` d'`AGENTS.md` pour la remise à zéro si elle existe ; puis `git worktree remove` sur ce worktree exact.
3. Le worktree parti, supprimer la branche : `git branch -D feature/<story>/<ticket>` (le `-D` est nécessaire à cause du squash) et sa copie distante.
4. Tableau : `status-set <story>/<ticket> test`, puis `parent-sync <story>`, qui met l'US parent en `test` quand tous ses tickets sont `test` ou `shipped`.

Terminer en indiquant l'URL de la PR, ou « ticket fusionné dans next, cycle terminé pour ce ticket ».
