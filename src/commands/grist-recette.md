---
description: Essayer en réel les droits et les écrans du document Grist déployé, un profil après l'autre, et consigner la liste d'essai. À lancer après /grist-deploy et avant la mise en service ; pas pour les tests automatisés (/grist-review).
argument-hint: [story ou profil à essayer]
allowed-tools:
  - Read
  - Glob
  - Grep
  - Write
  - Bash
  - AskUserQuestion
---
# grist-recette — Essai en réel

Cible : $ARGUMENTS

Lire le skill `grist-recette`. Les tests locaux imitent Grist ; ici on vérifie le vrai document. Le MCP ne sert qu'à relire des données, jamais à modifier une structure ou une règle.

## Déroulé
1. Lire la matrice ACL de `docs/architecture.md` (profil × table × droit) : un profil, une adresse de compte d'essai, plus un inconnu.
2. Dresser dans `docs/recette.md` la liste « à vérifier en réel » : pour chaque profil, ce qu'il peut faire **et** ce qu'il ne peut pas faire (lecture, création, modification, suppression, colonnes masquées), avec une case par essai.
3. Pour chaque profil, ouvrir `<document>/p/<n>?aclAsUser_=<adresse>` dans le navigateur déjà connecté de l'utilisateur. Session expirée : lui demander de se reconnecter, jamais d'identifiant saisi par l'agent. `aclAsUser_` n'existe que dans le navigateur, pas dans l'API.
4. Cocher chaque essai avec le résultat observé ; un écart devient un constat : refus attendu accordé, ou droit attendu refusé.
5. Mesurer en même temps un chargement et une écriture avec un compte non propriétaire (skill `grist-perf`).
6. Données d'essai : ne supprimer que les lignes créées pour l'essai, par ids explicites ; une ligne inattendue se signale.

Terminer par le nombre d'essais, les écarts et le verdict. Écart sur un droit : /grist-acl ; sur un écran : /grist-widget ; lenteur : /grist-optimise.
