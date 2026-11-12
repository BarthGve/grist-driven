---
description: Fixer le comment technique du produit dans docs/architecture.md — modèle de données, matrice ACL, widgets, règles en double, déploiement — et consigner les décisions en ADR. À lancer une fois, après /grist-stories-review ; pas pour le contexte d'une story (/grist-research) ni pour les visuels (/grist-design-system).
argument-hint: (aucun)
allowed-tools:
  - Read
  - Glob
  - Grep
  - Write
  - Edit
  - Bash
  - AskUserQuestion
---
# grist-architect — Architecture du produit

La pile est déjà décidée : Grist, `grist-kit`, et le profil de widgets lu dans `design_system` de `.grist-driven.json` (`dsfr` ou `ui-kit`). Cette commande ne la rediscute pas ; elle décrit ce qu'on construit dessus.

Lire `docs/prd.md` et `docs/stories.md`. Gabarit : `templates/architecture.md`. Si le dépôt contient déjà du code ou un classeur décrit par `docs/onboarding.md`, appliquer le skill `grist-codebase-analysis` d'abord : on cartographie l'existant avant de décider.

## Les cinq sections à produire dans `docs/architecture.md`
1. **Modèle de données** : tables, colonnes (donnée ou formule), références entre tables, clés naturelles. Il devient `schema.py` ; rien n'est inventé hors de ce que les stories exigent.
2. **Matrice ACL (profil × table × droit)** : les profils viennent du PRD ; pour chaque table et chaque profil, les droits de lecture, de création, de modification et de suppression, colonnes sensibles comprises. Chaque case non évidente est justifiée ; elle devient `acl_rules.py` et la liste d'essai de `/grist-recette`.
3. **Inventaire des widgets** : un widget par écran, sa table source, les profils qui le voient, le profil de design system utilisé.
4. **Règles en double (formule Grist + JS)** : toute règle de gestion appliquée à la fois dans une formule de colonne et dans un widget, avec les deux emplacements et le test qui les garde alignés. Si la liste est vide, l'écrire.
5. **Plan de déploiement** : ordre des opérations, document cible, version de départ, ce qui exige un accord avant d'être appliqué.

## Déroulé
1. Poser à l'utilisateur, une question à la fois, ce que le PRD ne tranche pas (par exemple un profil sans droit défini sur une table).
2. Remplir les cinq sections.
3. Compléter `AGENTS.md` à la racine : conventions techniques et tableau des vérifications, avec les vraies commandes `focused`, `fast` et `full`, le contenu de la CI, et la ligne `isolation` (variable à surcharger par worktree si les tests touchent un document Grist ou un service, ou `none`). Seules des commandes qui existent et tournent y figurent.
4. Consigner chaque décision structurante en ADR dans `docs/decisions/NNN-<slug>.md` (`templates/adr.md`), avec les options écartées. Un ADR ne se modifie pas : un changement est un nouvel ADR qui remplace l'ancien.
5. Commiter `docs/architecture.md`, `AGENTS.md` et les ADR sur la branche d'intégration (`📝 DOCS: architecture`).

Terminer par : « Architecture prête, AGENTS.md à jour. Suite : /grist-design-system (une fois), puis /grist-research <story> »
