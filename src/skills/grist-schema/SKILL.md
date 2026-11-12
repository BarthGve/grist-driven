---
name: grist-schema
description: Modifier le schéma d'un document Grist (tables, colonnes, formules) sans casser les données ni les droits. Utiliser quand une story ajoute, renomme ou convertit une table ou une colonne.
---
# Schéma Grist

Le schéma vit dans `schema.py` (données pures, aucun appel réseau). On le change là, puis on l'applique avec
`python -m grist_kit apply-schema --dry-run`, relecture du plan, puis sans `--dry-run` sur accord. Jamais par le MCP.

## Pièges, dans l'ordre où ils mordent

1. **Colonne de données ajoutée à une table existante** : Grist la crée avec `isFormula` vrai. La première écriture d'un
   non-propriétaire est alors refusée comme un changement de structure. Après tout ajout, relire `isFormula` et le repasser à faux.
2. **Colonne qui passe de formule à donnée** : `apply-schema` ne la convertit pas, elle ignore les écritures. Une seule fois,
   action `ModifyColumn` avec `isFormula: false`, `formula: ""` et le type voulu (table vide, ou valeurs recopiées avant).
3. **Formule ou choix modifié sur une colonne existante** : `apply-schema` n'y touche pas. Lancer ensuite `maj-formules --dry-run` ;
   les `divergentes` se règlent à la main, on n'écrase jamais une formule corrigée dans Grist sans l'avoir lue.
4. **Renommage** : `PATCH …/columns` qui change le libellé renomme aussi le `colId`. Pour ne changer que le libellé, repasser
   le `colId` actuel dans le corps.
5. **Table et colonne de formule qui la lit, créées dans la même passe** : la colonne peut rester vide (évaluée avant que la
   table existe). Créer la table, appliquer, ajouter les colonnes qui la lisent à la passe suivante.
6. **Ids de lignes réutilisés** quand une table est vidée : une ligne orpheline se rattache au prochain enregistrement qui reprend
   l'id. Pas de ligne orpheline ; créer les enfants avec l'id renvoyé par l'API, jamais deviné.
7. **Référence vers une ligne supprimée** : elle devient vide (0) et les enfants deviennent non conformes. Supprimer enfants d'abord.
8. **Formules** : pas de `pytz` ni de `dateutil` ; une `ChoiceList` revient de l'API sous la forme `['L', 'a', 'b']`.
   Pour un texte libre, préférer un `Text` séparé par des virgules.
9. **Pas d'unicité native** : une colonne de formule détecte le doublon, une règle d'accès le refuse. Deux envois simultanés restent possibles.

## Règle métier

Une règle vit dans une colonne `conforme` (formule) **et** dans le cœur JS du widget : voir `grist-widget`. Toute formule ajoutée
ou changée a son test sur le moteur de formules en mémoire (`grist_kit.testing.formules`), y compris le cas qui échoue.

## Performance

Une formule qui relit toute une famille de lignes coûte au carré. Voir `grist-perf` avant d'écrire un `lookupRecords`.
