---
description: Consigner le design system retenu (dsfr ou ui-kit) dans docs/design-system.md : jetons, composants, règles. Enregistre, n'invente pas. À lancer une fois, après /grist-architect ; pas pour l'écran d'une story (/grist-design).
argument-hint: (facultatif) source de la direction visuelle
allowed-tools:
  - Read
  - Glob
  - Grep
  - Write
  - Bash
  - AskUserQuestion
---
# grist-design-system — Référence visuelle du produit

Cette commande consigne, elle ne dessine pas. Interdit : inventer une identité visuelle, ou produire un design système générique (couleurs au hasard, composants imaginaires). Sans source ni système existant, s'arrêter et demander la source (jetons, maquettes, description).

## Déroulé
1. **Choix du profil.** Lire `design_system` dans `.grist-driven.json`. Absent ou illisible : arrêt, renvoi à `install.sh`. Le gabarit `templates/design-system.md` a deux variantes ; on ne garde que celle du profil retenu, la variante `dsfr` ou la variante `ui-kit`, plus la partie commune.
2. **Sources.** Ce que le gabarit du projet fournit déjà (feuilles de style DSFR et leur version exacte, ou composants de `@gouvfr-lasuite/ui-components` et thème), inventorié avec le skill `grist-codebase-analysis`, puis la direction visuelle de l'utilisateur : $ARGUMENTS, sinon la lui demander.
3. **Structurer** : version, jetons (couleurs, typographie, espacements), composants disponibles avec leur usage, règles propres au profil (feuilles et script pour `dsfr` ; build et chargement pour `ui-kit`), motifs d'interface imposés (formulaires, états, retours), à faire et à éviter.
4. **Écrire** `docs/design-system.md` et le commiter sur la branche d'intégration (`📝 DOCS: design system`). C'est l'unique référence visuelle, lue par `/grist-design` à chaque story.

Terminer par : « Design system consigné dans docs/design-system.md. Les écrans de story s'y appuieront via /grist-design <story>. »
