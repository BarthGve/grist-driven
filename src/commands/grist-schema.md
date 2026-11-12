---
description: Modifier le schéma d'un document Grist (tables, colonnes, formules) dans schema.py, puis le publier après lecture du plan. À lancer quand un ticket ajoute, renomme ou convertit une table ou une colonne ; pas pour les droits (/grist-acl) ni pour la mise en service (/grist-deploy).
argument-hint: <changement de schéma voulu>
allowed-tools:
  - Read
  - Glob
  - Grep
  - Write
  - Edit
  - Bash
---
# grist-schema — Changer le schéma

Changement demandé : $ARGUMENTS

Lire d'abord le skill `grist-schema` : ses pièges (`isFormula`, `colId`, ids réutilisés) décident de la façon de faire. La structure ne s'écrit jamais par le MCP (il sert à lire et à manipuler les données) : seuls les scripts de `grist-kit` la touchent.

## Déroulé
1. Relire `docs/architecture.md` (modèle de données) et `schema.py`. Le changement n'y figure pas : le dire, et proposer de mettre l'architecture à jour avant d'aller plus loin.
2. Écrire le test en premier, sur le moteur de formules en mémoire (`grist_kit.testing.formules`), y compris le cas qui échoue, puis modifier `schema.py` (données pures, aucun appel réseau).
3. Lancer `python -m grist_kit apply-schema --dry-run` et présenter le plan en clair : tables et colonnes créées, ce qui reste intact.
4. Attendre l'accord de l'utilisateur, puis relancer sans `--dry-run`.
5. Ensuite, selon ce qui a changé :
   - une colonne de données ajoutée à une table existante : relire `isFormula` et le repasser à faux ;
   - une formule ou un choix modifié sur une colonne qui existe déjà : `apply-schema` n'y touche pas, lancer `python -m grist_kit maj-formules --dry-run` après un changement de formule ; les `divergentes` se règlent à la main, on n'écrase jamais une formule corrigée dans Grist sans l'avoir lue ;
   - une règle métier touchée : la reporter dans le cœur du widget (`/grist-widget`).
6. Droits concernés par la nouvelle colonne : `/grist-acl`. Performance d'une formule sur gros volume : skill `grist-perf`.

Terminer en nommant ce qui a été appliqué et ce qui reste à la main. Suite : /grist-acl si les droits changent, sinon /grist-deploy.
