---
name: grist-stories-review
description: Relire un découpage en stories contre le périmètre du PRD (couverture, hors-périmètre, couches techniques, critères, ordre). Utiliser dans le sous-agent stories-reviewer, avant de lancer la recherche d'une story.
---
# Relecture des stories

Un défaut dans `docs/stories.md` coûte une ligne à corriger maintenant et contamine ensuite recherche, plan, code et livraison de chaque
story qui en découle. On confronte les stories à ce que le PRD a promis. On ne réécrit jamais les stories : on signale, l'humain corrige.

## Contrôles, dans l'ordre

1. **Couverture** : parcourir le tableau du périmètre du PRD, pas les stories (seul moyen de voir ce qui manque). Chaque fonction doit
   être livrée par au moins une story.
2. **Hors-périmètre** : rien de ce que le PRD exclut ne revient en story.
3. **Couches déguisées** : « créer les tables », « poser les règles d'accès » seuls ne sont pas des stories. Schéma, règles et widget
   se livrent dans la story qui en a besoin.
4. **Profils et droits** : chaque profil du PRD apparaît dans au moins une story ; chaque story qui touche une donnée a un critère de refus
   pour un profil sans droit.
5. **Volumétrie** : une story à gros volume (tableaux, synthèses) nomme la volumétrie visée dans ses notes.
6. **Critères testables** : chacun peut devenir un test.
7. **Ordre des dépendances** : pas de cycle, pas de renvoi vers une story placée plus loin.
8. **Complexité** : un 5 est déjà découpé ; un 4 énonce son risque.
9. **Ids** : `s<numéro>-<slug>`, uniques, stables (ils nomment fichiers et branches).
10. **Chevauchement** : deux stories sur la même tranche, ou une story qui mélange deux valeurs sans rapport.

## Fonctionnalité ajoutée à un produit déjà livré (`/grist-feature`)

On juge aussi le découpage contre ce qui tourne déjà.
- **Doublon de livré** : la fonctionnalité refait une tranche déjà couverte par une story livrée. Lire le statut de chaque story du tableau
  avant de juger. Critique.
- **Dépendance non livrée** : elle suppose une story pas encore livrée. Acceptable si dite ; sinon majeur.
- **Contradiction avec la production** : elle change un comportement dont les utilisateurs dépendent. Voulu, c'est légitime ; non dit, c'est
  critique. Cela vaut aussi pour un changement de schéma ou de droit sur un document qui contient déjà des données.
- Une fonction peut sortir du hors-périmètre si l'amendement du PRD l'explique ; sinon critique.

## Sévérité

- **critique** : produit incomplet ou hors périmètre (fonction non couverte, fuite du hors-périmètre, ordre impossible).
- **majeur** : défaut réel dans une story (couche technique, critère non testable, 5 non découpé, id dupliqué, profil sans refus, chevauchement).
- **mineur** : formulation, style d'id, note manquante.

## Hors sujet

Ce n'est pas une revue d'implémentation : le « comment » appartient à `/grist-research` et `/grist-plan`.
