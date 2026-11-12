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
