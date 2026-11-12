---
description: Écrire la page produit d'une story, destinée aux utilisateurs et au wiki (sans publier). À lancer après /grist-plan, avant la livraison du premier ticket ; la publication du wiki relève de /grist-release.
argument-hint: <identifiant ou nom de la story>
allowed-tools:
  - Read
  - Glob
  - Grep
  - Write
  - Bash
---
# grist-docs — Page produit d'une story

Story visée : $ARGUMENTS

Retrouver l'identifiant dans `docs/stories.md` ; aucune correspondance unique : lister et s'arrêter.

## Cadre
- Travailler dans `.worktrees/<story>`, branche `feature/<story>`. Absent : arrêt et renvoi à `/grist-research <story>`. Pas de changement de branche.
- `docs/plans/<story>.md` doit porter `validated: yes`, sinon arrêt : « Plan non validé : lancer /grist-plan <story>. »
- Aucune porte « ticket prêt » : les tickets peuvent encore être en `backlog`.

## À écrire
`docs/product/<story>.md` d'après `templates/product-doc.md`, en s'aidant de la story (but, critères devenus règles visibles et hors périmètre), de `docs/designs/<story>.md` pour le parcours et du plan pour les limites. Écrire pour les utilisateurs du produit, profil par profil quand les droits diffèrent : ni recherche, ni tâches de plan, ni jargon de relecture.

Les documents de la story (recherche, design, plan, page produit) se commitent sur `feature/<story>` et rejoignent `next` avec la PR de la story.

## Hors de cette commande
La publication dans le wiki : elle se fait à la livraison, par `/grist-release`.

Terminer par : « Page produit prête dans docs/product/<story>.md, exigée avant le premier /grist-ship de la story. Suite : passer un ticket enfant en ready, puis /grist-execute <story> <ticket>. »
