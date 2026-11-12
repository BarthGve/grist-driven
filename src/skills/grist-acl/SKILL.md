---
name: grist-acl
description: Écrire ou modifier les règles d'accès (ACL) d'un document Grist avec un test par règle, refus compris. Utiliser quand une story touche aux droits de lecture, de création, de modification ou de suppression.
---
# Règles d'accès Grist

Les règles vivent dans `acl_rules.py` (données pures). Appliquer : `python -m grist_kit apply-acl --dry-run`, relire le plan,
puis appliquer sur accord. Un droit se confirme en réel (voir `grist-recette`), jamais seulement en test.

## Écrire une règle

- **Pas de `rec.X.Y`** : la notation pointée sur une référence n'existe pas. Recopier par formule les adresses sur chaque ligne
  protégée (colonne d'aide), puis tester `user.Email in rec.<colonne>`.
- **Étiquette** : chaque règle commence son mémo par `[<app>:<ressource>#<n>]`. Le script suit les règles par cette étiquette ;
  insérer une règle décale les numéros suivants et le script réécrit formule, droits et mémo des règles décalées.
- **Colonnes `-R`** : une règle `-R` masque la colonne aux lecteurs, mais les règles la lisent côté serveur. Un widget reçoit
  alors un objet (truthy, `"CENSORED"` une fois sérialisé), pas une chaîne vide : se reconnaître par une colonne d'identité non vide,
  jamais par un test de vérité.
- Une règle `+R` ne fixe que la lecture ; les autres droits tombent sur les règles suivantes.
- Ouvrir une colonne en lecture à tous révèle l'existence des lignes (leurs ids).
- Le droit de structure contourne les règles de données : réservé au propriétaire.
- Ordre d'application : Grist refuse l'état intermédiaire où le repli précède une règle encore présente ; `apply-acl` retire les
  règles obsolètes avant les mises à jour. Ne pas contourner.

## Pièges de l'évaluation

- **`newRec` compte la ligne en cours d'insertion** : une règle de création qui teste l'appartenance via `newRec.<liste>` accorde le
  droit à celui qui s'ajoute lui-même. Tester chaque règle de création avec un inconnu qui s'ajoute.
- **Un lot d'actions est jugé sur l'état d'avant le lot**, et `newRec` n'existe pas à la suppression. Un lot peut retirer tous les
  responsables d'un groupe (le widget doit le refuser) ; supprimer un parent qui porte des enfants se fait en deux requêtes.
- **Comparer deux dates `rec`/`newRec`** (type `DateTime`) est faux dans Grist dès qu'elles sont renseignées. Comparer des colonnes de
  formule entières (secondes) ou des ids, jamais des dates ni des références.
- Les règles d'accès ne s'appliquent pas à la création d'une ligne par la clé d'un formulaire public.

## Tester

**Un test par règle, y compris le refus** : le profil qui n'a pas le droit doit échouer, et le test doit échouer si on casse la règle
(mutation). Utiliser `grist_kit.testing.acl.permis(profil, table, droit)`. Ce simulateur imite Grist, il ne le remplace pas : toute règle
de verrouillage de champ s'essaie en réel avec une valeur renseignée, pas seulement vide.
