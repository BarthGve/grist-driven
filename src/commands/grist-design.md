---
description: Dessiner l'écran d'une story à partir du design system consigné — par l'agent, par le canevas /design de Claude Code, ou par un brief pour un outil externe. À lancer après /grist-research pour une story avec écran ; pas pour le système global (/grist-design-system) ni pour une story sans interface.
argument-hint: <identifiant ou nom de la story> [--agent | --canvas | --brief]
allowed-tools:
  - Read
  - Glob
  - Grep
  - Write
  - AskUserQuestion
  - Bash
---
# grist-design — Écran d'une story

Story visée : $ARGUMENTS

Retrouver l'identifiant, puis le worktree `.worktrees/<story>`. Avant toute lecture ou écriture, vérifier qu'il est bien sur `feature/<story>` et travailler avec ce chemin absolu. Worktree absent, mauvaise branche, HEAD détaché ou dossier de base : arrêt et renvoi à `/grist-research <story>`. On ne change jamais de branche ici.

## Interdits
- Concevoir sans design system consigné.
- Inventer un composant, un jeton, une couleur ou un espacement hors de ce système.
- Dessiner un écran que la story ne demande pas.

## Déroulé
1. **Prérequis.** `docs/design-system.md` doit exister et n'être pas vide. Sinon : « Pas de design system : lancer /grist-design-system puis relancer /grist-design », et aucun dessin. Sinon le charger : ses jetons et composants (ceux du profil `dsfr` ou `ui-kit`) sont la seule source visuelle.
2. **Qui produit ?** Si $ARGUMENTS ne le dit pas, demander : l'agent, tout de suite ; le canevas `/design` de Claude Code, où l'agent prépare les planches et où l'utilisateur les affine visuellement ; ou un brief à confier à un outil externe.
3. **Lire** la story, ses critères, `docs/research/<story>.md` s'il existe (points d'ancrage), et les profils concernés dans la matrice ACL : un écran change selon le profil qui le voit.
4. **Produire**, selon la voie :
   - *agent* : `docs/designs/<story>.md` (écrans, états vide, chargement, erreur, refus d'accès ; profils ; composants employés ; écarts du design system) et `docs/designs/<story>.html`, maquette statique à basse fidélité n'utilisant que les jetons du système ;
   - *canevas* : lancer `/design`, puis déposer les planches en `docs/designs/<story>.dc.html` avec le même `.md` ; l'Artifact publié n'est pas le livrable ;
   - *brief* : remplir `templates/design-brief.md` en `docs/designs/<story>-brief.md`, puis attendre que l'utilisateur rapporte les écrans.
5. **Écarts.** Tout besoin que le design system ne couvre pas va dans « Écarts du design system » ; on ne l'invente pas.

La maquette HTML est une référence, pas du code : en exécution, l'écran se construit avec les composants du profil, jamais en collant la maquette. Défini suffisamment pour débloquer le plan, pas au pixel près. Aucune porte « ticket prêt » ici.

Terminer par : « Design prêt (docs/designs/<story>.md + .html). Suite : /grist-plan <story> »
