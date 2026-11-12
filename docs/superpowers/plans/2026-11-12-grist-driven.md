# grist-driven — plan d'implémentation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal :** Livrer `grist-driven` v0.1 : un repo public, installable en une ligne, qui pose dans un projet les commandes `grist-*`, les skills, la bibliothèque `grist-kit`, un gabarit de projet (DSFR ou La Suite ui-kit) et le MCP Grist.

**Architecture :** Trois blocs construits dans l'ordre : (A) `grist-kit`, paquet Python extrait des dépôts SP2C et etude_projet_grist ; (B) `install.sh` et le gabarit de projet ; (C) le contenu repris de driven (commandes, skills, agents, scripts, gabarits), réécrit et renommé `grist-*`.

**Tech Stack :** Python ≥ 3.11 (`requests`, `python-dotenv`, `pytest`), bash pur pour l'installeur, Node ≥ 20 seulement pour le profil `ui-kit` (React, Vite, `vite-plugin-singlefile`).

**Spec :** `docs/superpowers/specs/2026-11-12-grist-driven-design.md`

## Contraintes globales (valeurs exactes de la spec)

- Repo **public** : aucun identifiant de document, clé, nom de client ni donnée réelle ; exemples et tests neutres ; CI sans secret.
- Python ≥ 3.11 ; dépendances `requests`, `python-dotenv`, `pytest` ; installeur en bash pur ; Node ≥ 20 requis **seulement** pour le design system ui-kit.
- Claude Code seul ; macOS et Linux ; pas de build Node pour installer.
- Commandes et skills préfixés `grist-` ; aucun reste de `dm-` ni de `.dm/`.
- Design system **obligatoire, sans défaut** : `dsfr` ou `ui-kit` (`--design-system dsfr|ui-kit` en mode `--yes`).
- Secrets : `.env` ignoré par git ; `.mcp.json` n'utilise que `${GRIST_API_KEY}` et `${GRIST_API_HOST}` ; la clé n'est écrite que dans `.env`.
- MCP par défaut `mcp-server-grist`, installé isolé (`pipx` ou `uv tool`, à défaut `pip --user`), **jamais sans l'accord** de l'utilisateur ; `grist-coder` sur demande seulement.
- Écritures de structure (schéma, ACL, widgets) uniquement par les scripts de `grist-kit`, jamais par le MCP.
- Toutes les commandes du kit : idempotentes, `--dry-run`, `--doc <id>`.
- Textes visibles, commentaires et commits en français ; commits `✨ FEAT:`, `🐛 FIX:`, `📝 DOCS:`, `✅ TEST:`, `🔧 CHORE:`.
- Fichiers repris de driven : tout fichier resté proche de killer-saas est réécrit ; `NOTICE` conserve la filiation.
- Flux git `main`/`next`, tableau GitHub, wiki et semver conservés ; `grist-continue` remplace le mode « cloner un SaaS ».

## Exécution (décidée par Bruno : subagents, chacun dans sa conversation)

Chaque tâche est menée dans **sa propre session**, dans son propre worktree (branche `feature/tache-<n>`), depuis `next` à jour ; une PR par tâche vers `next`, relue par une session de relecture distincte avant fusion. Les tâches qui modifient `install.sh` s'exécutent **une à la fois**.

| Vague | Tâches (en parallèle) | Prérequis |
|---|---|---|
| 0 | 1 | — |
| 1 | 2, 4, 5, 6, 7, 11, 17 | 1 (sauf 11 et 17) |
| 2 | 3, 3 bis, 8, 12, 18, 21, 22 | 2 pour 3 bis ; 7 pour 8 ; 11 pour 12 ; 17 pour 18, 21, 22 |
| 3 | 9, 13, 19 | 8 ; 12 ; 18, 21 et 22 |
| 4 | 10, 15, 20 | 2, 3, 3 bis, 5, 6, 7, 8, 9 ; 13 ; 19 |
| 5 | 14 | 10, 12 |
| 6 | 16 | 12, 13, 14 |
| 7 | 23 | toutes |

Ordre sur `install.sh` : 11 → 12 → 13 → 15 → 14 → 16.

## Points de focus de la relecture

Chacun a son test dans la tâche indiquée.

1. `curl … | bash` **sans terminal** et sans `--yes` : échec net, sans attente ni choix implicite du design system (tâche 11).
2. `init` relancé sur un projet aux gabarits modifiés et à `.env` existant : rien n'est écrasé, `.env` n'est jamais réécrit (tâches 12 et 14).
3. La clé d'API n'apparaît ni dans `.mcp.json`, ni dans la sortie de `--dry-run`, ni dans l'index git ; `.env` est ignoré **avant** d'être écrit (tâches 11 et 13).
4. Ni `pipx` ni `uv`, ou Python « externally managed » (PEP 668) : `init` n'échoue pas, affiche la commande à lancer (tâche 13).
5. Erreurs d'API lisibles : 403 du pare-feu (corps refusé) et 413 (bundle trop gros) donnent un message clair, pas une trace (tâches 1, 8 et 9).

---

## Phase A — `grist-kit`

Dépôt : `packages/grist-kit/` ; tests : `cd packages/grist-kit && python -m pytest -q`. Sources à porter (lecture seule) : `~/Developpeur/SP2C/outils_grist/*.py`, `~/Developpeur/SP2C/sp2c/tests/{faux_grist,acl,formules}.py`, `~/Developpeur/etude_projet_grist/{versions,deployer_widgets}.py` et la branche `refactor/deployeur-standard`. Pour chaque module, comparer d'abord les variantes des 9 dépôts par `diff`, consigner les écarts dans `packages/grist-kit/ECARTS.md` ; demander un arbitrage à Bruno seulement si deux comportements sont incompatibles.

### Tâche 1 : bootstrap du repo, `GristClient`, faux client

**Fichiers :**
- Créer : `VERSION` (`0.1.0`), `NOTICE`, `.gitignore` (inclut `.env`, `.venv`, `node_modules`, `dist`), `README.md` (court), `packages/grist-kit/pyproject.toml`, `packages/grist-kit/grist_kit/__init__.py`, `packages/grist-kit/grist_kit/client.py`, `packages/grist-kit/grist_kit/testing/__init__.py`, `packages/grist-kit/grist_kit/testing/faux_grist.py`, `packages/grist-kit/tests/test_client.py`

