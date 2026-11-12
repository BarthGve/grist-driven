---
name: grist-tdd
description: Mener un ticket Grist test d'abord (échec constaté, code minimal, mutation) pour le schéma, les règles d'accès, le cœur des widgets et les scripts. Utiliser quand on implémente un ticket.
---
# Test d'abord

## Boucle, par tâche du plan

1. Écrire un test qui décrit le comportement attendu.
2. Le lancer et le voir échouer. Un test jamais vu rouge ne prouve rien.
3. Écrire le code minimal qui le fait passer.
4. Lancer les tests ciblés de l'unité (jamais la suite complète ici), nettoyer, tout reste vert.
5. Cocher la tâche dans le plan. Pas de commit à ce stade : un commit par ticket, tests verts.

Avant le commit du ticket, une fois : vérification rapide, puis complète (`AGENTS.md`, section Vérifications). Rouge : corriger, relancer.
Commande de test inconnue : la chercher dans `pyproject.toml`, `package.json`, le `Makefile` ou la CI ; n'en inventer aucune.

## Où poser les tests dans un projet Grist

Par ordre de valeur :
1. **Règles d'accès** (`grist_kit.testing.acl.permis`) : pour chaque règle, le profil autorisé **et** le profil refusé. Sur un refus, vérifier
   aussi que rien n'a été écrit en aval. Tester la création avec un inconnu qui s'ajoute (`newRec`).
2. **Formules** (`grist_kit.testing.formules`) : chaque règle de `conforme` ou de synthèse, cas qui échoue compris, avec un volume qui rend
   visible un coût quadratique.
3. **Cœur des widgets** : fonctions pures (validations, tris, dérivations), testées avec `node:test` (profil `dsfr`) ou le lanceur du
   projet (profil `ui-kit`). La règle en double (formule et cœur) a un test de chaque côté, sur les mêmes cas.
4. **Scripts** : contre le faux client Grist (`grist_kit.testing.faux_grist`) : idempotence, `--dry-run` sans écriture, garde-fous.
5. **Écrans** : seulement les comportements conditionnels et les interactions (refus, changement d'état, navigation, état vide ou erreur).
   Ni balisage, ni classes CSS, ni libellés ordinaires. Un changement purement visuel se vérifie dans le navigateur, à la bonne largeur et
   dans les deux thèmes, preuve notée avant de cocher.

## La mutation est le critère d'acceptation

Avant de cocher une tâche qui porte un comportement : neutraliser l'invariant protégé (retirer la garde, inverser la condition), relancer
les tests ciblés, **voir le bon test rougir**, restaurer. Rien ne rougit : test décoratif, le supprimer et écrire celui qui mord. Un autre
test rougit : couverture accidentelle, déplacer l'assertion à côté de la règle. Citer dans le compte rendu les mutations jouées et le
nombre de tests rouges.

## Ce qu'on n'écrit pas

- Un test qui fige une liste contre sa propre copie.
- Un test qui vérifie qu'un double a été appelé avec ce qu'on vient de lui passer.
- Des instantanés de balisage, des assertions sur des classes.
- Un test pour monter un taux de couverture : cette méthode n'en fixe aucun.
- Une borne de performance serrée : elle est instable. Bornes larges, qui repèrent une vraie régression (`grist-perf`).

## Coût de la suite

- Un fichier de test par unité, pas par comportement ; au plus deux nouveaux fichiers par ticket (au-delà, le ticket est trop gros).
- Une règle partagée se prouve une fois chez elle, puis un seul témoin de refus chez chaque appelant : jamais la matrice répétée.

## Quand ça dérape

Le test passe du premier coup : il ne teste pas le nouveau comportement, le réécrire. Test instable : réparer d'abord. Comportement joignable
seulement à travers une frontière remplacée : descendre la règle dans une unité testable directement. Tests impossibles à lancer : s'arrêter
et le dire, ne jamais sauter les tests.
