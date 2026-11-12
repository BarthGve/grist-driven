---
name: grist-recette
description: Essayer en réel les droits et les écrans d'un document Grist avec un compte par profil. Utiliser après un déploiement et avant la mise en service.
---
# Recette en réel

Les tests locaux imitent Grist, ils ne le remplacent pas. Une règle jamais essayée avec un compte non propriétaire n'est pas vérifiée.

## Méthode

1. Partir de la matrice ACL de `docs/architecture.md` (profil × table × droit). Un compte d'essai par profil, plus un inconnu et un archivé
   s'il y en a un.
2. Ouvrir le document connecté, puis l'URL `<document>/p/<n>?aclAsUser_=<adresse>` : le navigateur joue ce profil.
   `aclAsUser_` ne marche qu'avec le navigateur connecté ; l'API REST n'a pas d'équivalent.
3. Pour chaque profil, essayer ce qu'il peut faire **et** ce qu'il ne peut pas faire : lecture, création, modification, suppression,
   colonnes masquées. Noter le résultat dans une liste « à vérifier en réel » (`docs/recette.md`).
4. Une session de navigateur expirée ne se rétablit pas par un identifiant saisi par l'agent : demander à l'utilisateur de se connecter.

## À savoir

- Un refus d'écriture ne dit pas quelle règle a refusé : vérifier d'abord que la valeur écrite est bonne.
- Éditer une cellule Choice dans l'interface : l'éditeur s'ouvre avec la valeur actuelle, faire `cmd+a` avant de taper.
- Une création `Ref` ne se forge pas à la main depuis l'interface : l'essayer par le widget.
- Les règles qui verrouillent des champs s'essaient avec une valeur renseignée.
- Données d'essai : relire les lignes (lecture seule), ne supprimer que celles créées pour l'essai, par ids explicites. Une ligne inattendue
  se signale à l'utilisateur, on ne la supprime pas sans son accord.
- `NOW()` n'est recalculé qu'au chargement ou à la modification de la ligne : un indicateur de retard peut être périmé jusqu'au rechargement.
- Mesurer en même temps (voir `grist-perf`) : un chargement et une écriture, avec un compte non propriétaire.
