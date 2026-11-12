---
description: Optimiser la performance d'un document Grist (widgets, formules, ACL, appels d'API, bundle ui-kit) en mesurant avant et après. À lancer quand un chargement ou une écriture est lent, ou avant de valider une story à gros volume ; pas sans mesure.
argument-hint: <widget, table ou écran lent>
allowed-tools:
  - Read
  - Glob
  - Grep
  - Write
  - Edit
  - Bash
---
# grist-optimise — Mesurer, corriger, remesurer

Cible : $ARGUMENTS

Lire le skill `grist-perf`, dont la checklist guide chaque correction. Le MCP peut lire les données pour mesurer ; il ne change jamais la structure.

## Règle
Aucune modification sans mesure avant, aucune livraison sans mesure après. Un gain affirmé sans chiffre n'existe pas.

## Déroulé
1. **Mesure avant.** Volumétrie réelle, sinon jeu de données synthétique (par exemple 2 000 lignes) ; compte non propriétaire, car il lit moins. Mesurer séparément : temps de chargement de chaque widget, temps d'interaction (tri, recherche, écriture d'une ligne) et, en profil `ui-kit`, taille du bundle après gzip.
2. **Cause.** Appliquer la checklist du skill `grist-perf` à ce qui est lent : un seul chargement, pagination à 50 lignes, `Intl` hors des boucles, index `Map`, `lookupRecords` en colonne, ACL coûteuses, écritures groupées par `/apply`. Un constat par cause, pas de correction à l'aveugle.
3. **Corriger** une cause à la fois, test d'abord.
4. **Mesure après**, dans les mêmes conditions. Pas de gain net : annuler le changement.
5. **Garde-fou.** Ajouter ou resserrer une borne large dans les tests de performance (elle repère une régression, elle ne chronomètre pas).
6. **Consigner** dans `docs/revue-performance.md` : constat, cause, correction, mesure avant, mesure après.

Une formule ou une règle changée passe par /grist-schema ou /grist-acl, puis /grist-deploy. Terminer par le tableau avant/après.
