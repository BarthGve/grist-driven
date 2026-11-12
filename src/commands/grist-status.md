---
description: Montrer où en est le projet — cadrage, colonnes du tableau, jours-personne restants, prochaine commande. À lancer pour savoir où l'on en est ; pas pour la carte générale des phases (/grist-help).
argument-hint: (aucun)
allowed-tools:
  - Read
  - Glob
  - Grep
  - Bash
---
# grist-status — L'état du projet, déduit et non deviné

Tout se déduit des fichiers et du tableau. Bash ne sert qu'à des lectures git et à **un seul** appel `bash .grist/lib/grist-board.sh status-all` (une ligne `<clé>` tabulation `<statut>` par issue ; l'ignorer, colonnes « n/d », si `.grist/config.json` manque). Jamais `status-get` story par story : chaque appel relit tout le tableau.

1. **Cadrage.** `docs/prd.md`, `docs/stories.md`, `docs/architecture.md`, `docs/design-system.md` existent-ils ? Chercher aussi `^Stories prêtes` dans `docs/reviews/stories.md`. Afficher `VERSION` si présent. Un cadrage manquant désigne la commande suivante (`/grist-prd`, `/grist-init`, …).
2. **Stories.** Pour chaque identifiant de `docs/stories.md` : complexité, colonne du tableau (ligne `<story>` de `status-all`), présence de la recherche, du design, du plan (`validated: yes` ?) et de la page produit `docs/product/<story>.md` ; total du plan en jours-personne et répartition des tailles ; reste à faire, c'est-à-dire la somme des estimations des tickets pas encore `test` ni `shipped`.
3. **Tickets.** Pour chaque `t*` de `docs/plans/<story>.md` : colonne (`<story>/<ticket>`), taille, estimation, dernière ligne `^Ship allowed:` de `docs/reviews/<story>/<ticket>.md` avec le nombre de tours, état de la PR vers `next`. Un ticket en colonne `review` attend sa livraison ; un ticket `in progress` dont le dernier verdict est `no` attend une correction.
4. **Synthèse.** Une ligne d'abord : X livrées, Y en test, Z en cours, W en backlog. Puis des tableaux compacts, une ligne par story et ses tickets en retrait.
5. **Décisions.** Si `docs/decisions/` existe : nombre d'ADR et le dernier.

Si `docs/` n'existe pas, le projet n'a pas démarré : du code hors `docs/` et plus d'un commit signalent un projet antérieur au flux (renvoyer à `/grist-continue`) ; sinon dépôt vide (`/grist-prd`). Quand tout est `shipped` et que rien n'est en vol, le produit est livré : la bonne suite est `/grist-feature <slug>`, pas un tableau vide.

Terminer par la commande la plus utile, par exemple : « Suite : /grist-docs s02-… » ou « Suite : passer s01/t02 en ready, puis /grist-execute s01 t02 ».
