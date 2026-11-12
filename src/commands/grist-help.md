---
description: Afficher le pipeline grist-driven — l'ordre des phases, stories et tickets, commandes Grist. À lancer pour savoir quelle commande vient ensuite en général ; pas pour l'état réel du projet (/grist-status).
argument-hint: (aucun)
allowed-tools:
  - Read
---
# grist-help — Le pipeline grist-driven

Règle unique : pas de modification directe. Toute évolution passe par le flux, et la structure du document Grist (schéma, droits, widgets) ne s'écrit que par les scripts de `grist-kit`, jamais par le MCP.

## Projet déjà en cours
0. `/grist-continue` : état des lieux dans `docs/onboarding.md` et proposition de correspondance des issues, sans rien modifier. Puis on reprend en 1.

## Une fois par produit
1. `/grist-prd <idée>` : cadre le produit (nouveau projet ou reprise), profils et volumétrie
2. `/grist-init` : branches `main` et `next`, dépôt, tableau, wiki, `VERSION`
3. `/grist-stories` : user stories, une issue parent chacune en `backlog`
4. `/grist-stories-review` : relecture du découpage contre le PRD, contexte neuf
5. `/grist-architect` : modèle de données, matrice ACL, widgets, règles en double, déploiement
6. `/grist-design-system` : jetons et composants du profil retenu

## Par story (cadrage, branche `feature/<story>`, documents seulement)
7. `/grist-research <story>` : contexte réel et prémisses vérifiées
8. `/grist-design <story>` : écran, si la story en a un
9. `/grist-plan <story>` : tickets enfants `tNN-…` avec taille (XS à XL) et estimation (pas de 0,5 j)
10. `/grist-docs <story>` : page produit, sans publication

## Par ticket (livraison, branche `feature/<story>/<ticket>`)
La colonne `ready` n'existe que pour les tickets, jamais pour une story.
11. `/grist-execute <story> <ticket>` : code en TDD par sous-agent
12. `/grist-review <story> <ticket>` : relecture et porte `Ship allowed`
13. `/grist-ship <story> <ticket>` : PR vers `next`, puis ticket en `test`

## Commandes Grist (tout au long du flux)
`/grist-schema`, `/grist-acl`, `/grist-widget` écrivent la structure ; `/grist-deploy` met le document à jour dans l'ordre et sur accord ; `/grist-recette` essaie chaque profil en réel ; `/grist-optimise` mesure avant de toucher.

## Versions
14. `/grist-release` : `next` vers `main`, bump, tag, wiki, tableau en `shipped` (ne déploie pas sur Grist)
15. `/grist-feature <slug>` : après la v1, cadre une évolution et ajoute des stories

## Stories et tickets
| | Story (parent) | Ticket (enfant) |
| --- | --- | --- |
| Identifiant | `s01-…` | `s01-…/t01-…` |
| Tableau | backlog, in progress, test, shipped | backlog, **ready**, in progress, review, test, shipped |
| Branche | `feature/<story>` (documents) | `feature/<story>/<ticket>` (code) |
| Issue créée par | `/grist-stories` | `/grist-plan` (à la validation) |

## Chef d'orchestre
- `/grist-orchestrator <story>` : recherche, design, plan (point de validation), docs, puis liste des tickets en backlog.
- `/grist-orchestrator <story> <ticket>` : exécution, relecture, livraison (point de validation).

État réel du projet : `/grist-status`
