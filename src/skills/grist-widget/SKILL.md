---
name: grist-widget
description: Créer ou modifier un widget Grist personnalisé selon le profil dsfr (HTML d'un seul fichier) ou ui-kit (React, bundle gzip). Utiliser quand une story ajoute ou change un écran.
---
# Widgets Grist

Lire `design_system` dans `.grist-driven.json` : il fixe le profil. Un widget ne peut pas appeler l'API REST (pas de `fetch` vers le
document, même avec un jeton) : il lit ce que Grist lui livre. Pour alléger, recopier par formule sur une table plus petite ce
que l'écran affiche.

## Règle en deux endroits

Toute règle métier vit dans la colonne `conforme` du schéma **et** dans le cœur JS du widget (pour afficher l'erreur avant l'envoi).
On la change aux deux, avec un test de chaque côté. Le cœur se modifie dans sa source, jamais dans les HTML : on relance l'inliner
(`python -m grist_kit inliner`, vérification avec `--check`).

## Données livrées au widget

- `grist.onRecords` ne livre pas les mêmes valeurs que `fetchTable` : une référence arrive en `{ tableId, rowId }`, une date-heure en
  objet `Date` (millisecondes). Normaliser avant d'appeler le cœur.
- Une cellule masquée par une règle `-R` arrive en objet, pas en chaîne vide (voir `grist-acl`).
- Un seul chargement des données au démarrage ; tout tableau paginé par 50 lignes (voir `grist-perf`).

## Profil `dsfr` (`widgets/`)

Un HTML par widget, DSFR en version exacte (jamais `@1.14`), `core.js` inliné entre marqueurs, tests `node:test` du cœur.
- Ordre des feuilles strict : script de thème `fr-scheme` avant toute CSS, puis `core`, `utility`, `utility/icons`, `scheme`, puis les
  composants par ordre alphabétique. Pas de pied de page.
- **Interdits** : `style="…"`, `!important`, `innerHTML`, `alert()`/`confirm()`/`prompt()`, scripts externes autres que
  `grist-plugin-api.js`. Notifications par `fr-alert`, confirmation par `<dialog>`.
- Classes utilitaires DSFR d'abord ; CSS propre seulement avec les jetons de décision (`--text-*`, `--background-*`, `--border-*`),
  jamais de couleur en dur.
- Accessibilité (RGAA) : `aria-label` sur les champs dynamiques, icônes décoratives `aria-hidden="true"`, clavier, focus rendu après
  chaque reconstruction du DOM, thème sombre essayé. Vues basculées par onglets DSFR, pas par un groupe de boutons.
- Un tableau d'éléments dans un tableau d'éléments s'affiche en `[object HTMLElement]` : étaler (`...liste.map(…)`).
- `el.hidden = true` ne cache rien si une règle de classe fixe `display` : ajouter `.classe[hidden] { display: none; }`.
- Un menu ou une liste `position: fixed` ouvert depuis un tiroir animé (`transform`) est décalé et rogné : le poser au niveau de la page.

## Profil `ui-kit` (`widgets_ui/`)

Application React/TypeScript construite par Vite (`vite-plugin-singlefile`), une entrée par widget, sortie `dist/<entrée>.html`.
- Composants de `@gouvfr-lasuite/ui-components` d'abord ; pas de style en dur hors des jetons du kit.
- Le bundle dépasse la limite de l'API (413 vers 1 Mo) : le déployeur le dépose compressé (gzip + base64, décompressé par le
  navigateur). Garder le bundle sous la limite après gzip (voir `grist-perf`).
- Les tests portent sur la logique (cœur, hooks), pas sur le balisage.

## Après modification

Version avant déploiement, déploiement et `--check` : voir `grist-deploy`.
