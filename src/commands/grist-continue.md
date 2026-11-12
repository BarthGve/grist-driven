---
description: Adopter le flux sur un projet Grist déjà en cours (code, classeur, issues existants) en écrivant un état des lieux sans rien modifier. À lancer quand le travail a commencé avant le flux ; pas pour un dépôt vide (/grist-prd) ni pour une évolution d'un produit déjà cadré (/grist-feature).
argument-hint: (aucun, lit le dépôt courant)
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
  - Write
  - AskUserQuestion
---
# grist-continue — Reprendre un projet en cours

Le projet fonctionne déjà, sa documentation n'existe pas. Le seul livrable est `docs/onboarding.md`. Bash ne sert qu'à des lectures (`git log`, `git ls-files`, `gh issue list`) et au commit final : ni écriture sur le tableau, ni appel d'écriture à `gh`, ni écriture sur un document Grist.

## Prérequis
- Des fichiers source hors de `docs/` et plus d'un commit dans l'historique. Sinon : « Dépôt vide : /grist-prd. »
- Pas de `docs/prd.md`. S'il existe : « Projet déjà cadré : /grist-status. »

## Ce qu'il ne faut pas faire
- Analyser la structure, les conventions ou la pile : c'est le travail de `/grist-architect` avec le skill `grist-codebase-analysis`, et une seconde analyse ici deviendrait une seconde vérité qui dérive.
- Créer, renommer, fermer ou déplacer la moindre issue : le tableau n'existe pas encore (`.grist/config.json` est écrit par `/grist-init`). On **propose** une correspondance, rien de plus.
- Écrire `docs/prd.md`, `docs/stories.md` ou `docs/architecture.md`.

## Relever l'état réel (lecture seule)
1. Ce que l'application fait pour ses utilisateurs : écrans, widgets, tables qu'ils manipulent, flux principaux. La question est « que fait-elle », pas « comment est-elle construite ».
2. L'historique (`git log --oneline`) : ce qui est livré et quand.
3. Si `gh auth status` réussit, les issues ouvertes et fermées (`gh issue list --state open|closed`). Sinon, avertir clairement, sauter la correspondance et écrire quand même l'état des lieux : l'absence de tableau ne bloque jamais la documentation.

## À confirmer (une question à la fois)
Le résumé du produit en une phrase ; les flux que l'utilisateur tient pour déjà livrés ; pour chaque issue ouverte, un identifiant proposé `s<NN>-<slug>` à confirmer, amender ou exclure. Les réponses sont consignées, rien n'est appliqué.

## Écrire `docs/onboarding.md`
Cinq sections, dans cet ordre :
1. `## Ce que fait l'application` : la boucle de valeur et les profils d'utilisateurs, tels que confirmés.
2. `## Base livrée` : les flux livrés, avec les commits ou dates qui le montrent.
3. `## Reste à faire (pistes)` : non contractuel, le vrai découpage est celui de `/grist-stories`.
4. `## Correspondance des issues ouvertes` : **intitulé repris tel quel par `/grist-stories`**, qui le cherche à la lettre ; ne pas le traduire ni le reformuler. Un tableau, une ligne par issue ouverte, de cette forme exacte :

   | Issue | Titre | Story proposée |
   | --- | --- | --- |
   | #12 | Export CSV | s03-export-csv |

   Ce n'est qu'une proposition : `/grist-stories` la lit après `/grist-init` et demande une confirmation par issue.
5. `## Issues fermées (contexte)` : listées, jamais touchées.

Rien n'est écrit sans validation de l'utilisateur.

## Commit
`next` n'existe pas encore : commiter sur la branche par défaut, documents seulement (le hook ne demande alors aucun plan) : `git add docs/onboarding.md` puis `📝 DOCS: état des lieux`.

Terminer par : « État des lieux prêt dans docs/onboarding.md (N issues mises en correspondance, rien de modifié). Suite : /grist-prd (mode reprise) »
