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

# Écarts entre variantes (module `inliner`)

Comparaison par `cmp` de `outils_grist/inliner.py` : SP2C, SCIP_grist, ST_parcours-managerial,
nanterre-grist-projet, ppn_grist, sirpa. Les six fichiers sont **identiques à l'octet près** ;
`portfolio_grist` n'a pas d'`inliner.py`.

## Changements propres à grist-kit

- Le core et les pages deviennent des paramètres : plus de chemin fixe ni de liste `PAGES` codée en dur
  (la liste nommait des widgets de fiches IA) ; plus de CLI propre au module (la commande `inliner` de
  `python -m grist_kit` viendra à la tâche 10).
- `inliner_tout(core_path, pages, check)` est tiré de `sp2c/widgets.py` : il lit le core et traite chaque page.
  La génération du `CHANGELOG.md` qu'il faisait n'en fait pas partie (tâche 6).
- `inliner(page, core, check)` : logique inchangée, y compris le `lambda` de `re.sub` (le core peut contenir des antislashs).

# Écarts entre variantes (module `pages`, ex-`creer_page`)

Comparaison à l'octet (`cmp`) de `outils_grist/creer_page.py` : SP2C, SCIP_grist, ST_parcours-managerial,
nanterre-grist-projet, sirpa, portfolio_grist, ppn_grist, etude_risques. Les huit sont **identiques** ; aucun arbitrage.
(`etude_projet_grist` n'a pas ce fichier.)

## Changements propres à grist-kit

- `grist_kit/pages.py` : plus de `sys.path`, de `RACINE`, de `CONFIG` global ni de `main` (la CLI relève de la tâche 10) ;
  `charger_config(chemin)` et `ecrire_config(chemin, config)` prennent le chemin en paramètre.
- L'entrée de `widgets.json` porte aussi `table_id`.
- `creer` consigne `config["doc_id"] = client.doc_id` à la première création et refuse (`ValueError`) si
  `config["doc_id"]` diffère du document courant.
- Validations avant toute écriture : accès hors `read table` / `full` et table inconnue lèvent `ValueError` (au lieu de `StopIteration`).
- Faux client : aucune extension nécessaire (`CreateViewSection` et `/apply` y existaient déjà).

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

# Écarts entre variantes (module `apply_acl`)

Comparaison par `diff` de `outils_grist/apply_acl.py` (SP2C, SCIP_grist, ST_parcours-managerial, nanterre-grist-projet,
ppn_grist, sirpa). portfolio_grist n'a pas d'`apply_acl.py`.

| Variante | Écart avec SP2C |
|---|---|
| nanterre-grist-projet, ppn_grist, sirpa | Identiques à SP2C. |
| ST_parcours-managerial | Regex d'étiquette `[a-z_]+` : le préfixe d'application n'accepte pas de chiffre. |
| SCIP_grist | Compare aussi le `memo` (une règle insérée décale les suivantes, leur texte doit suivre) ; place les `RemoveRecord` (prune) AVANT les ajouts et mises à jour (une mise à jour peut faire remonter le repli devant une règle obsolète, état que Grist refuse) ; variable `GRIST_DOC_ID_SCIP`. |

## Arbitrage

Aucune incompatibilité : SCIP_grist (la plus récente et la plus complète) est un sur-ensemble de SP2C. Regex de SP2C conservée (chiffres admis, conforme au plan).

- **Retenu** : mise à jour du `memo` et suppressions d'abord (SCIP_grist).

## Changements propres à grist-kit

- `regles_module` paramètre obligatoire (plus de global `acl_rules = None`, plus de repli) ; signature `appliquer(client, regles_module, dry_run=False, prune=False)`.
- Validation avant tout appel réseau (`valider`) : étiquette manquante ou en double -> `ValueError` claire, rien n'est écrit.
- Pas de `main()` ni de variable `GRIST_DOC_ID_*` : le lanceur est la CLI `python -m grist_kit apply-acl` (tâche 10).
- Faux client : aucune extension nécessaire (`/apply` gère déjà `AddRecord`/`UpdateRecord`/`RemoveRecord` sur les tables système ACL).
- Attribut utilisateur : payload complet comparé (`name`, `tableId`, `lookupColId`, `charId`, ressource) ; s'il diffère, `UpdateRecord` (signalé dans `mises_a_jour` en `--dry-run`). SP2C ne comparait que le `name` : un attribut modifié restait périmé.
- Ressource des règles : `planifier(souhaitees, existantes, id_par_cle)` compare aussi `resource` et replace une règle posée sur une autre ressource ; `valider` exige que la partie ressource de l'étiquette égale `resource_key`. SP2C ne comparait ni l'un ni l'autre.

# Écarts entre variantes (module `maj_formules`)

Comparaison par `cmp` de `sp2c/maj_formules.py` : SP2C et ses deux worktrees (`sad-yonath`, `meeting-room-booking-widget`)
sont **identiques à l'octet près**. `etude_projet_grist` et `instances_DOE_grist` n'ont aucune variante (aucun
`maj_formules.py`).

## Changements propres à grist-kit

- `schema_module` devient un paramètre **obligatoire** (signature `appliquer(client, schema_module, dry_run=False)`) :
  plus d'import de `sp2c.schema`, plus de CLI propre au module (la commande `maj-formules` viendra à la tâche 10).
- Clés du rapport alignées sur le plan : `formules` + `choix` fusionnent en `mises_a_jour` ; `inchangees` ajoutée
  (colonnes suivies déjà alignées) ; `divergentes`, `absentes` et `illisibles` conservées.
- Table ou colonne absente : hors simulation, lève `GristErreur` (message citant les absentes, renvoi vers `apply_schema`)
  au lieu de retourner un rapport sans rien écrire ; en simulation, `absentes` est seulement listée.
- Logique de comparaison inchangée : colonnes de données divergentes jamais écrasées, choix ajoutés sans réordonner.

# Écarts entre variantes (module `deployer`, profil dsfr)

Comparaison de `outils_grist/deployer.py` : SP2C, SCIP_grist, ppn_grist, sirpa ; `etude_projet_grist`
(branche `refactor/deployeur-standard`, `outils_grist/deployer.py`). Les cinq sont **identiques à l'octet près** ;
la branche d'etude_projet_grist ajoute `etude_flux/widgets.py`, dont `_verifier_section` est le même contrôle que celui de
`SP2C/sp2c/widgets.py`. Aucun arbitrage.

## Changements propres à grist-kit

- `main()` devient `deployer(client, config, nom, racine, check=False, session=None) -> int` : plus de `sys.path`,
  `load_dotenv`, `RACINE`/`CONFIG` globaux ni `argparse` (la CLI relève de la tâche 10). `session` est injectable
  (`SessionFactice` en test) ; à défaut, `ouvrir_session(client)`.
- `_verifier_section` devient `verifier_section(client, config, nom)`, appelée **avant toute écriture** : la table attendue
  vient de `config["widgets"][nom]["table_id"]` (plus de `schema.PAGES_PAR_WIDGET`). Elle refuse aussi si
  `config["doc_id"]` ≠ `client.doc_id` (ajout par rapport à SP2C). Refus en `ValueError` citant `creer-page` (au lieu de `SystemExit`).
- `section_du_widget` lève `ValueError` (au lieu de `SystemExit`) ; sa consigne cite `python -m grist_kit creer-page`.
- Les réponses de la session HTTP (PATCH et relecture) passent par `_verifie` : tout statut ≥ 300 lève `GristErreur`
  (403 : message pare-feu ; 413 : bundle trop gros), au lieu de `raise_for_status()` et sa trace brute.
- « écriture non conforme » lève `GristErreur` (au lieu de `SystemExit`).
