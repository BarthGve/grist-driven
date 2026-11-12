---
description: Livrer next vers main — bump de VERSION, PR, tag, wiki, tableau en shipped. À lancer quand des stories parent sont en test ; ne déploie rien sur Grist (voir /grist-deploy) et ne livre pas un ticket (/grist-ship).
argument-hint: (aucun)
allowed-tools:
  - Read
  - Bash
  - AskUserQuestion
---
# grist-release — Version de production (`next` vers `main`)

Se placer à la racine du dépôt, sur `next`. Jamais depuis une branche de travail. Cette commande publie une version du **dépôt** ; le document Grist, lui, se met à jour par `/grist-deploy`, séparément et sur accord.

## 1. Candidats
Lancer une fois `bash .grist/lib/grist-board.sh status-all` et garder, parmi les stories de `docs/stories.md`, celles dont la ligne dit exactement `test`. Aucune : « Rien à livrer : livrer des tickets dans next jusqu'à ce que leur story parent atteigne test. » Présenter les stories retenues et leurs tickets.

## 2. Type de version
Demander : majeure, **mineure** (par défaut) ou correctif.

## 3. Bump sur `next`, une seule fois par version
Si `VERSION` diffère déjà de celui de `origin/main` **et** qu'une PR `next` vers `main` est ouverte (`gh pr list --base main --head next --state open`), s'arrêter : « Livraison déjà en vol, ne pas incrémenter une seconde fois : fusionner cette PR. » Sinon :
```bash
bash .grist/lib/grist-version.sh bump <major|minor|patch>
```
Le script réécrit `VERSION`, aligne `pyproject.toml` et `package.json` s'ils existent et ouvre la section du `CHANGELOG.md`. Commiter ces fichiers sur `next` (`🔧 CHORE: version <x.y.z>`) et pousser. Le hook de poussée vers `main` refuse une version inchangée ou absente du `CHANGELOG.md` : le bump vient donc avant la PR.

## 4. PR vers `main`
`gh pr create --base main --head next --title "Version <x.y.z>"`, avec en description les stories livrées. Ne pas fusionner sans accord explicite : par défaut on s'arrête à la PR ouverte. Elle se fusionne en **squash** : une version égale un commit sur `main`, jamais de merge de `next`.

## 5. Après fusion prouvée seulement
La preuve est `gh pr view <url> --json state --jq .state` égal à `MERGED`. Alors :
1. Récupérer `origin/main` et poser le tag `v<x.y.z>` sur **ce** commit (celui du squash sur `main`, jamais un commit de `next`), puis pousser le tag.
2. Wiki, une page par story livrée : `bash .grist/lib/grist-wiki.sh publish "$(pwd)" "$(cat VERSION)" <story>...`
3. Tableau : `status-set <story> shipped` pour chaque story livrée, puis le même pour chacun de ses tickets (`<story>/<ticket>`).

Terminer par : « Version <x.y.z> publiée, wiki à jour, tableau en shipped. Le document Grist n'est pas touché : /grist-deploy pour le mettre à jour. » ou par l'URL de la PR si elle attend sa fusion.
