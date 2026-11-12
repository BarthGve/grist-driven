---
description: Explorer le contexte réel d'une story avant de la planifier — classeur, code, règles, pièges — et créer son worktree de cadrage. À lancer en premier pour chaque story ; pas pour l'architecture du produit (/grist-architect).
argument-hint: <identifiant ou nom de la story>
allowed-tools:
  - Read
  - Glob
  - Grep
  - Write
  - Bash
  - Agent
---
# grist-research — Contexte vérifié d'une story

Story visée : $ARGUMENTS

Retrouver l'identifiant `s<numéro>-<slug>` dans `docs/stories.md`. Aucune correspondance unique : lister les stories et s'arrêter.

## Espace de travail (on s'arrête au moindre doute)
Appeler le sous-agent `worktree-manager` avec l'identifiant et le dossier de base du dépôt. Il crée `feature/<story>` depuis `next` dans `.worktrees/<story>` (cadrage, documents seulement). Ne continuer qu'une fois reçus le chemin absolu, la branche exacte et un état propre. Toute lecture et toute écriture de la story se fait dans ce worktree ; jamais de branche créée ou changée dans le dossier de base.

Si `docs/reviews/stories.md` manque ou dit `Stories prêtes : non`, le signaler : le découpage n'a pas passé `/grist-stories-review`. Continuer seulement si l'utilisateur confirme.

## Lire
`docs/stories.md` (la story visée), `docs/architecture.md`, `AGENTS.md`. Gabarit de sortie : `templates/research.md`. Appliquer le skill `grist-codebase-analysis` sur le périmètre de la story : l'état actuel du dépôt et du classeur, pas ce que les documents affirment, car ils ont pu vieillir depuis les stories précédentes.

## Déroulé
1. Isoler la story et ses critères d'acceptation.
2. Repérer les fichiers vraiment concernés (`schema.py`, `acl_rules.py`, widgets, tests) et leur état.
3. **Vérifier les présupposés**, pas seulement l'existence des noms : une table, une colonne, une règle ou une fonction que la story évoque se contrôle dans le code, avec son nom exact et son comportement sur le cas de la story. Une prémisse fausse se met en tête du rapport : c'est la découverte la plus précieuse de cette commande, et elle se corrige dans la story, pas au moment du plan.
4. Chercher les pièges propres à Grist : droits qui changent ce qu'un profil voit, formules existantes à garder alignées avec un widget, volumétrie réelle des tables touchées. Lire la matrice ACL de l'architecture pour chaque profil concerné.
5. Noter dans « Questions ouvertes » ce qu'on n'a pas pu trancher : un inconnu avoué vaut mieux qu'une supposition plausible.
6. Réévaluer la complexité (1 à 5) maintenant qu'on a lu le code et la comparer à `docs/stories.md`. Un 5 s'accompagne d'une proposition de découpe.
7. Écrire `docs/research/<story>.md`.

Pas de code, pas de plan : cette commande ne produit que du contexte vérifié. Aucune porte « ticket prêt » ici, les tickets n'existent peut-être pas encore.

Terminer par : « Recherche prête dans docs/research/<story>.md. Suite : /grist-design <story> (story avec écran) ou /grist-plan <story> »
