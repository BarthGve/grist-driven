---
description: Créer ou modifier un widget Grist selon le profil de design system du projet (dsfr : HTML d'un seul fichier ; ui-kit : entrée React construite par Vite). À lancer quand un ticket ajoute ou change un écran ; pas pour le dessin (/grist-design) ni pour la publication (/grist-deploy).
argument-hint: <nom du widget> <changement voulu>
allowed-tools:
  - Read
  - Glob
  - Grep
  - Write
  - Edit
  - Bash
---
# grist-widget — Un écran, selon le profil

Cible : $ARGUMENTS

Lire d'abord le skill `grist-widget`, puis la clé `design_system` de `.grist-driven.json` : absente ou illisible, arrêt et renvoi à `install.sh`. Un seul profil s'applique, on ne mélange pas. Le widget ne lit que ce que Grist lui livre ; aucune écriture de structure, et le MCP n'y a aucune part.

## Avant d'écrire
Lire `docs/designs/<story>.md` s'il existe et `docs/design-system.md` : jetons et composants viennent de là, rien d'inventé. Une règle métier vit en deux endroits, la colonne `conforme` du schéma et le cœur JS du widget : changer les deux avec un test de chaque côté.

## Profil `dsfr` (dossier `widgets/`)
1. Test `node:test` du cœur d'abord, puis le cœur (`core.js`) dans sa source, jamais dans les HTML.
2. Le HTML du widget : DSFR en version exacte, ordre des feuilles imposé, aucun `style=""`, `innerHTML` ni `alert()`.
3. Relancer l'inliner : `python -m grist_kit inliner`, puis `python -m grist_kit inliner --check`.

## Profil `ui-kit` (dossier `widgets_ui/`)
1. Test de la logique (cœur, hooks) d'abord, puis une entrée React par widget, composants de `@gouvfr-lasuite/ui-components` en priorité.
2. Construire (`npm run build`, Node ≥ 20) et vérifier la taille du bundle après gzip, sous la limite de l'API (voir skill `grist-perf`).

## Fin
Accessibilité (clavier, focus, thème sombre) essayée, tests verts. Le widget n'est pas en ligne tant que `/grist-deploy` n'est pas passé.
