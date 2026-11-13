# Écarts entre variantes (module `client` et faux client)

Comparaison par `diff` de `outils_grist/grist_client.py` : projet A, projet B, projet C,
projet D, projet F, projet G.

| Variante | Écart avec projet A |
|---|---|
| projet B, projet C, projet D, projet F, projet G | Identiques à projet A. |
| projet E | `_make_request` plus robuste : session persistante, suivi manuel des redirections 301/302/303/307/308 en rejouant la **même** méthode (sinon un POST redirigé devient un GET et l'écriture est ignorée sans erreur), cadence de 0,6 s entre requêtes, deux nouvelles tentatives sur 403 Incapsula, refus d'une méthode HTTP inconnue avant tout appel. |

## Arbitrage

Comportements compatibles (la variante projet E est un sur-ensemble de projet A) : la variante projet E est **retenue**, aucun
arbitrage demandé. `cadence` et `pause_refus` sont des attributs de classe (mise à 0 dans les tests).

## Changements propres à grist-kit

- Retrait des méthodes de génération de user stories : `get_config_projet`, `_get_default_config`, `get_idees_validees`,
  `idee_has_user_story`, `create_user_story`, `update_idee_statut` (et la configuration par défaut qui nommait un client).
- Toute réponse HTTP ≥ 400 lève `GristErreur` (sous-classe de `RuntimeError`) au message lisible ; 403 : « pare-feu »
  + droits de la clé ; 413 : bundle trop gros. Les erreurs réseau (`requests`) ne sont pas encapsulées.
- `faux_grist.py` porté tel quel, sauf `base_url` neutralisée (`https://grist.test/o/demo/api`, au lieu d'un nom de projet).

# Écarts entre variantes (module `inliner`)

Comparaison par `cmp` de `outils_grist/inliner.py` : projet A, projet B, projet C,
projet D, projet E, projet F. Les six fichiers sont **identiques à l'octet près** ;
`projet G` n'a pas d'`inliner.py`.

## Changements propres à grist-kit

- Le core et les pages deviennent des paramètres : plus de chemin fixe ni de liste `PAGES` codée en dur
  (la liste nommait des widgets de fiches IA) ; plus de CLI propre au module (la commande `inliner` de
  `python -m grist_kit` viendra à la tâche 10).
- `inliner_tout(core_path, pages, check)` est tiré de `projet A/widgets.py` : il lit le core et traite chaque page.
  La génération du `CHANGELOG.md` qu'il faisait n'en fait pas partie (tâche 6).
- `inliner(page, core, check)` : logique inchangée, y compris le `lambda` de `re.sub` (le core peut contenir des antislashs).

# Écarts entre variantes (module `pages`, ex-`creer_page`)

Comparaison à l'octet (`cmp`) de `outils_grist/creer_page.py` : projet A, projet B, projet C,
projet D, projet F, projet G, projet E, projet J. Les huit sont **identiques** ; aucun arbitrage.
(`projet H` n'a pas ce fichier.)

## Changements propres à grist-kit

- `grist_kit/pages.py` : plus de `sys.path`, de `RACINE`, de `CONFIG` global ni de `main` (la CLI relève de la tâche 10) ;
  `charger_config(chemin)` et `ecrire_config(chemin, config)` prennent le chemin en paramètre.
- L'entrée de `widgets.json` porte aussi `table_id`.
- `creer` consigne `config["doc_id"] = client.doc_id` à la première création et refuse (`ValueError`) si
  `config["doc_id"]` diffère du document courant.
- Validations avant toute écriture : accès hors `read table` / `full` et table inconnue lèvent `ValueError` (au lieu de `StopIteration`).
- Faux client : aucune extension nécessaire (`CreateViewSection` et `/apply` y existaient déjà).

# Écarts entre variantes (module `apply_schema`)

Comparaison par `diff` de `outils_grist/apply_schema.py` (projet A, projet B, projet C, projet D,
projet E, projet F, projet G) et de `projet H/apply_schema.py`.

| Variante | Écart avec projet A |
|---|---|
| projet C, projet D, projet F | Identiques à projet A. |
| projet B | Réécrit aussi les formules du schéma qui ont changé (clé `formules_mises_a_jour`) ; force `isFormula=False` sur toute colonne de données ajoutée (table existante, seconde passe) ; variable `GRIST_DOC_ID_SCIP`. |
| projet G | Comme projet B, plus `widgetOptions` tiré de `col["options"]` quand il n'y a pas de `choices`. |
| projet E | Table neuve : colonnes de données d'abord, puis colonnes de formule une à une (le pare-feu refuse parfois, en 403, une table envoyée d'un bloc avec ses formules). |
| projet H | Simple lanceur (51 lignes) : appelle le module de projet A avec son propre schéma, puis réécrit les formules de déclenchement (`DECLENCHEURS`) en `isFormula=False`, `recalcWhen=0`. |

## Arbitrage

Aucune incompatibilité : toutes les variantes sont des sur-ensembles de projet A, aucun arbitrage demandé.

- **Retenu** : correction `isFormula=False` (projet B, projet G) ; `options` (projet G) ; formules de table neuve une à une (projet E).
- **Non repris ici** : réécriture des formules existantes (projet B, projet G) : c'est le rôle de `maj_formules` (tâche 3 bis), qui évite aussi de changer les clés du rapport (`tables_creees`, `colonnes_ajoutees`, `inchangees`).
  Les `DECLENCHEURS` du projet H sont couverts par `declenchee: True` dans la définition de colonne (payload `isFormula=False`, `recalcWhen=0` dès la création).

## Changements propres à grist-kit

- `schema_module` paramètre obligatoire (plus de global `schema = None`) ; signature `appliquer(client, schema_module, dry_run=False)`.
- `--dry-run` sur un document à jour ne signale plus la colonne auto-référente déjà présente (projet A la listait toujours).
- Pas de `main()` ni de variable `GRIST_DOC_ID_*` : le lanceur est la CLI `python -m grist_kit apply-schema` (tâche 10).
- Contrat de `schema_module` : `TABLES` et `colonnes_auto_referentes()` seulement ; `get_table()` de projet A n'est pas requis.

# Écarts entre variantes (module `apply_acl`)

Comparaison par `diff` de `outils_grist/apply_acl.py` (projet A, projet B, projet C, projet D,
projet E, projet F). projet G n'a pas d'`apply_acl.py`.

| Variante | Écart avec projet A |
|---|---|
| projet D, projet E, projet F | Identiques à projet A. |
| projet C | Regex d'étiquette `[a-z_]+` : le préfixe d'application n'accepte pas de chiffre. |
| projet B | Compare aussi le `memo` (une règle insérée décale les suivantes, leur texte doit suivre) ; place les `RemoveRecord` (prune) AVANT les ajouts et mises à jour (une mise à jour peut faire remonter le repli devant une règle obsolète, état que Grist refuse) ; variable `GRIST_DOC_ID_SCIP`. |

## Arbitrage

Aucune incompatibilité : projet B (la plus récente et la plus complète) est un sur-ensemble de projet A. Regex de projet A conservée (chiffres admis, conforme au plan).

- **Retenu** : mise à jour du `memo` et suppressions d'abord (projet B).

## Changements propres à grist-kit

- `regles_module` paramètre obligatoire (plus de global `acl_rules = None`, plus de repli) ; signature `appliquer(client, regles_module, dry_run=False, prune=False)`.
- Validation avant tout appel réseau (`valider`) : étiquette manquante ou en double -> `ValueError` claire, rien n'est écrit.
- Pas de `main()` ni de variable `GRIST_DOC_ID_*` : le lanceur est la CLI `python -m grist_kit apply-acl` (tâche 10).
- Faux client : aucune extension nécessaire (`/apply` gère déjà `AddRecord`/`UpdateRecord`/`RemoveRecord` sur les tables système ACL).
- Attribut utilisateur : payload complet comparé (`name`, `tableId`, `lookupColId`, `charId`, ressource) ; s'il diffère, `UpdateRecord` (signalé dans `mises_a_jour` en `--dry-run`). projet A ne comparait que le `name` : un attribut modifié restait périmé.
- Ressource des règles : `planifier(souhaitees, existantes, id_par_cle)` compare aussi `resource` et replace une règle posée sur une autre ressource ; `valider` exige que la partie ressource de l'étiquette égale `resource_key`. projet A ne comparait ni l'un ni l'autre.

# Écarts entre variantes (module `maj_formules`)

Comparaison par `cmp` de `projet A/maj_formules.py` : projet A et ses deux worktrees (`sad-yonath`, `meeting-room-booking-widget`)
sont **identiques à l'octet près**. `projet H` et `projet I` n'ont aucune variante (aucun
`maj_formules.py`).

## Changements propres à grist-kit

- `schema_module` devient un paramètre **obligatoire** (signature `appliquer(client, schema_module, dry_run=False)`) :
  plus d'import de `projet A.schema`, plus de CLI propre au module (la commande `maj-formules` viendra à la tâche 10).
- Clés du rapport alignées sur le plan : `formules` + `choix` fusionnent en `mises_a_jour` ; `inchangees` ajoutée
  (colonnes suivies déjà alignées) ; `divergentes`, `absentes` et `illisibles` conservées.
- Table ou colonne absente : hors simulation, lève `GristErreur` (message citant les absentes, renvoi vers `apply_schema`)
  au lieu de retourner un rapport sans rien écrire ; en simulation, `absentes` est seulement listée.
- Logique de comparaison inchangée : colonnes de données divergentes jamais écrasées, choix ajoutés sans réordonner.

# Écarts entre variantes (module `deployer`, profil dsfr)

Comparaison de `outils_grist/deployer.py` : projet A, projet B, projet E, projet F ; `projet H`
(branche `refactor/deployeur-standard`, `outils_grist/deployer.py`). Les cinq sont **identiques à l'octet près** ;
la branche du projet H ajoute `projet H/widgets.py`, dont `_verifier_section` est le même contrôle que celui de
`projet A/projet A/widgets.py`. Aucun arbitrage.

## Changements propres à grist-kit

- `main()` devient `deployer(client, config, nom, racine, check=False, session=None) -> int` : plus de `sys.path`,
  `load_dotenv`, `RACINE`/`CONFIG` globaux ni `argparse` (la CLI relève de la tâche 10). `session` est injectable
  (`SessionFactice` en test) ; à défaut, `ouvrir_session(client)`.
- `_verifier_section` devient `verifier_section(client, config, nom)`, appelée **avant toute écriture** : la table attendue
  vient de `config["widgets"][nom]["table_id"]` (plus de `schema.PAGES_PAR_WIDGET`). Elle refuse aussi si
  `config["doc_id"]` ≠ `client.doc_id` (ajout par rapport à projet A). Refus en `ValueError` citant `creer-page` (au lieu de `SystemExit`).
- `section_du_widget` lève `ValueError` (au lieu de `SystemExit`) ; sa consigne cite `python -m grist_kit creer-page`.
- Les réponses de la session HTTP (PATCH et relecture) passent par `_verifie` : tout statut ≥ 300 lève `GristErreur`
  (403 : message pare-feu ; 413 : bundle trop gros), au lieu de `raise_for_status()` et sa trace brute.
- « écriture non conforme » lève `GristErreur` (au lieu de `SystemExit`).

# Écarts entre variantes (module `build_uikit`, profil ui-kit)

Source : `projet H/deployer_widgets.py` (seule variante : `chargeur_gzip` et le dépôt du bundle) et
`widgets_ui/{build.mjs,package.json,vite.config.ts}` (contrat : `dist/<entrée>.html`, ligne `<entrée> : N Ko` par build).
La branche `refactor/deployeur-standard` n'a pas de profil ui-kit. Aucun arbitrage.

## Changements propres à grist-kit

- `chargeur_gzip` porté **à l'identique** (gzip 9, `mtime=0`, base64, `DecompressionStream`).
- Le dépôt devient `deployer_uikit(client, config, nom, widgets_ui, check=False, session=None) -> int`, dans `grist_kit/build_uikit.py`
  (pas dans `deployer.py`, laissé intact : il en importe `verifier_section`, `corps_patch`, `ouvrir_session`, `_verifie`, `synchroniser_champs`).
  Plus de `WIDGETS` codé en dur ni de `creer_page` dans la boucle (`creer-page` est une commande à part) : la section vient de `widgets.json`,
  l'entrée construite de `widgets[nom]["entree"]` (défaut : le nom du widget).
- Ajouts par rapport à `deployer_widgets.py` : garde-fou `verifier_section` (section/document), mode `check` (compare au `dist/`),
  relecture et vérification après PATCH, réponses HTTP ≥ 300 en `GristErreur` (au lieu de `raise_for_status()`).
- **Limite de taille** : `LIMITE_API_OCTETS = 1_000_000`, mesurée sur le **corps du PATCH** (le pare-feu impose un échappement `\uXXXX` qui gonfle
  la base64 : mesurer la seule charge compressée sous-estimerait). Au-delà : `GristErreur` (« 413 … Réduire le bundle … ») **avant** toute écriture.
- `construire(widgets_ui, entrees=None)` : nouveau ; `npm ci` puis `node build.mjs [entrées]`, `GristErreur` claire si `node` absent ou < 20, ou `npm` absent ;
  sortie et code d'erreur des commandes cités. Taille lue sur les lignes `<entrée> : N Ko` de `build.mjs`.
- Non repris : `synchroniser_changelog` (table `CHANGELOG` propre à ce projet ; le journal des versions relève de `versions.py`).

# Écarts (CLI `python -m grist_kit`, tâche 10)

Pas de variante source : la CLI est nouvelle (chaque dépôt avait ses scripts à `argparse` propres). Choix propres à grist-kit :

- `main(argv, racine, client)` : `racine` (défaut : dossier courant) et `client` injectables pour les tests ; sans client, `GristClient(doc_id=--doc ou GRIST_DOC_ID)` après `load_dotenv(<racine>/.env)`. Document absent : message citant `GRIST_DOC_ID`, code 1.
- Toute `GristErreur`, `ValueError`, `FileNotFoundError` ou `ImportError` devient « Erreur : … » sur stderr et code 1 (jamais de trace).
- `--dry-run` : `apply-schema`, `maj-formules`, `apply-acl`, `amorcer` le transmettent au module ; `creer-page` affiche seulement le plan ; `deployer` et `inliner` comparent sans écrire (comme `--check`, mais code 0) ; `versions` n'écrit ni la table CHANGELOG ni `CHANGELOG.md`.
- `deployer` : `dsfr` → `deployer.deployer` sur `<widgets_dir>` ; `ui-kit` → `build_uikit.construire` (sauf `--check`/`--dry-run`, qui ne lancent ni `npm` ni `node`) puis `deployer_uikit`. `widgets.json` est lu à la racine du projet.
- `inliner` : recopie `core` dans les `*.html` de premier niveau de `widgets_dir` ; sans objet en `ui-kit` (message, code 0).
- `versions` : le journal est cherché dans `core` puis dans les pages ; `CHANGELOG.md` écrit à la racine, sans libellés de widgets (identifiants).
- `amorcer` : `<package>.amorcer.executer(client, dry_run)` ; module absent (et seulement lui) = « rien à faire », code 0.
- `charger_projet` ajoute la racine à `sys.path` et n'importe `<package>.schema` / `.acl_rules` / `.amorcer` qu'à l'usage (propriétés paresseuses) : `inliner` ou un design system refusé n'exigent pas ces modules.
- `widgets_dir` et `core` sont facultatifs dans `.grist-driven.json` (défauts : `widgets`/`widgets_ui` selon le profil, `widgets/core.js`).
- `tests/test_testing_helpers.py::test_helpers_n_importent_aucun_module_de_projet` exige `grist-kit` installé (`pip install -e packages/grist-kit`) : sans cela il échoue, indépendamment de cette tâche.

# Écarts du gabarit de projet (tâche 14)

- **Profil `ui-kit` : build non lancé.** Aucun `npm ci` ni build Vite dans les tests (pas de réseau, rien d'installé).
  `tests/test_projet_genere.py` vérifie la structure de `widgets_ui/`, la dépendance `@gouvfr-lasuite/ui-components`,
  la syntaxe de `build.mjs` (`node --check`) et le message de l'inliner ; le déploiement gzip est couvert par
  `test_deployer_uikit.py`. À jouer à la main : `cd widgets_ui && npm ci && node build.mjs`.
- **Versions npm non vérifiées hors ligne** : `@gouvfr-lasuite/ui-components` épinglé à `2.0.0` (reprise de la version
  du fork utilisé dans `projet H`) ainsi que React/Vite de ce projet ; à confirmer au premier vrai `npm ci`.
- **Source du kit** : `GRIST_KIT_SPEC` par défaut = `git+https://github.com/brunogauville/grist-driven.git@v0.1.0#subdirectory=packages/grist-kit`,
  dépôt et tag supposés (le dépôt n'a pas encore de remote) ; surchargeable (chemin local en test).
- `"package"` de `.grist-driven.json` : nom Python dérivé du nom de l'application (`Mon App` → `mon_app`), au lieu de
  la valeur fixe `grist-kit` posée par la tâche 11 (le kit importe `<package>.schema`).
- Le gabarit ne pose pas `.github/workflows/ci.yml` lui-même : `ci_poser` (tâche 15) s'en charge ; son étape Node
  accepte désormais l'absence de `package-lock.json`.
