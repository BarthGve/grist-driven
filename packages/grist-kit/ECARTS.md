# Écarts entre variantes (module `client` et faux client)

Comparaison par `diff` de `outils_grist/grist_client.py` : SP2C, SCIP_grist, ST_parcours-managerial,
nanterre-grist-projet, sirpa, portfolio_grist.

| Variante | Écart avec SP2C |
|---|---|
| SCIP_grist, ST_parcours-managerial, nanterre-grist-projet, sirpa, portfolio_grist | Identiques à SP2C. |
| ppn_grist | `_make_request` plus robuste : session persistante, suivi manuel des redirections 301/302/303/307/308 en rejouant la **même** méthode (sinon un POST redirigé devient un GET et l'écriture est ignorée sans erreur), cadence de 0,6 s entre requêtes, deux nouvelles tentatives sur 403 Incapsula, refus d'une méthode HTTP inconnue avant tout appel. |

## Arbitrage

Comportements compatibles (la variante ppn_grist est un sur-ensemble de SP2C) : la variante ppn_grist est **retenue**, aucun
arbitrage demandé. `cadence` et `pause_refus` sont des attributs de classe (mise à 0 dans les tests).

## Changements propres à grist-kit

- Retrait des méthodes de génération de user stories : `get_config_projet`, `_get_default_config`, `get_idees_validees`,
  `idee_has_user_story`, `create_user_story`, `update_idee_statut` (et la configuration par défaut qui nommait un client).
- Toute réponse HTTP ≥ 400 lève `GristErreur` (sous-classe de `RuntimeError`) au message lisible ; 403 : « pare-feu »
  + droits de la clé ; 413 : bundle trop gros. Les erreurs réseau (`requests`) ne sont pas encapsulées.
- `faux_grist.py` porté tel quel, sauf `base_url` neutralisée (`https://grist.test/o/demo/api`, au lieu d'un nom de projet).

# Écarts entre variantes (module `apply_schema`)

Comparaison par `diff` de `outils_grist/apply_schema.py` (SP2C, SCIP_grist, ST_parcours-managerial, nanterre-grist-projet,
ppn_grist, sirpa, portfolio_grist) et de `etude_projet_grist/apply_schema.py`.

| Variante | Écart avec SP2C |
|---|---|
| ST_parcours-managerial, nanterre-grist-projet, sirpa | Identiques à SP2C. |
| SCIP_grist | Réécrit aussi les formules du schéma qui ont changé (clé `formules_mises_a_jour`) ; force `isFormula=False` sur toute colonne de données ajoutée (table existante, seconde passe) ; variable `GRIST_DOC_ID_SCIP`. |
| portfolio_grist | Comme SCIP_grist, plus `widgetOptions` tiré de `col["options"]` quand il n'y a pas de `choices`. |
| ppn_grist | Table neuve : colonnes de données d'abord, puis colonnes de formule une à une (le pare-feu refuse parfois, en 403, une table envoyée d'un bloc avec ses formules). |
| etude_projet_grist | Simple lanceur (51 lignes) : appelle le module de SP2C avec son propre schéma, puis réécrit les formules de déclenchement (`DECLENCHEURS`) en `isFormula=False`, `recalcWhen=0`. |

## Arbitrage

Aucune incompatibilité : toutes les variantes sont des sur-ensembles de SP2C, aucun arbitrage demandé.

- **Retenu** : correction `isFormula=False` (SCIP_grist, portfolio_grist) ; `options` (portfolio_grist) ; formules de table neuve une à une (ppn_grist).
- **Non repris ici** : réécriture des formules existantes (SCIP_grist, portfolio_grist) : c'est le rôle de `maj_formules` (tâche 3 bis), qui évite aussi de changer les clés du rapport (`tables_creees`, `colonnes_ajoutees`, `inchangees`).
  Les `DECLENCHEURS` d'etude_projet_grist sont couverts par `declenchee: True` dans la définition de colonne (payload `isFormula=False`, `recalcWhen=0` dès la création).

## Changements propres à grist-kit

- `schema_module` paramètre obligatoire (plus de global `schema = None`) ; signature `appliquer(client, schema_module, dry_run=False)`.
- `--dry-run` sur un document à jour ne signale plus la colonne auto-référente déjà présente (SP2C la listait toujours).
- Pas de `main()` ni de variable `GRIST_DOC_ID_*` : le lanceur est la CLI `python -m grist_kit apply-schema` (tâche 10).
- Contrat de `schema_module` : `TABLES` et `colonnes_auto_referentes()` seulement ; `get_table()` de SP2C n'est pas requis.
