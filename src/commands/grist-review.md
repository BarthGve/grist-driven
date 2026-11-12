---
description: Faire relire un ticket enfant par un sous-agent au contexte neuf et ajouter un tour de relecture, la porte avant la livraison. À lancer après /grist-execute ; pas pour relire les stories (/grist-stories-review) ni pour corriger du code.
argument-hint: <identifiant de la story> <identifiant du ticket>
allowed-tools:
  - Read
  - Grep
  - Agent
  - Write
  - Bash
---
# grist-review — Relecture et porte avant livraison

Cible : $ARGUMENTS

## Règle de cette commande
Le jugement revient au sous-agent `reviewer` (contexte neuf) : tu as probablement produit le code, donc tu ne le juges pas. Tu ne modifies aucun code ; ta seule écriture est `docs/reviews/<story>/<ticket>.md`. Un constat critique ou majeur ne se lève pas par décision de ta part.

## Déroulé
1. Retrouver `<story>` et `<ticket>`. Le ticket doit être `in progress` ou `review` sur le tableau (`status-get <story>/<ticket>` de `.grist/lib/grist-board.sh`) ; sinon arrêt.
2. Retrouver `.worktrees/<story>/<ticket>`, vérifier la branche `feature/<story>/<ticket>`, utiliser ce chemin absolu. Absent : arrêt.
3. Appeler l'outil Agent avec :
   - subagent_type: reviewer
   - dossier de travail : le worktree du ticket
   - prompt : relire le ticket `<ticket>` de la story `<story>` (diff `git diff next...feature/<story>/<ticket>`), remplir `templates/review-checklist.md` ; vérifier la conformité au design system si le ticket a un écran, la structure Grist posée par les scripts de `grist-kit` et non par le MCP, et un test par règle d'accès, refus compris.
4. **Rapport.** Ajouter le tour du relecteur à `docs/reviews/<story>/<ticket>.md`, après les tours précédents, sans jamais en réécrire un. Le fichier se termine par les deux lignes exactes `Max severity: <critical|major|minor|none>` et `Ship allowed: yes` ou `Ship allowed: no` ; les portes ne lisent que le dernier verdict (la ligne française du gabarit peut les accompagner, jamais les remplacer).
5. **Porte.**
   - critique ou majeur : « Livraison bloquée. Corriger par /grist-execute <story> <ticket> (mode correction), puis relancer /grist-review. » Le ticket reste `in progress`.
   - sinon : passer le ticket en `review` (`status-set <story>/<ticket> review`), puis : « Relecture passée. Suite : /grist-ship <story> <ticket> »
