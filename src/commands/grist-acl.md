---
description: Écrire ou modifier les règles d'accès d'un document Grist dans acl_rules.py, avec un test par règle (refus compris), puis les publier après lecture du plan. À lancer quand un ticket touche aux droits de lecture, création, modification ou suppression ; pas pour le schéma (/grist-schema).
argument-hint: <droit à ajouter ou à changer, profil concerné>
allowed-tools:
  - Read
  - Glob
  - Grep
  - Write
  - Edit
  - Bash
---
# grist-acl — Changer les droits

Changement demandé : $ARGUMENTS

Lire d'abord le skill `grist-acl` : `newRec`, absence de `rec.X.Y`, colonnes `-R`, étiquettes. Les règles ne s'écrivent jamais par le MCP (il ne touche pas à la structure) : seul `grist-kit` les applique.

## Déroulé
1. Partir de la matrice ACL de `docs/architecture.md` (profil × table × droit). Le droit voulu n'y est pas : l'y ajouter d'abord, c'est la référence de la recette.
2. Écrire les tests avant la règle, avec `grist_kit.testing.acl.permis(profil, table, droit)` : un test par règle, **y compris le cas refusé** (le profil sans droit doit échouer, et le test doit casser si la règle est cassée). Une règle de création se teste avec un inconnu qui s'ajoute.
3. Modifier `acl_rules.py` (données pures) : mémo commençant par `[<app>:<ressource>#<n>]`, colonne d'aide recopiée par formule plutôt que `rec.X.Y`.
4. Lancer `python -m grist_kit apply-acl --dry-run`, présenter le plan (règles ajoutées, retirées, décalées) et attendre l'accord ; puis appliquer sans `--dry-run`.
5. Le simulateur imite Grist sans le remplacer : consigner dans `docs/recette.md` les cas à essayer en réel (`/grist-recette`), surtout les verrouillages de champ avec une valeur renseignée.

Terminer par ce qui est appliqué et ce qui reste à vérifier en réel. Suite : /grist-recette.
