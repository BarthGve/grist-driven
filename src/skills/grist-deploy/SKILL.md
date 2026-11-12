---
name: grist-deploy
description: Déployer un projet Grist dans le bon ordre (schéma, formules, ACL, amorçage, pages, widgets) en gérant le pare-feu et la version. Utiliser avant toute mise en service ou republication de widgets.
---
# Déploiement Grist

Toutes les commandes de `grist-kit` sont idempotentes et acceptent `--dry-run` et `--doc <id>`. **Toujours `--dry-run` d'abord**, relire,
puis appliquer. Le déploiement se fait sur le document réel, jamais depuis le MCP.

## Ordre (il compte)

1. `apply-schema` : crée tables et colonnes.
2. `maj-formules` : aligne formules et choix des colonnes existantes. En `--dry-run`, la liste des `divergentes` se traite à la main ;
   toute ligne inattendue = arrêt et analyse.
3. `apply-acl`.
4. `amorcer` : ancres de pages, réglages, valeurs d'exemple (une fois).
5. `creer-page` pour chaque widget neuf (le déployeur refuse une section absente de `widgets.json`).
6. `deployer <widget>`, puis `deployer <widget> --check`.

Un widget qui lit une table absente affiche « Chargement impossible » : les étapes 1 à 4 passent avant le 6.
Après un changement du cœur inliné, redéployer chaque widget dont la copie a changé.

## Version avant déploiement

Demander à l'utilisateur patch, minor ou major, ajouter l'entrée en tête du journal des versions, relancer l'inliner (il régénère
`CHANGELOG.md`). Notes rédigées pour l'utilisateur final, sans jargon.

## Pare-feu devant l'API (403)

- Il rejette en 403 les corps qui contiennent des motifs de piratage web, **même dans une donnée** (un cas de test qui stocke un
  `<script>`) et certaines formules (`… or 0) >= 0` refusé, `not (… < 0)` accepté). Le `--dry-run` ne le voit pas : le refus n'apparaît
  qu'à l'écriture. Reformuler la formule.
- Après une rafale de refus, il peut tout refuser un moment, même des écritures inoffensives. Ne pas insister : attendre, faire une écriture
  neutre, reprendre par petits lots. Ne jamais boucler sur les refus.
- Un corps entièrement échappé en `\uXXXX` est refusé presque partout : dernier recours, pour une ligne isolée. Le déploiement des
  widgets en a besoin : c'est le déployeur qui s'en charge.
- Une ligne définitivement refusée se saisit à la main dans l'interface de Grist.
- 413 : bundle trop gros, voir `grist-widget` (profil `ui-kit`) et `grist-perf`.

## Après le déploiement

Pages natives des tables : `python -m grist_kit pages` retire celles qui ne montrent qu'une table brute (à relancer après toute création
de page). Puis `grist-recette`.