**Interfaces :**
- Produit : `GristClient(api_key: str|None=None, doc_id: str|None=None, base_url: str|None=None)` ; variables `GRIST_API_KEY`, `GRIST_API_HOST` (défaut `https://grist.numerique.gouv.fr/api`), `GRIST_DOC_ID` ; attributs `api_key`, `doc_id`, `base_url`, `headers` ; `_make_request(method: str, endpoint: str, data=None) -> Any` ; `fetch_table(name) -> list[dict]` ; `add_record(table, data) -> int` ; `update_record(table, record_id, updates) -> None`.
- Produit : `grist_kit.testing.faux_grist.ClientFactice` (même interface `_make_request`, plus `ecritures`, `ajouter(table, fields)`, `lignes(table)`), `SessionFactice(client, deforme=False)` avec `get(url, timeout)` et `patch(url, data, timeout)`.

- [ ] **Étape 1 : `git init`, branche `main`, fichiers racine.** `NOTICE` cite killer-saas (Mike Codeur) et ai-driven-method comme filiation. `LICENSE` : **MIT** (Bruno : « libre de droit » ; interprétation de l'auteur, une licence totalement sans condition type CC0/Unlicense reste possible si Bruno la préfère). Elle ne couvre que le contenu propre au repo ; `NOTICE` rappelle la filiation avec killer-saas et que les fichiers hérités ne sont pas relicensés, d'où la réécriture (tâche 17).
- [ ] **Étape 2 : écrire les tests** (`test_client.py`) : `test_cle_absente_leve_valueerror`, `test_doc_absent_leve_valueerror`, `test_hote_lu_dans_l_environnement`, `test_requete_403_leve_erreur_lisible` (le message contient « pare-feu » et le code 403, pas de trace brute), `test_fetch_table_via_faux_client`.
- [ ] **Étape 3 : lancer, constater l'échec** — `python -m pytest -q` → FAIL (module absent).
- [ ] **Étape 4 : porter `GristClient`** depuis `SP2C/outils_grist/grist_client.py` **sans** les méthodes propres à la génération de user stories (`get_config_projet`, `get_idees_validees`, `idee_has_user_story`, `create_user_story`, `update_idee_statut`) ; traduire les erreurs HTTP 403 en `GristErreur` (sous-classe de `RuntimeError`) au message explicite. Porter `faux_grist.py` tel quel.
- [ ] **Étape 5 : lancer, constater le succès** — `python -m pytest -q` → tous PASS.
- [ ] **Étape 6 : commit** — `git add -A && git commit -m "🎉 INIT: grist-kit, client Grist et faux client"`.

### Tâche 2 : `apply_schema`

**Fichiers :** Créer `grist_kit/apply_schema.py`, `tests/test_apply_schema.py`, `tests/schema_exemple.py` (schéma de 3 tables fictives dont une auto-référente).

**Interfaces :**
- Consomme : `ClientFactice` (tâche 1).
- Produit : `appliquer(client, schema_module, dry_run: bool=False) -> dict` avec les clés `tables_creees`, `colonnes_ajoutees`, `inchangees` (listes) ; `schema_module` expose `TABLES` (liste ordonnée de tables ; chaque colonne : `id`, `label`, `type`, `formula?`, `declenchee?`, `choices?`) et `colonnes_auto_referentes() -> list`.

- [ ] **Étape 1 : tests** : `test_cree_tables_et_colonnes_manquantes`, `test_deuxieme_passage_ne_change_rien` (idempotence : `tables_creees == []`), `test_dry_run_n_ecrit_rien` (`client.ecritures == []`), `test_colonne_auto_referente_creee_en_deuxieme_passe`, `test_ne_supprime_jamais` (colonne en trop conservée), `test_colonne_de_donnees_ajoutee_a_table_existante_n_est_pas_formule` (`isFormula` faux : piège documenté dans SP2C).
- [ ] **Étape 2 : lancer → FAIL.**
- [ ] **Étape 3 : porter `SP2C/outils_grist/apply_schema.py`** ; `schema_module` devient un paramètre obligatoire (plus de global `schema = None`) ; ajouter la correction de `isFormula` pour les colonnes de données ajoutées à une table existante.
- [ ] **Étape 4 : lancer → PASS.**
- [ ] **Étape 5 : commit** — `✨ FEAT: apply_schema idempotent`.

### Tâche 3 : `apply_acl`

**Fichiers :** Créer `grist_kit/apply_acl.py`, `tests/test_apply_acl.py`, `tests/regles_exemple.py`.

**Interfaces :**
- Produit : `ETIQUETTE` (regex `^\[[a-z0-9_]+:([a-z_]+)#(\d+)\]`) ; `planifier(souhaitees: list[dict], existantes: list[dict]) -> dict` (clés `ajouts`, `mises_a_jour`, `obsoletes`, sans appel réseau) ; `ressource_a_renommer(cle, table_id, existantes, ressources) -> int|None` ; `appliquer(client, regles_module, dry_run=False, prune=False) -> dict` (retourne le plan) ; `regles_module` expose `RESOURCES`, `RULES`, `USER_ATTRIBUTES`.

- [ ] **Étape 1 : tests** : `test_regle_nouvelle_est_ajoutee`, `test_formule_modifiee_met_a_jour_en_place` (pas de doublon), `test_regle_retiree_signalee_pas_supprimee`, `test_prune_supprime_les_obsoletes`, `test_ordre_relatif_force_si_different`, `test_regle_sans_etiquette_refusee` (erreur claire, pas d'ajout), `test_etiquettes_en_double_refusees`, `test_dry_run_n_ecrit_rien`, `test_le_post_apply_envoie_les_actions_a_la_racine` (piège d'API de SP2C).
- [ ] **Étape 2 : lancer → FAIL.**
- [ ] **Étape 3 : porter `SP2C/outils_grist/apply_acl.py`** (variante la plus récente après diff des 3) ; `regles_module` obligatoire ; ajouter la validation des étiquettes manquantes ou en double avant tout appel.
- [ ] **Étape 4 : lancer → PASS.**
- [ ] **Étape 5 : commit** — `✨ FEAT: apply_acl par étiquettes`.

### Tâche 3 bis : `maj_formules` (alignement des formules et choix existants)

`apply_schema` ne modifie jamais une formule ni les choix d'une colonne existante ; sans cette tâche, un changement de règle métier (`conforme`) n'atteindrait jamais le document.

**Fichiers :** Créer `grist_kit/maj_formules.py`, `tests/test_maj_formules.py`.

**Interfaces :**
- Consomme : `ClientFactice`, `tests/schema_exemple.py` (tâches 1 et 2).
- Produit : `appliquer(client, schema_module, dry_run: bool=False) -> dict` (clés `mises_a_jour`, `divergentes`, `inchangees` ; refuse d'écrire, avec message, si une table ou une colonne du schéma manque dans le document) ; `_options(texte) -> dict` (lecture des `widgetOptions`).

- [ ] **Étape 1 : tests** : `test_formule_modifiee_est_mise_a_jour`, `test_dry_run_liste_sans_ecrire`, `test_table_manquante_refuse_d_ecrire`, `test_colonne_de_donnees_non_formule_est_dite_divergente` (listée, jamais écrasée), `test_choix_alignes_sur_le_schema`, `test_idempotent`.
- [ ] **Étape 2 : FAIL.** **Étape 3 : porter** `SP2C/sp2c/maj_formules.py` (hors de `outils_grist/`) avec `schema_module` obligatoire. **Étape 4 : PASS.**
- [ ] **Étape 5 : commit** — `✨ FEAT: maj_formules`.

### Tâche 4 : aides de test (simulateur d'ACL, formules en mémoire)

**Fichiers :** Créer `grist_kit/testing/acl.py`, `grist_kit/testing/formules.py`, `tests/test_testing_helpers.py`.

**Interfaces :**
- Produit : `permis(base, regles_module, email, table, droit, rec=None, apres=None, colonne=None, acces="editors") -> bool` (évalue les règles comme Grist : ressources de la plus précise à la plus générale, première règle qui tranche chaque droit ; `DROITS = "CRUD"`) ; `Base(schema_module, maintenant=…, **tables)` avec `avec(table, id_=None, **valeurs)`, `ligne(table, id_)`, `executer(formule, rec)`, `toutes_les_formules()` ; `Ligne`, `Table` (`all`, `lookupRecords`, `lookupOne`). Le simulateur d'ACL et les formules reçoivent **explicitement** le module de règles et le module de schéma du projet (dans SP2C ils importent `sp2c.acl_rules` et `sp2c.schema` en tête de fichier : ces importations disparaissent).

- [ ] **Étape 1 : tests** : `test_premiere_regle_qui_tranche_gagne`, `test_ressource_precise_avant_generale`, `test_droit_refuse_par_defaut`, `test_formule_lookuprecords`, `test_formule_now_fige_par_maintenant`, `test_colonne_formule_par_defaut_selon_type`, `test_helpers_n_importent_aucun_module_de_projet` (importer `grist_kit.testing` dans un interpréteur vierge sans `sp2c` ni `schema` en chemin réussit).
- [ ] **Étape 2 : lancer → FAIL.**
- [ ] **Étape 3 : porter** `SP2C/sp2c/tests/acl.py` et `formules.py` en ajoutant les paramètres `regles_module` et `schema_module`.
- [ ] **Étape 4 : lancer → PASS.**
- [ ] **Étape 5 : commit** — `✅ TEST: simulateur d'ACL et formules en mémoire`.

### Tâche 5 : `inliner`

**Fichiers :** Créer `grist_kit/inliner.py`, `tests/test_inliner.py`.

**Interfaces :**
- Produit : `MARQUEURS` (regex `/* === CORE BEGIN === */ … /* === CORE END === */`) ; `inliner(page: Path, core: str, check: bool) -> bool` (vrai si à jour) ; `inliner_tout(core_path: Path, pages: list[Path], check: bool) -> bool`.

- [ ] **Étape 1 : tests** : `test_recopie_le_core_entre_marqueurs`, `test_check_ne_modifie_rien_et_renvoie_faux_si_ecart`, `test_marqueurs_absents_renvoie_faux`, `test_core_avec_antislashs_intact` (régression : `re.sub` interprète `\`).
- [ ] **Étape 2 : lancer → FAIL.** **Étape 3 : porter** `SP2C/outils_grist/inliner.py` en paramétrant core et pages. **Étape 4 : PASS.**
- [ ] **Étape 5 : commit** — `✨ FEAT: inliner du core JS`.

### Tâche 6 : journal des versions et `CHANGELOG`

**Fichiers :** Créer `grist_kit/versions.py`, `tests/test_versions.py`.

**Interfaces :**
- Produit : `lire_journal(html_ou_js: str) -> list[dict]` (JSON entre `/* VERSIONS BEGIN */` et `/* VERSIONS END */`, chaque entrée `{version, date, notes:[{texte, widgets}]}`) ; `lignes_changelog(journal) -> list[dict]` (`version`, `date`, `notes`) ; `changelog_md(journal) -> str` ; `synchroniser(client, lignes, dry_run=False) -> list[str]` (versions créées ou mises à jour dans la table `CHANGELOG`, jamais supprimées) ; `notes_du_widget(journal, widget) -> list`.

- [ ] **Étape 1 : tests** : `test_journal_lu_entre_marqueurs`, `test_synchroniser_cree_puis_est_idempotent`, `test_synchroniser_met_a_jour_une_note_modifiee`, `test_jamais_de_suppression`, `test_changelog_md_stable` (deux appels identiques), `test_notes_filtrees_par_widget`.
- [ ] **Étape 2 : FAIL.** **Étape 3 : porter** `etude_projet_grist/versions.py` et `SP2C/sp2c/widgets.py:changelog`. **Étape 4 : PASS.**
- [ ] **Étape 5 : commit** — `✨ FEAT: journal des versions et table CHANGELOG`.

### Tâche 7 : `creer_page`

**Fichiers :** Créer `grist_kit/pages.py`, `tests/test_pages.py`.

**Interfaces :**
- Produit : `creer(client, config: dict, nom: str, table_id: str, titre: str, acces: str="full") -> dict` (entrée de `widgets.json` : `fichier`, `table_ref`, `table_id`, `section_id`, `view_ref`, `acces` ; consigne aussi `config["doc_id"] = client.doc_id` si vide) ; idempotent ; `options_section(acces) -> str` ; `charger_config(chemin) -> dict` et `ecrire_config(chemin, config)`.

- [ ] **Étape 1 : tests** : `test_cree_page_et_section_puis_consigne`, `test_deuxieme_appel_ne_cree_rien`, `test_table_inconnue_message_clair`, `test_acces_invalide_refuse` (hors `read table` / `full`), `test_doc_id_consigne_a_la_premiere_creation`, `test_creer_sur_un_autre_doc_que_celui_de_widgets_json_refuse`.
- [ ] **Étape 2 : FAIL.** **Étape 3 : porter** `SP2C/outils_grist/creer_page.py` (chemins paramétrés, plus de `sys.path`). **Étape 4 : PASS.**
- [ ] **Étape 5 : commit** — `✨ FEAT: création de page de widget`.

### Tâche 8 : `deployer`, profil `dsfr`

**Fichiers :** Créer `grist_kit/deployer.py`, `tests/test_deployer.py`.

**Interfaces :**
- Consomme : `GristClient`, `SessionFactice` (tâche 1), `charger_config` (tâche 7).
- Produit : `separer_html_et_js(contenu: str) -> tuple[str, str]` ; `chargeur(js: str) -> str` (JS déposé en base64, contourne le pare-feu) ; `corps_patch(section_id, options, vue, attendu) -> str` ; `ouvrir_session(client)` (GET initial pour les cookies du pare-feu) ; `section_du_widget(config, nom) -> dict` ; `synchroniser_champs(client, table_ref, section_id) -> list[str]` ; `verifier_section(client, config, nom) -> None` (refuse, avec un message qui cite `creer-page`, si le document courant ne porte pas la section de `widgets.json`, si cette section n'est pas liée à la table du widget, si elle n'est pas un widget personnalisé, ou si `config["doc_id"]` ≠ `client.doc_id`) ; `deployer(client, config, nom: str, racine: Path, check: bool=False, session=None) -> int` (0 = à jour/déposé, 1 = écart en mode `check` ; appelle d'abord `verifier_section`).

- [ ] **Étape 1 : tests** : `test_separe_html_et_js`, `test_widget_a_jour_renvoie_0`, `test_ecart_en_check_renvoie_1_sans_ecrire`, `test_depot_relit_et_verifie`, `test_section_absente_message_clair` (cite `creer-page`), `test_section_d_un_autre_widget_refusee` (même id, autre table : aucune écriture), `test_doc_different_de_widgets_json_refuse`, `test_colonne_ajoutee_declaree_dans_la_section`, `test_ecriture_non_conforme_leve_erreur`, `test_refus_403_message_pare_feu` (point de focus 5).
- [ ] **Étape 2 : FAIL.** **Étape 3 : porter** `SP2C/outils_grist/deployer.py` ; la logique de `main()` devient `deployer(...)` ; porter `_verifier_section` de `SP2C/sp2c/widgets.py` en `verifier_section` (sans `schema.PAGES_PAR_WIDGET` : la table attendue vient de `config["widgets"][nom]["table_id"]`). **Étape 4 : PASS.**
- [ ] **Étape 5 : commit** — `✨ FEAT: déploiement des widgets DSFR`.

### Tâche 9 : `deployer`, profil `ui-kit` (bundle gzip)

**Fichiers :** Modifier `grist_kit/deployer.py` ; Créer `grist_kit/build_uikit.py`, `tests/test_deployer_uikit.py`.

**Interfaces :**
- Produit : `chargeur_gzip(js: str) -> str` (gzip niveau 9, `mtime=0`, base64, décompressé par `DecompressionStream` ; sortie stable) ; `construire(widgets_ui: Path, entrees: list[str]|None=None) -> dict[str,int]` (lance `npm ci` puis `node build.mjs`, renvoie la taille en Ko par entrée ; erreur claire si `node` < 20 ou absent) ; `deployer_uikit(client, config, nom, widgets_ui: Path, check=False, session=None) -> int` ; constante `LIMITE_API_OCTETS = 1_000_000`.

- [ ] **Étape 1 : tests** : `test_chargeur_gzip_aller_retour` (décompression Python de la charge == js d'origine), `test_chargeur_gzip_deterministe`, `test_bundle_trop_gros_refuse_avec_message` (au-delà de `LIMITE_API_OCTETS` après compression : message explique 413 et propose de réduire le bundle, point de focus 5), `test_node_absent_message_clair`, `test_check_compare_au_dist`.
- [ ] **Étape 2 : FAIL.** **Étape 3 : porter** `chargeur_gzip` et le dépôt de `etude_projet_grist/deployer_widgets.py` en réutilisant `corps_patch` et `ouvrir_session`. **Étape 4 : PASS.**
- [ ] **Étape 5 : commit** — `✨ FEAT: déploiement des widgets ui-kit (bundle gzip)`.

### Tâche 10 : CLI `python -m grist_kit` et configuration du projet

**Fichiers :** Créer `grist_kit/__main__.py`, `grist_kit/projet.py`, `tests/test_cli.py`.

**Interfaces :**
- Produit : `charger_projet(racine: Path) -> Projet` lit `.grist-driven.json` (`version`, `app`, `package`, `design_system` ∈ {`dsfr`,`ui-kit`}, `widgets_dir`, `core`) et importe `<package>.schema` et `<package>.acl_rules` ; sous-commandes `apply-schema`, `maj-formules`, `apply-acl [--prune]`, `amorcer`, `creer-page <widget> <table> --titre T [--acces]`, `deployer <widget> [--check]`, `inliner [--check]`, `versions` ; options communes `--dry-run`, `--doc <id>` (défaut `GRIST_DOC_ID`) ; `amorcer` appelle `<package>.amorcer.executer(client, dry_run)` s'il existe, sinon dit qu'il n'y a rien à faire ; chargement de `.env` par `python-dotenv`.

- [ ] **Étape 1 : tests** (sur un projet temporaire avec `ClientFactice` injecté) : `test_apply_schema_sans_doc_dit_quoi_faire` (message cite `GRIST_DOC_ID`, code 1), `test_dry_run_n_ecrit_rien_pour_chaque_sous_commande`, `test_design_system_inconnu_refuse`, `test_amorcer_absent_n_echoue_pas`, `test_deployer_choisit_le_profil_selon_design_system`.
- [ ] **Étape 2 : FAIL.** **Étape 3 : implémenter** `argparse` avec sous-commandes. **Étape 4 : PASS.**
- [ ] **Étape 5 : commit** — `✨ FEAT: CLI grist_kit`.

---

## Phase B — installeur et gabarit de projet

Tests d'installeur : `bash tests/installer/run.sh` (scripts bash, répertoires temporaires, **binaires factices** `pipx`/`uv`/`gh`/`claude` placés en tête de `PATH`, aucun accès réseau). Un jeu de contenu minimal de test vit dans `tests/fixtures/payload/` (une commande, un skill, un gabarit) pour ne pas dépendre de la phase C.

### Tâche 11 : `install.sh` — modes, prérequis, questionnaire

**Fichiers :** Créer `install.sh`, `src/lib/questions.sh`, `tests/installer/run.sh`, `tests/installer/test_questions.sh`.

**Interfaces :**
- Produit : `install.sh [init|update|doctor|uninstall] [--yes] [--dry-run] [--force]` ; drapeaux de réponse `--name`, `--api-host`, `--org`, `--design-system dsfr|ui-kit`, `--mcp existing|install|coder|none`, `--mcp-scope project|user`, `--doc-id`, `--git-flow|--no-git-flow`, `--hooks|--no-hooks`, `--ci|--no-ci` ; la clé d'API vient de `GRIST_API_KEY` dans l'environnement ou d'une saisie masquée, jamais d'un drapeau ; écrit `.grist-driven.json` (`version`, `app`, `package`, `design_system`, `api_host`, `mcp`, `mcp_scope`, `git_flow`, `hooks`, `ci`). Le questionnaire lit sur `/dev/tty`.
- Produit : codes de sortie `0` succès, `2` réponse manquante en non interactif, `3` prérequis manquant.

- [ ] **Étape 1 : tests** : `test_sans_terminal_ni_yes_echoue_code_2` (point de focus 1 : message « relancer avec --yes et --design-system »), `test_yes_sans_design_system_echoue_code_2`, `test_yes_avec_drapeaux_ecrit_grist_driven_json`, `test_prerequis_manquant_code_3` (python < 3.11 simulé, `git` absent), `test_dry_run_n_ecrit_aucun_fichier`, `test_design_system_invalide_refuse`, `test_la_cle_n_apparait_pas_dans_la_sortie_ni_les_fichiers_dry_run` (point 3).
- [ ] **Étape 2 : lancer → FAIL.**
- [ ] **Étape 3 : implémenter** les modes, la vérification des prérequis (git, python3.11+, gh si `--git-flow`, node ≥ 20 si `ui-kit`), le questionnaire (valeurs par défaut sauf design system) et `.grist-driven.json`.
- [ ] **Étape 4 : lancer → PASS.**
- [ ] **Étape 5 : commit** — `✨ FEAT: install.sh, modes et questionnaire`.

### Tâche 12 : pose du contenu, manifeste, mise à jour, désinstallation

**Fichiers :** Créer `src/lib/payload.sh`, `tests/installer/test_payload.sh` ; Modifier `install.sh`.

**Interfaces :**
- Consomme : `.grist-driven.json` (tâche 11).
- Produit : `payload_pose <source> <cible>` copie `commands/`, `skills/`, `agents/` dans `.claude/`, `lib/` dans `.grist/lib/`, `templates/` dans `./templates/` ; manifeste `.grist/manifest` (une ligne par fichier posé) ; baseline `.grist/templates.orig/` pour détecter les gabarits modifiés ; `update` ne touche pas aux fichiers hors manifeste ; `uninstall` retire seulement ce que le manifeste liste.

- [ ] **Étape 1 : tests** : `test_init_pose_commandes_skills_gabarits`, `test_update_ecrase_un_gabarit_non_modifie`, `test_update_preserve_un_gabarit_modifie_et_previent`, `test_force_ecrase_un_gabarit_modifie`, `test_update_ne_touche_pas_au_code_du_projet`, `test_uninstall_retire_seulement_le_manifeste`, `test_init_relance_est_idempotent` (point 2).
- [ ] **Étape 2 : FAIL.** **Étape 3 : implémenter** (logique de comparaison à la baseline écrite pour ce repo, pas copiée de driven). **Étape 4 : PASS.**
- [ ] **Étape 5 : commit** — `✨ FEAT: pose, mise à jour et désinstallation du contenu`.

### Tâche 13 : installation et déclaration du MCP

**Fichiers :** Créer `src/lib/mcp.sh`, `src/mcp/mcp.json.tpl`, `tests/installer/test_mcp.sh` ; Modifier `install.sh`.

**Interfaces :**
- Produit : `mcp_detecter -> existing|absent` (binaire `mcp-server-grist` dans `PATH`, ou entrée `grist` dans `.mcp.json`, ou dans `claude mcp list`) ; `mcp_installer` (ordre : `pipx install`, `uv tool install`, puis `pip install --user` sauf si Python « externally managed » ; version `MCP_SERVER_GRIST_VERSION=0.2.2`, à confirmer par l'étape 3) ; `mcp_declarer project|user` (`.mcp.json` sans secret, ou `claude mcp add --scope user`) ; en cas d'échec ou de refus : message avec la commande à lancer, **sortie 0** ; `grist-coder` : seule la déclaration HTTP est posée, avec la mise en route affichée.

- [ ] **Étape 1 : tests** : `test_deja_installe_ne_reinstalle_pas`, `test_installe_avec_pipx_puis_declare_dans_mcp_json`, `test_repli_uv_si_pas_de_pipx`, `test_pep668_sans_outils_affiche_la_commande_et_continue` (point 4), `test_refus_n_installe_rien`, `test_mcp_json_ne_contient_que_des_variables` (`${GRIST_API_KEY}`, `${GRIST_API_HOST}`, aucune valeur littérale, point 3), `test_portee_utilisateur_appelle_claude_mcp_add`, `test_option_none_ne_pose_rien`, `test_update_aligne_la_version_du_mcp_sur_l_epinglage` (version installée ≠ `MCP_SERVER_GRIST_VERSION` : réinstalle avec accord ; identique : ne fait rien).
- [ ] **Étape 2 : FAIL.**
- [ ] **Étape 3 : vérifier la version à épingler sans rien installer sur la machine** : `uvx --from mcp-server-grist==0.2.2 mcp-server-grist --help` (ou `pipx run`) ; vérifier dans le code de cette version qu'elle lit bien `GRIST_API_KEY` et `GRIST_API_HOST` (le modèle `.mcp.json` en dépend, connus seulement par des configs en 0.1.0) ; si elle ne démarre pas ou lit d'autres variables, épingler la version la plus récente qui convient et le consigner dans `CHANGELOG.md`.
- [ ] **Étape 4 : implémenter.** **Étape 5 : PASS.**
- [ ] **Étape 6 : commit** — `✨ FEAT: installation du MCP Grist`.

### Tâche 14 : gabarit de projet (commun, `dsfr`, `ui-kit`) et environnement

**Fichiers :** Créer `src/scaffold/common/…`, `src/scaffold/dsfr/…`, `src/scaffold/ui-kit/…`, `src/lib/scaffold.sh`, `tests/installer/test_scaffold.sh`, `tests/test_projet_genere.py`.

**Interfaces :**
- Produit : fichiers génériques posés par `init` avec substitution de `{{app}}` et `{{package}}` : `schema.py` et `acl_rules.py` (données pures, une table d'exemple), `<package>/amorcer.py` (optionnel, vide commenté), `widgets.json` (`{"doc_id": null, "widgets": {}}`), `tests/` (utilisent `grist_kit.testing`), `.env.example` (`GRIST_API_KEY=`, `GRIST_API_HOST=`, `GRIST_DOC_ID=`), `AGENTS.md`, `CLAUDE.md` (`@AGENTS.md`), `.github/workflows/ci.yml` (si `--ci`) ; profil `dsfr` : `widgets/exemple.html` (marqueurs CORE, DSFR 1.14.4 en version exacte) + `widgets/core.js` + `tests/core.test.js` ; profil `ui-kit` : `widgets_ui/` (`package.json` avec `@gouvfr-lasuite/ui-components`, `build.mjs`, `vite.config.ts`, `src/exemple.tsx`). `.env` : créé seulement s'il n'existe pas, `chmod 600`, après vérification que `.gitignore` l'ignore ; `.venv` créé et `grist-kit` installé depuis le tag git (`GRIST_KIT_SPEC`, surchargeable pour les tests par un chemin local).

- [ ] **Étape 1 : tests bash** : `test_env_existant_jamais_reecrit` (point 2), `test_env_cree_ignore_par_git_avant_ecriture` (point 3), `test_substitution_app_et_package`, `test_profil_dsfr_pose_widgets_html`, `test_profil_uikit_pose_widgets_ui`, `test_scaffold_relance_n_ecrase_pas_les_fichiers_du_projet`.
- [ ] **Étape 2 : test d'intégration** `tests/test_projet_genere.py` : pour chacun des deux profils, `install.sh init --yes … ` dans un répertoire temporaire avec `GRIST_KIT_SPEC` pointant vers `packages/grist-kit`, puis `pytest` **dans le projet généré** doit passer ; `python -m grist_kit apply-schema --dry-run` du projet généré, avec un client factice, ne lève rien.
- [ ] **Étape 3 : FAIL.** **Étape 4 : écrire le gabarit** (contenu minimal fonctionnel ; l'exemple de widget affiche la liste d'une table). **Étape 5 : PASS.**
- [ ] **Étape 6 : commit** — `✨ FEAT: gabarit de projet DSFR et ui-kit`.

### Tâche 15 : hooks git, flux `main`/`next`, tableau, CI

**Fichiers :** Créer `src/hooks/pre-commit`, `src/hooks/pre-push` (ils appellent `src/hooks/grist-gate.sh`, créé par la tâche 18 ; ici testés avec un `grist-gate.sh` factice), `src/lib/gitflow.sh`, `tests/installer/test_gitflow.sh` ; Modifier `install.sh`.

**Interfaces :**
- Produit : `gitflow_init` (crée `next` depuis `main` si absent, sans toucher à l'existant) ; `hooks_poser` (copie dans `.git/hooks/`, refuse d'écraser un hook étranger sans `--force`) ; hook pré-commit : refuse de commiter `.env` ou un motif de clé (`GRIST_API_KEY=` avec valeur) et lance `pytest -q` rapide si `--hooks` ; tableau GitHub créé via `gh` seulement si `git_flow` vrai et `gh auth status` réussit, sinon message.

- [ ] **Étape 1 : tests** : `test_hook_refuse_env_dans_l_index`, `test_hook_refuse_cle_en_clair`, `test_hook_etranger_non_ecrase`, `test_next_cree_sans_toucher_main`, `test_sans_gh_connecte_continue_avec_message`.
- [ ] **Étape 2 : FAIL.** **Étape 3 : implémenter.** **Étape 4 : PASS.**
- [ ] **Étape 5 : commit** — `✨ FEAT: hooks git, flux main/next et CI`.

### Tâche 16 : `doctor`

**Fichiers :** Créer `src/lib/doctor.sh`, `tests/installer/test_doctor.sh` ; Modifier `install.sh`.

**Interfaces :**
- Produit : `install.sh doctor` affiche, ligne à ligne et avec `OK`/`KO` : versions (installeur, `grist-kit`, MCP), présence de `.env` et des trois variables (sans afficher la clé), accès à l'API Grist (`GET /docs/<id>/tables`, ignoré avec message si pas de document), présence de l'entrée MCP, cohérence du manifeste ; code de sortie 1 s'il y a un `KO`.

- [ ] **Étape 1 : tests** (serveur HTTP factice local en `python -m http.server`) : `test_tout_ok_code_0`, `test_cle_absente_ko_sans_afficher_de_valeur`, `test_api_injoignable_ko_message`, `test_mcp_manquant_ko_avec_commande`.
- [ ] **Étape 2 : FAIL.** **Étape 3 : implémenter.** **Étape 4 : PASS.**
- [ ] **Étape 5 : commit** — `✨ FEAT: install.sh doctor`.

---

## Phase C — contenu `grist-*`

Tests de contenu : `python -m pytest tests/content -q`. Source de lecture : `~/Developpeur/ai-driven-dev/src/` (lecture seule). Règle : on **réécrit** ; on ne copie pas un fichier proche de killer-saas (tâche 17 le mesure).

### Tâche 17 : audit de provenance

**Fichiers :** Créer `scripts/provenance.py`, `tests/content/test_provenance.py`, `docs/provenance.md` (généré).

**Interfaces :**
- Produit : `normaliser(texte: str) -> str` (remplace les préfixes `ks-`, `dm-` et `grist-` par un jeton commun, supprime les espaces superflus) ; `similarite(a: str, b: str) -> float` (`difflib.SequenceMatcher` sur les textes normalisés) ; `auditer(driven: Path, amont: dict[str,str], seuil: float=0.5) -> list[tuple[str,float,str,str]]` (chemin driven, meilleur rapport, chemin amont le plus proche, verdict `reecrire`|`libre`) ; `charger_amont(depot: Path) -> dict[str,str]` lit **tous** les fichiers du dernier commit de Mike Codeur dans le dépôt git de `ai-driven-dev` (`git log --author="Mike Codeur"` ; le premier commit de Bruno suit ce commit ; `git show <commit>:<chemin>`).
- Chaque fichier de driven est comparé à **chaque** fichier amont (les préfixes amont étaient `ks-*`, rebrandés `dm-*` : une recherche par chemin raterait les fichiers renommés) ; le meilleur rapport décide.

- [ ] **Étape 1 : tests** : `test_fichiers_identiques_rapport_1`, `test_fichier_reecrit_sous_le_seuil_est_libre`, `test_fichier_renomme_reste_detecte` (même contenu, préfixe `ks-` → `dm-`, chemin différent : verdict `reecrire`), `test_fichier_sans_equivalent_amont_est_libre`, `test_audit_liste_tous_les_fichiers_de_src`.
- [ ] **Étape 2 : FAIL.** **Étape 3 : implémenter** puis lancer sur `ai-driven-dev/src/` ; `docs/provenance.md` liste chaque fichier, son rapport, son plus proche équivalent amont et son verdict ; les fichiers `reecrire` forment la liste de travail des tâches 18 à 22. Bruno relit la liste avant la tâche 18.
- [ ] **Étape 4 : PASS.** **Étape 5 : commit** — `📝 DOCS: audit de provenance des fichiers de driven`.

### Tâche 18 : scripts du flux et hooks `grist-*`

**Fichiers :** Créer `src/lib/grist-board.sh`, `grist-config.sh`, `grist-version.sh`, `grist-wiki.sh`, `grist-init.sh`, `src/hooks/grist-gate.sh`, `tests/fixtures/gh-stub.sh`, `tests/content/test_lib.py`.

**Interfaces :** Reprennent le rôle des `dm-*.sh` de driven (tableau GitHub à statuts `backlog/ready/in progress/review/test/shipped`, configuration `.grist/config.json`, bump semver et section de changelog, publication du wiki, porte « plan validé » avant tout code sur `feature/<story>/<ticket>`). Chemin de configuration : `.grist/config.json` ; version : fichier `VERSION`.

- [ ] **Étape 1 : tests** (avec `gh-stub.sh`) : `test_bump_patch_minor_major_synchronise_changelog`, `test_porte_refuse_code_sans_plan_valide`, `test_porte_accepte_les_commits_de_docs`, `test_board_transition_interdite_refusee`, `test_aucun_reste_de_dm_dans_lib` (aucun `dm-`, `.dm/`).
- [ ] **Étape 2 : FAIL.** **Étape 3 : réécrire** les scripts d'après la liste de la tâche 17, renommés et simplifiés (pas de profils multi-cibles, pas de Codex/Grok). **Étape 4 : PASS.**
- [ ] **Étape 5 : commit** — `✨ FEAT: scripts du flux et porte de qualité`.

### Tâche 19 : commandes du pipeline (trois lots, un commit chacun)

**Lots :** **19a cadrage** (`prd`, `init`, `stories`, `stories-review`, `architect`, `design-system`) ; **19b par story** (`research`, `design`, `plan`, `docs`) ; **19c par ticket et livraison** (`execute`, `review`, `ship`, `release`, `feature`, `continue`, `status`, `help`, `orchestrator`). Les tests ci-dessous s'écrivent une fois (au lot 19a) et couvrent les fichiers présents ; chaque lot les relance.

**Fichiers :** Créer `src/commands/grist-{prd,init,stories,stories-review,architect,design-system,research,design,plan,docs,execute,review,ship,release,feature,continue,status,help,orchestrator}.md`, `tests/content/test_commands.py`.

**Interfaces :** Chaque commande : frontmatter `description`, `argument-hint`, `allowed-tools` ; mêmes phases et mêmes portes que driven, adaptées à Grist (voir spec §6.3). `grist-prd` : modes « nouveau projet » et « reprise » seulement ; gabarit PRD avec profils d'utilisateurs et volumétrie. `grist-architect` : produit `docs/architecture.md` avec sections *modèle de données*, *matrice ACL (profil × table × droit)*, *inventaire des widgets*, *règles en double (formule Grist + JS)*, *plan de déploiement*. `grist-init` : ne recrée pas le projet (c'est `install.sh`), il crée le tableau, le wiki, `VERSION`. `grist-release` : `next` → `main`, bump, tag, wiki ; ne déploie pas sur Grist (renvoie à `grist-deploy`).

- [ ] **Étape 1 : tests** : `test_chaque_commande_a_un_frontmatter_complet`, `test_aucune_reference_a_dm`, `test_toute_commande_citee_existe` (chaque `/grist-xxx` mentionné correspond à un fichier), `test_tout_skill_et_agent_cite_existe`, `test_nom_de_fichier_egal_au_nom_de_commande`, `test_prd_n_a_pas_de_mode_cloner_un_saas`.
- [ ] **Étape 2 : FAIL.** **Étape 3 : écrire les commandes du lot** (réécriture d'après `docs/provenance.md`). **Étape 4 : PASS.**
- [ ] **Étape 5 : commit** — `✨ FEAT: commandes grist-* (cadrage)`, puis `… (par story)`, puis `… (par ticket et livraison)`.

### Tâche 20 : nouvelles commandes Grist

**Fichiers :** Créer `src/commands/grist-{schema,acl,widget,deploy,recette,optimise}.md`, compléter `tests/content/test_commands.py`.

**Interfaces :**
- `grist-optimise` : mesure d'abord (volumétrie réelle ou jeu de données synthétique, temps de chargement et d'interaction des widgets, taille du bundle ui-kit), applique la checklist du skill `grist-perf`, ne change rien sans mesure avant/après, ajoute ou resserre une borne de performance dans les tests, consigne le gain dans `docs/revue-performance.md`.
- `grist-schema` : modifier `schema.py` puis `python -m grist_kit apply-schema --dry-run`, lecture du plan, application sur accord ; `grist-acl` : modifier `acl_rules.py` avec test du cas refusé (via `grist_kit.testing.acl.permis`), `apply-acl --dry-run` ; `grist-widget` : créer ou modifier un widget selon `design_system` de `.grist-driven.json` (profil `dsfr` : HTML + core + test node ; profil `ui-kit` : entrée React + build) ; `grist-deploy` : ordre `apply-schema` → `maj-formules` (`--dry-run` : la liste des `divergentes` se traite à la main) → `apply-acl` → `amorcer` → `creer-page` → `deployer`, version à demander avant déploiement, `--check` final ; `grist-recette` : liste d'essai en réel avec `?aclAsUser_=<adresse>` pour chaque profil de la matrice ACL.

- [ ] **Étape 1 : tests** : `test_grist_deploy_cite_l_ordre_exact` (avec `maj-formules` entre `apply-schema` et `apply-acl`), `test_grist_schema_cite_maj_formules_apres_un_changement_de_formule`, `test_grist_schema_et_acl_imposent_dry_run_d_abord`, `test_grist_widget_distingue_les_deux_profils`, `test_grist_recette_cite_aclasuser`, `test_aucune_commande_n_ecrit_la_structure_via_le_mcp` (mention explicite d'interdiction), `test_grist_optimise_exige_une_mesure_avant_et_apres`, `test_grist_optimise_cite_le_skill_grist_perf`.
- [ ] **Étape 2 : FAIL.** **Étape 3 : écrire.** **Étape 4 : PASS.**
- [ ] **Étape 5 : commit** — `✨ FEAT: commandes grist-schema, acl, widget, deploy, recette`.

### Tâche 21 : skills

**Fichiers :** Créer `src/skills/grist-{schema,acl,widget,deploy,recette,mcp,perf}/SKILL.md`, `src/skills/grist-{agentic-stories,codebase-analysis,quality-bar,stories-review,tdd}/SKILL.md`, `tests/content/test_skills.py`.

**Contenu imposé :** `grist-schema` : `isFormula` des colonnes de données ajoutées à une table existante, renommage de `colId` par `PATCH …/columns`, ids de lignes réutilisés, pas de ligne orpheline ; `grist-acl` : pas de `rec.X.Y`, `newRec` compte la ligne en cours d'insertion (tester l'inconnu qui s'ajoute), lots évalués sur l'état d'avant, colonnes `-R`, étiquette `[<app>:<ressource>#<n>]`, un test par règle y compris le refus ; `grist-widget` : règle en deux endroits, une section par profil (`dsfr` : ordre des feuilles, interdits `style=""`, `innerHTML`, `alert()` ; `ui-kit` : composants, bundle gzip, limite 1 Mo) ; `grist-deploy` : ordre, `--dry-run`, pare-feu 403 (motifs de piratage même dans une donnée), version avant déploiement ; `grist-recette` : essai en réel par profil ; `grist-mcp` : le MCP lit, explore, manipule les données, **jamais la structure** ; `grist-perf` : mesurer avant et après ; widgets (un seul chargement, pagination à 50 lignes, `Intl` et collateurs construits une fois, index `Map` plutôt que `find` dans un tri, saisie différée 250 ms, DSFR en version exacte pour le cache) ; ui-kit (taille du bundle sous `LIMITE_API_OCTETS` après gzip, chargement différé, cache `react-query`) ; formules (`lookupRecords` en colonne sur grosse table, `NOW()` qui recalcule, colonnes calculées inutiles) ; ACL (règles évaluées par ligne, pas de lecture croisée coûteuse) ; API (écritures groupées par `/apply`, lots découpés devant le pare-feu) ; bornes larges dans les tests de performance. Le skill `grist-quality-bar` reprend ces critères pour `grist-review`. Sources des pièges et de la performance : `SCIP_grist/docs/revue-performance-widgets.md`, section « Performance » de `SP2C/CLAUDE.md`, `SP2C/CLAUDE.md`, `SCIP_grist/CLAUDE.md`, `SCIP_grist/docs/pieges.md`, `sirpa/docs/wiki/Pieges-Grist.md`.

- [ ] **Étape 1 : tests** : `test_frontmatter_name_egal_dossier`, `test_description_commence_par_un_verbe_et_dit_quand_l_utiliser`, `test_chaque_piege_obligatoire_est_cite` (une liste de motifs par skill : `isFormula`, `colId`, `newRec`, `rec\.`, `403`, `aclAsUser_`, `jamais la structure`, et pour `grist-perf` : `Intl`, `Map`, `lookupRecords`, `NOW`, `/apply`, `avant et après`), `test_quality_bar_cite_les_criteres_de_performance`, `test_aucune_reference_a_dm`.
- [ ] **Étape 2 : FAIL.** **Étape 3 : écrire** les 11 skills (`grist-mcp` ≤ 1 page). **Étape 4 : PASS.**
- [ ] **Étape 5 : commit** — `✨ FEAT: skills Grist et skills de méthode`.

### Tâche 22 : agents et gabarits de documents

**Fichiers :** Créer `src/agents/{implementer,reviewer,stories-reviewer,worktree-manager}.md`, `src/templates/{prd,architecture,stories,plan,research,adr,review-checklist,stories-review-checklist,product-doc,design-brief,design-system}.md`, `tests/content/test_templates.py`.

**Interfaces :** Gabarits `prd.md` et `architecture.md` enrichis comme en tâche 19 ; `design-system.md` a deux variantes de contenu (`dsfr`, `ui-kit`) choisies par `grist-design-system` d'après `.grist-driven.json`.

- [ ] **Étape 1 : tests** : `test_architecture_a_les_cinq_sections_grist`, `test_prd_a_profils_et_volumetrie`, `test_agents_ont_un_frontmatter`, `test_aucune_reference_a_dm`, `test_les_gabarits_cites_par_les_commandes_existent`.
- [ ] **Étape 2 : FAIL.** **Étape 3 : écrire.** **Étape 4 : PASS.**
- [ ] **Étape 5 : commit** — `✨ FEAT: agents et gabarits de documents`.

### Tâche 23 : CI du repo, documentation, parcours de bout en bout, v0.1.0

**Fichiers :** Créer `.github/workflows/ci.yml`, `RELEASING.md`, `CHANGELOG.md` ; Modifier `README.md` ; Créer `tests/e2e/test_init_complet.sh`.

**Interfaces :** CI : `pytest` du kit, `bash tests/installer/run.sh`, `pytest tests/content` ; aucun secret. `README.md` : installation en une ligne, les huit questions, les deux design systems, le tableau des commandes. `RELEASING.md` : vérifier, `bump`, changelog, tag `v0.1.0`, `gh release create`.

- [ ] **Étape 1 : test e2e** `test_init_complet.sh` : pour `dsfr` puis `ui-kit`, dans un répertoire vierge, `install.sh init --yes --name demo --design-system <p> --mcp none --no-git-flow --no-hooks --ci` avec `GRIST_KIT_SPEC` local ; vérifier la présence de `.claude/commands/grist-prd.md`, `.grist-driven.json`, `.env.example`, absence de `.env` rempli, puis `install.sh doctor` (client factice) et le `pytest` du projet généré.
- [ ] **Étape 2 : lancer l'ensemble** — `pytest`, `bash tests/installer/run.sh`, `bash tests/e2e/test_init_complet.sh` → tout PASS.
- [ ] **Étape 3 : relecture du dépôt** : `grep -rEn "dm-|\.dm/|BarthGve/(SP2C|scip)|[A-Za-z0-9]{22}" .` ne trouve ni reste de driven, ni nom de client, ni identifiant de document (dépôt public).
- [ ] **Étape 4 : documentation et changelog** : rédiger `README.md` et la section `0.1.0` de `CHANGELOG.md` ; la version reste `0.1.0` (aucun bump).
- [ ] **Étape 5 : commit** — `🔖 RELEASE: 0.1.0`, puis tag `v0.1.0` (la publication sur GitHub reste à la main de Bruno).
