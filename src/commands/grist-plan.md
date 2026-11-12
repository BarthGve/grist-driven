---
description: Découper une story en tickets enfants avec tâches, taille et estimation en jours-personne, puis faire valider le plan. À lancer après /grist-research (et /grist-design si la story a un écran) ; pas pour écrire du code (/grist-execute).
argument-hint: <identifiant ou nom de la story>
allowed-tools:
  - Read
  - Glob
  - Grep
  - Write
  - AskUserQuestion
  - Bash
---
# grist-plan — Tickets d'une story

Story visée : $ARGUMENTS

Retrouver l'identifiant dans `docs/stories.md`, puis le worktree `.worktrees/<story>` : il doit être sur `feature/<story>` exactement, et tout se lit et s'écrit là. Absent, mauvaise branche, HEAD détaché ou dossier de base : arrêt et renvoi à `/grist-research <story>`. Aucune branche n'est créée ni changée ici.

Lire : la story, `docs/research/<story>.md` (sans elle, conseiller `/grist-research` et ne continuer qu'avec l'accord de l'utilisateur : le plan reposerait sur des documents peut-être périmés), `docs/design-system.md` et `docs/designs/<story>.md` si présents, `docs/architecture.md`, `AGENTS.md`. Gabarit : `templates/plan.md`. Une story à écran suit l'écran de `docs/designs/<story>.md` et n'invente aucun composant.

## Tickets
Chaque ticket `t<numéro>-<slug>` est un cycle complet exécuter, relire, livrer : une tranche de schéma, un jeu de règles d'accès, un widget. Ce n'est ni une couche technique ni une case à cocher. Chacun porte obligatoirement :
- `size:` parmi XS, S, M, L, XL ;
- `estimate:` en jours-personne, par pas de 0,5 ;
- ce qu'il touche (schéma, ACL, widget, formules) : c'est ce qui décide des skills et du déploiement.

## Déroulé
1. Ordonner les tickets avec leurs dépendances, leurs tâches, leurs interdits d'exécution, leurs fichiers probables et leur stratégie de test. Une règle de gestion, un droit ou un contrat de données nomme le test qui peut échouer ; un droit nomme aussi le cas refusé. Une tâche de pure présentation peut nommer un contrôle visuel plus lint et typage.
2. Story notée 5, ou plan de plus d'une dizaine de tickets : la story est trop grosse, proposer de la découper au lieu de gonfler le plan.
3. Un choix structurant imposé par le plan devient un ADR (`templates/adr.md`).
4. Écrire `docs/plans/<story>.md` avec l'en-tête `validated: no` (c'est la ligne que lit la porte avant tout code) et un total : somme des estimations, répartition des tailles.
5. **Validation** (AskUserQuestion : valider, ou relire d'abord). Le résumé liste chaque ticket avec taille et estimation, plus le total ; sans les deux champs sur chaque ticket, pas de validation.
   - Valider : remplacer par `validated: yes`, puis créer une issue **enfant** au statut `backlog` (jamais `ready`) par ticket : `bash .grist/lib/grist-board.sh issue-create-ticket <story> <ticket> "<titre> (TAILLE, Nj)" <fichier-corps>`. Titre avec taille et estimation ; corps avec les lignes `Size:` et `Estimate:` et le périmètre. Mettre à jour l'issue parent avec le total, au mieux, par `gh issue edit`.
   - Pas d'appel à `require-ready` ici.

Si le fichier existe déjà, passer directement à la validation. Cette commande ne produit ni code, ni migration, ni déploiement.

Terminer par : « Plan validé, tickets en backlog. Suite : /grist-docs <story>, puis passer un ticket en ready et /grist-execute <story> <ticket> », ou : « Plan en attente de validation : relancer /grist-plan <story>. »
