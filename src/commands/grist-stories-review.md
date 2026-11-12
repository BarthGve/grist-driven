---
description: Faire relire le découpage en stories contre le périmètre du PRD par un sous-agent au contexte neuf, l'endroit le moins cher pour rattraper un mauvais découpage. À lancer après /grist-stories ; pas pour relire du code (/grist-review).
argument-hint: (aucun)
allowed-tools:
  - Read
  - Grep
  - Glob
  - Agent
  - Write
---
# grist-stories-review — Relecture du découpage

## Règle de cette commande
Le jugement appartient au sous-agent `stories-reviewer`, pas à toi : tu as sans doute écrit les stories, donc tu ne vois pas leurs trous. Tu n'as le droit ni de corriger `docs/stories.md`, ni d'adoucir un verdict pour faire avancer le flux. Ta seule écriture est le rapport `docs/reviews/stories.md`. Si l'outil Agent est indisponible, signale l'erreur et arrête-toi.

## Déroulé
1. **Prérequis.** `docs/prd.md` et `docs/stories.md` doivent exister ; sinon arrêt, avec renvoi à `/grist-prd` ou `/grist-stories`.
2. **Délégation.** Appeler l'outil Agent avec :
   - subagent_type: stories-reviewer
   - prompt : relire `docs/stories.md` contre `docs/prd.md` (et `docs/architecture.md` s'il existe, pour les droits), en remplissant `templates/stories-review-checklist.md`.
3. **Rapport.** Écrire le rapport complet dans `docs/reviews/stories.md`. Il se termine par les deux lignes exactes `Gravité max : …` et `Stories prêtes : oui` ou `Stories prêtes : non` (un seul point critique suffit pour « non »). Le commiter sur la branche d'intégration (`📝 DOCS: relecture des stories`).
4. **Issue.**
   - « non » : « Relecture bloquante (<gravité>). Corriger docs/stories.md (relancer /grist-stories ou l'éditer), puis relancer /grist-stories-review. »
   - « oui » : « Relecture passée. Suite : /grist-architect »

Cette porte est souple : rien ne l'impose mécaniquement, mais `/grist-status` l'affiche et `/grist-research` avertit si elle manque. Corriger un découpage ici coûte une ligne de Markdown ; après cinq stories livrées, cela coûte des cycles.
