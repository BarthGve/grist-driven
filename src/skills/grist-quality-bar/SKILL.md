---
name: grist-quality-bar
description: Appliquer la barre de qualité d'un ticket Grist (preuve, sécurité, factorisation, performance, UI) et bloquer la livraison sur un défaut critique ou majeur. Utiliser pendant l'exécution et dans /grist-review.
---
# Barre de qualité

La qualité tient à la façon d'appliquer le plan, pas à des fonctionnalités en plus. Chargé par `implementer` et `reviewer`.

## 1. Preuve (plausible n'est pas correct)

1. Lancer soi-même la vérification complète du projet (`AGENTS.md`, section Vérifications). « Les tests passent » dans un résumé n'est
   qu'une affirmation.
2. Chaque import, fonction, clé de configuration, commande `grist_kit` et colonne citée dans le diff : ouvrir la cible et vérifier qu'elle
   existe, avec ce nom et cette signature. Les références inventées sont la première cause d'échec d'un agent.
3. Diff contre plan, tâche par tâche : tout est-il fait ? Quelque chose a-t-il été ajouté sans être demandé ?
4. Les tests mordent-ils ? Neutraliser l'invariant visé (inverser une condition, retirer une garde), lancer les tests ciblés, **compter les
   tests rouges**, restaurer, vérifier que l'arbre est propre. Zéro rouge = invariant non testé. Un changement purement visuel demande
   une preuve dans le navigateur, pas une mutation.
5. Valeurs plausibles mais fausses (défauts, formats, bornes) jamais confrontées au réel ; régressions sur ce qui réutilise le code touché.

## 2. Sécurité et droits Grist

- Injection : rien d'entrant n'atteint une commande, un gabarit ou un HTML sans validation ; pas de `innerHTML` ni de HTML construit à la main.
- Secrets : aucune clé, aucun id de document, aucune adresse réelle dans le code, les journaux, les bundles ou les jeux de données ;
  `.env` ignoré par git ; `.mcp.json` n'utilise que des variables.
- Droits : chaque règle d'accès a son test, **refus compris**, et une étiquette `[<app>:<ressource>#<n>]` ; pas de `rec.X.Y` ; une règle de
  création est essayée avec un inconnu qui s'ajoute (`newRec`).
- Accès par id : un objet est protégé par appartenance, pas parce que son id est difficile à deviner.
- La structure (schéma, ACL, widgets) ne s'écrit jamais par le MCP.

## 3. Factorisation et maintenabilité

- Une règle métier, un endroit… sauf la règle volontairement en deux copies (formule `conforme` et cœur JS), chacune testée.
- Réutiliser les points d'accroche trouvés en recherche ; ne pas copier un flux sous un autre nom.
- Pas d'abstraction spéculative : extraire à la deuxième utilisation réelle. Pas de code mort ni de commentaire qui ment.

## 4. Performance (critères de `grist-perf`)

Sur tout ticket qui touche un widget, une formule, une règle ou un déploiement :
- widget : un seul chargement, pagination à 50 lignes, `Intl` et collateurs hors des boucles, `Map` plutôt que `find` dans un tri,
  saisie différée, DSFR en version exacte ;
- ui-kit : bundle sous `LIMITE_API_OCTETS` après gzip, chargement différé, cache `react-query` explicite ;
- formules : pas de `lookupRecords` sur une seule clé en colonne d'une grosse table, pas de balayage d'une famille entière par parent,
  `NOW()` connu pour être périmé, colonnes calculées inutiles supprimées ;
- ACL : pas de lecture croisée coûteuse dans une règle ;
- API : écritures groupées par `/apply`, lots découpés devant le pare-feu ;
- toute optimisation affirmée comporte une mesure avant et après (`docs/revue-performance.md`) et une borne large dans les tests.

## 5. Interface

Composants et jetons du design system choisi, rien en dehors. Hors système = dérive (majeur ; critique si la cohérence visuelle du produit casse).

## Sévérité

Lignes de rapport exactes :

```
Max severity: <critical|major|minor|none>
Ship allowed: <yes|no>
```

- **critical** (`Ship allowed: no`) : faille de sécurité, fuite de données, contournement de droit, référence inventée, règle métier ou règle
  d'accès sans test, régression.
- **major** (`Ship allowed: no`) : flux copié-collé, module impossible à faire évoluer, plan ignoré, rupture du design system, régression de
  performance mesurée.
- **minor** : style, nommage, nettoyage léger.

Un seul critique ou majeur bloque. Corriger par `/grist-execute` (mode correction), puis nouvelle `/grist-review`.
