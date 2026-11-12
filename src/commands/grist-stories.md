---
description: Découper le PRD en user stories livrables et exploitables par un agent, avec une issue parent par story. À lancer après /grist-init, ou après /grist-feature pour en ajouter ; pas pour les tickets enfants (/grist-plan).
argument-hint: (aucun)
allowed-tools:
  - Read
  - Write
  - Bash
  - AskUserQuestion
---
# grist-stories — Découpage en user stories

## Avant de commencer
- `docs/prd.md` obligatoire. Lire aussi `docs/architecture.md` s'il existe : la matrice ACL dit quelles stories touchent aux droits.
- `.grist/config.json` conseillé (créé par `/grist-init`). Sans lui, aucune issue parent ne peut être créée : prévenir, et ne continuer qu'avec l'accord de l'utilisateur, en écrivant seulement `docs/stories.md`.

Appliquer le skill `grist-agentic-stories`. Gabarit : `templates/stories.md`. Rien de ce que le PRD place hors périmètre ne devient une story.

## Déroulé
1. **Découper.** Chaque story est une tranche de bout en bout, testable, qui livre quelque chose à un profil du PRD. Identifiant : `s<numéro>-<slug court>` (par exemple `s01-saisir-une-demande`) ; il nomme tous les fichiers du flux et la branche, donc court et stable.
2. **Critères.** Pour chaque story : des critères d'acceptation dont chacun peut devenir un test, une note d'exécution (tables, widgets, règles d'accès concernés) et une complexité de 1 à 5. Un 5 se découpe maintenant. Une story qui touche aux droits porte un critère par profil concerné.
3. **Ordre.** Par dépendance : aucune story ne suppose un travail qui vient après elle.
4. **Écrire** `docs/stories.md` et le commiter sur `next` (sur la branche par défaut si `next` n'existe pas encore) : `📝 DOCS: stories`.
5. **Tableau.** Une issue parent par story, au statut `backlog`, sans ticket enfant : `bash .grist/lib/grist-board.sh issue-create-us <story> "<titre>" <fichier-corps>`. Le corps tient en un résumé et les critères. Une issue dont le titre commence déjà par `[<story>]` n'est pas recréée.

## Projet repris avec des issues déjà écrites
Si `docs/onboarding.md` existe, lire sa section `## Correspondance des issues ouvertes` avant toute création. Pour chaque story citée dans ce tableau, l'issue existe : ne pas en ouvrir une seconde. Demander, issue par issue, si on l'adopte :
- oui : `bash .grist/lib/grist-board.sh issue-adopt <story> <numéro> "<titre>"` (renomme, ajoute au tableau, met `backlog`). Jamais `status-set` pour cela : une issue écrite à la main n'est pas encore un élément du tableau ;
- non : la laisser telle quelle et créer l'issue parent normalement.

Rien n'est renommé ni déplacé sans réponse explicite, et les issues de la section « Issues fermées » ne sont jamais touchées.

Terminer par : « Stories prêtes dans docs/stories.md (issues parent en backlog). Suite : /grist-stories-review »
