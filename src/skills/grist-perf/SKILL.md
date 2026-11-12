---
name: grist-perf
description: Optimiser un document Grist (widgets, formules, ACL, API, bundle ui-kit) en mesurant avant et après. Utiliser quand un chargement ou une écriture est lent, ou avant de valider une story à gros volume.
---
# Performance Grist

**Mesurer avant et après.** Sans chiffre avant, on ne change rien ; sans chiffre après, le changement n'est pas livré. Mesurer avec un compte
non propriétaire (il lit moins) et un volume réel ou synthétique (par exemple 2 000 lignes), sur deux choses distinctes : le **chargement** d'un
widget (durée de chaque `fetchTable` et instant d'affichage) et l'**écriture** d'une ligne (une formule coûteuse ne se voit qu'ici).
Consigner dans `docs/revue-performance.md` : constat, cause, correction, mesure avant, mesure après. Ajouter ou resserrer une borne
**large** dans les tests (elle repère une régression, elle ne chronomètre pas).

## Widgets

- Un seul chargement des données au démarrage ; ne lire que les tables et colonnes que l'écran affiche. Les colonnes d'adresses pèsent lourd :
  les masquer aux non-propriétaires, ou recopier par formule une synthèse sur une table plus petite.
- Tout tableau paginé par 50 lignes : découper avant de construire les lignes ; page remise à 1 quand un filtre change.
- Formateurs `Intl` et collateurs (`localeCompare` avec options) construits une fois, jamais dans une boucle ; clés de tri calculées une fois.
- Index `Map` plutôt que `find` dans un tri ou une boucle.
- Saisie de recherche différée de 250 ms.
- DSFR en version exacte (le cache navigateur est long) ; polices système ou hébergées si le réseau cible ne joint pas Google Fonts.
- Pas de relecture complète après chaque écriture : relire ce qui a été touché ; redessiner seulement ce qui change.

## Widgets `ui-kit`

- Taille du bundle sous `LIMITE_API_OCTETS` **après gzip** ; surveiller à chaque ajout de dépendance.
- Chargement différé (`lazy`, import dynamique) des écrans lourds ; une entrée par widget.
- Cache `react-query` : une clé par table, durée de fraîcheur explicite, invalidation ciblée après écriture.

## Formules

- `lookupRecords(col=$col)` suivi d'un filtre Python, dans une colonne de **chaque ligne**, est quadratique : Grist refait le travail pour
  toutes les lignes à chaque écriture (3,6 s par lot, 7 s par écriture à 2 000 lignes constaté). Chercher sur toutes les clés du critère
  (`lookupRecords(a=…, b=…)`) : le coût ne dépend plus du volume. Un rang par comptage de lignes : le remplacer par l'id de ligne ou une
  donnée posée par le widget.
- Une synthèse qui balaie toutes les lignes d'une famille dans une colonne de chaque parent : chercher par clé fine pour que Grist ne relance
  que les cellules qui lisent la ligne écrite.
- `NOW()` ne recalcule qu'au chargement du document ou à la modification de la ligne : coût faible, mais valeur périmée ; le widget
  recalcule avec l'heure réelle.
- Colonnes calculées inutiles : en supprimer, chacune coûte à chaque écriture.
- Une colonne qui passe de formule à donnée : voir `grist-schema`.

## ACL

Les règles sont évaluées par ligne : pas de lecture croisée coûteuse dans une condition. Préférer une colonne d'aide recopiée par formule
(voir `grist-acl`) à une recherche.

## API

- Écritures groupées par `/apply` (le tableau d'actions est à la racine du corps), pas une requête par ligne.
- Lots découpés devant le pare-feu : un lot refusé se coupe en deux, se retente après une pause, et on s'arrête si des lignes isolées sont
  refusées à la suite (`grist-deploy`).
