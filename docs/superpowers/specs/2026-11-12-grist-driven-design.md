# grist-driven — design

Statut : à valider (v2, après relecture de Bruno) · date : 2026-11-12 · nom du repo provisoire (`grist-driven`)

## 1. Intention et pourquoi

Bruno construit plusieurs applications Grist pour différents clients. Neuf dépôts
(SP2C, SCIP_grist, ST_parcours-managerial, nanterre-grist-projet, ppn_grist, sirpa,
portfolio_grist, etude_projet_grist, instances_DOE_grist) suivent le même squelette,
mais chacun **recopie à la main** `outils_grist/` (~930 lignes). Les copies divergent
déjà : `grist_client` en 2 variantes, `apply_acl` en 3, `apply_schema` en 4. Chaque
`CLAUDE.md` (60 à 310 lignes) répète les mêmes pièges Grist.

Ce repo est **mis à la disposition d'équipes** : une équipe l'installe **en une ligne de
commande** dans un projet et obtient, sans rien recopier, les outils pour construire une
application Grist proprement, et des commandes `grist-*` qui disciplinent l'agent IA
(PRD, architecture, fonctionnalités, schéma, ACL, widgets, déploiement).

## 2. Décision structurante (Bruno, 2026-11-12)

Le repo est **autonome** : il intègre et adapte les commandes, skills, agents, scripts et
hooks pertinents du repo `ai-driven-method` (« driven ») au lieu de s'installer au-dessus.
Les commandes s'appellent `grist-*`. Bruno **assume la divergence avec driven** et
maintient ce repo seul ; il n'y a ni dépendance à driven ni version de driven épinglée.

## 3. Objectifs, non-objectifs, anti-objectifs

**Objectifs**
- Une installation en une ligne (`curl … | bash` à la racine du projet) ; une mise à jour en une commande.
- Une bibliothèque Python versionnée (`grist-kit`) à la place des copies d'`outils_grist/`.
- Un pipeline `grist-*` complet, du PRD à la release, pensé pour Grist.
- Un projet généré qui applique d'emblée la méthode : schéma et ACL déclaratifs, scripts
  idempotents avec `--dry-run`, widgets HTML d'un seul fichier, règles métier en double
  (formule Grist + JS) avec tests, journal des versions.
- Un MCP Grist configuré par défaut, sans secret dans le dépôt.

**Non-objectifs**
- Rester compatible avec driven ou suivre ses évolutions.
- Les cibles Codex et Grok de driven (v0.1 : Claude Code seul ; le build Node md→skills n'est pas repris).
- Porter les 9 dépôts existants (chantier ultérieur, dépôt par dépôt).
- Héberger Grist ou gérer les comptes/clés des équipes.

**Anti-objectifs** (échec même si ça « marche »)
- Le kit redevient une dépendance qu'on recopie : toute équipe peut le mettre à jour.
- Une équipe ne comprend pas la méthode sans lire 300 lignes de `CLAUDE.md`.
- Une clé d'API ou un identifiant de document de production fini dans un dépôt.
- On reprend de driven des commandes dont Grist n'a pas besoin, qui alourdissent le pipeline.

## 4. Contraintes

- **Licence et attribution** : driven est un fork de killer-saas (Mike Codeur) dont la
  licence en amont est absente ; les fichiers hérités ne sont pas relicensés (voir son `NOTICE`).
  Bruno a **réécrit une grande partie** de killer-saas : tout ce qu'il a réécrit ou ajouté se reprend
  librement. Le constructeur compare chaque fichier de driven à killer-saas ; tout fichier resté
  proche de l'original est **réécrit** avant d'entrer dans ce repo public. Un `NOTICE` rappelle la filiation.
- Python ≥ 3.11 ; dépendances minimales (`requests`, `python-dotenv`, `pytest`).
- Installeur en bash pur (pas de Node requis pour installer). Node ≥ 20 n'est requis que pour les widgets du design system ui-kit.
- **Design system à choisir à l'installation, sans défaut : DSFR ou La Suite ui-kit** (`suitenumerique/ui-kit`, paquet `@gouvfr-lasuite/ui-components`). Deux profils de widgets, voir 6.5.
- Secrets dans `.env` (jamais commité) ; `.mcp.json` lit les variables d'environnement.
- Dépôt **public** : aucun identifiant de document, clé, nom de client ni donnée réelle ; exemples et tests neutres ; CI sans secret.
- Contexte des équipes visées : administrations utilisant grist.numerique.gouv.fr.

## 5. Approches envisagées

- **A. Couche au-dessus de driven** : première option retenue, puis abandonnée par Bruno au profit d'A′ (dépendance à driven, deux installations, gabarits à surcharger).
- **A′. Repo autonome qui intègre et adapte driven** (retenue) : un seul installeur, un seul jeu de commandes `grist-*`, une seule version. Coût assumé : divergence avec driven et maintenance par Bruno.
- **B. Fork de driven** : même effet qu'A′ mais en gardant l'historique et le nom `dm-*` ; écartée, car Bruno veut des commandes `grist-*` et un repo public indépendant.
- **C. Gabarit GitHub + package pip** : les skills et la méthode ne se mettent pas à jour, la dérive revient. Écartée.

## 6. Conception

### 6.1 Contenu du repo

```
grist-driven/
├── install.sh                  une ligne : init | update | doctor | uninstall (bash pur)
├── VERSION, CHANGELOG.md, NOTICE
├── packages/grist-kit/         bibliothèque Python (pip, versionnée)
│   └── grist_kit/              client, schema, acl, inliner, deployer, pages,
│                               versions (CHANGELOG), testing/ (faux_grist, simulateur ACL,
│                               formules en mémoire)
├── src/commands/               grist-*.md (voir 6.3)
├── src/skills/                 savoir Grist + méthode (voir 6.4), préfixe grist-
├── src/agents/                 implementer, reviewer, stories-reviewer, worktree-manager (adaptés)
├── src/lib/                    scripts du flux : tableau, config, version, wiki, init (adaptés)
├── src/hooks/                  pre-commit, pre-push (adaptés) + contrôles Grist
├── src/templates/              prd, architecture, stories, plan, adr… enrichis Grist
├── src/scaffold/               fichiers générés par `init` (voir 6.5)
├── src/mcp/                    modèle de .mcp.json
└── tests/
```

### 6.2 Installation

Une ligne, à la racine du projet :
`curl -fsSL https://raw.githubusercontent.com/<org>/grist-driven/main/install.sh | bash`.
`init` vérifie les prérequis (git, python3.11+, gh), **pose des questions**, puis pose commandes, skills, agents, lib,
hooks, gabarits, crée `.venv`, installe `grist-kit` à la version du dépôt (tag git), génère le gabarit de projet,
`.mcp.json` et `.env.example`, et **installe le MCP s'il manque** (voir 6.7). `update` met à jour tout sauf le code du
projet et préserve les gabarits modifiés localement. `doctor` vérifie versions, `.env`, accès à l'API Grist et connexion MCP.

**Questions posées à l'installation** (lues sur le terminal même en `curl … | bash` ; chacune a une réponse par défaut,
un drapeau équivalent et `--yes` pour tout accepter sans interaction) :
1. Nom de l'application et du dépôt.
2. Instance Grist : adresse de l'API (défaut `https://grist.numerique.gouv.fr/o/<org>/api`) et organisation.
3. Design system des widgets : **DSFR** ou **La Suite ui-kit** (pas de défaut ; obligatoire, `--design-system dsfr|ui-kit` en mode `--yes`). Le choix est consigné dans `.grist-driven.json` et pilote le gabarit, les skills et le déployeur.
4. MCP Grist : déjà installé / l'installer (`mcp-server-grist`, défaut) / `grist-coder` / aucun ; portée : ce projet (`.mcp.json`) ou toute la machine (utilisateur).
5. Clé d'API : la saisir maintenant (écrite dans `.env`, ignoré par git) ou plus tard ; jamais écrite ailleurs ni affichée.
6. Identifiant du document Grist de travail (facultatif, dans `.env`).
7. Flux git `main`/`next` et tableau GitHub (nécessite `gh auth`) : oui/non.
8. Hooks git et workflow CI : oui/non.
`--dry-run` affiche tout ce qui serait fait sans rien écrire ; relancer `init` ne casse rien (idempotent).

### 6.3 Commandes (reprises de driven, adaptées, renommées)

| Commande `grist-*` | Origine / rôle |
|---|---|
| `prd`, `init`, `stories`, `stories-review`, `architect`, `design-system` | cadrage une fois par produit ; PRD et architecture enrichis Grist (profils, volumétrie, modèle de données, **matrice ACL** profil × table × droit, inventaire des widgets, règles en double, plan de déploiement) ; `init` crée aussi le projet |
| `research`, `design`, `plan`, `docs` | par story (branche `feature/<story>`, docs seulement) |
| `execute`, `review`, `ship` | par ticket (branche `feature/<story>/<ticket>`, un commit, une PR vers `next`) |
| `release`, `feature`, `continue`, `status`, `help`, `orchestrator` | reprises de driven |
| **`schema`, `acl`, `widget`, `deploy`, `recette`, `optimise`** | **nouvelles** : écrire/changer le schéma, les ACL, un widget ; déployer ; recetter en réel ; **optimiser** (performance des widgets, formules, ACL et appels d'API ; sources : `SCIP_grist/docs/revue-performance-widgets.md`, règles de performance de `SP2C/CLAUDE.md`) |

Le flux git `main`/`next`, le tableau GitHub, le wiki et le semver de driven sont conservés (choix de l'auteur : Bruno les utilise déjà).
Les commandes de la ligne « nouvelles » appellent `grist-kit` et portent les règles du §6.4.

### 6.4 Skills

Savoir Grist (préfixe `grist-`) : `schema` (`isFormula`, renommage de `colId`, ids réutilisés), `acl` (`newRec`,
pas de `rec.X.Y`, test du cas refusé, étiquette `[app:<ressource>#<n>]`), `widget` (HTML d'un seul fichier, core inliné,
règle en deux endroits, DSFR, accessibilité), `deploy` (ordre apply_schema → apply_acl → amorcer → deployer, `--dry-run`,
pare-feu 403, version avant déploiement), `recette` (`?aclAsUser_=`, liste « à vérifier en réel »),
`mcp` (le MCP lit, explore et manipule les données ; **la structure passe par les scripts**, jamais par le MCP),
`perf` (optimisation : un seul chargement des données, pagination, formateurs `Intl` hors des boucles, index `Map`, saisie différée ; formules `lookupRecords`/`NOW()` coûteuses sur grosses tables ; coût des ACL ; écritures groupées par `/apply` ; taille du bundle ui-kit ; **mesurer avant et après**, avec des bornes larges dans les tests). Les critères de `perf` entrent aussi dans la barre de qualité de `grist-review`.
Skills de méthode repris de driven et adaptés : `agentic-stories`, `codebase-analysis`, `quality-bar`, `stories-review`, `tdd`.

### 6.5 Projet généré

Commun : `schema.py` et `acl_rules.py` (données pures), `widgets.json`, `tests/` (pytest), `docs/` (PRD, architecture, specs),
`.env.example`, `.grist-driven.json`, `AGENTS.md` (règles Grist courtes, renvoyant aux skills), `CLAUDE.md` d'une ligne `@AGENTS.md`,
workflow CI. Un seul module Python propre au projet ; plus aucune copie d'`outils_grist/`.

Deux **profils de widgets**, selon le design system choisi :
- **`dsfr`** : `widgets/` = un HTML d'un seul fichier par widget (DSFR 1.14, version exacte) + `core.js` inliné entre marqueurs ; tests `node:test` du cœur ; aucun Node pour déployer.
- **`ui-kit`** : `widgets_ui/` = application React/TypeScript construite par Vite (`vite-plugin-singlefile`), une entrée par widget, sortie `dist/<entrée>.html` ;
  les composants viennent de `@gouvfr-lasuite/ui-components`. Le bundle dépasse la limite de l'API Grist (413 vers 1 Mo) : le déployeur le dépose
  compressé (gzip + base64, décompressé par le navigateur). Modèle : `etude_projet_grist/widgets_ui` et `deployer_widgets.py`.

### 6.6 `grist-kit`

Extrait et réconcilié des dépôts. Source de vérité : `SP2C/outils_grist` et `SP2C/sp2c/tests/` (faux Grist, simulateur d'ACL,
formules) ; `refactor/deployeur-standard` (etude_projet_grist, instances_DOE_grist) pour le déployeur ;
`etude_projet_grist/versions.py` et `deployer_widgets.py` (journal des versions, chargeur gzip du profil `ui-kit`). Les autres variantes sont comparées par diff,
chaque écart est consigné ; Bruno n'arbitre que si deux comportements sont incompatibles.
Commandes : `python -m grist_kit apply-schema|maj-formules|apply-acl|amorcer|creer-page|deployer|inliner|versions`, toutes avec `--dry-run`
et `--doc <id>`, idempotentes. Distribution par tag git (dépôt public, sans jeton, pas de PyPI en v0.1).

### 6.7 MCP

Par défaut `mcp-server-grist` (stdio, paquet PyPI de nic01asFr ; Bruno en a la 0.1.0, la dernière est 0.2.2), avec
`${GRIST_API_KEY}` et `${GRIST_API_HOST}`. `grist-coder` (`gristcoder_mcp`, HTTP local, exploratoire) reste une option documentée.
**L'installation du MCP fait partie de la commande** : `init` détecte si le binaire est présent (PATH, `~/.claude.json`,
`.mcp.json`) ; sinon, avec l'accord de l'utilisateur, il l'installe isolé (`pipx` ou `uv tool`, à défaut `pip --user`), sans toucher
au Python du système, puis déclare le serveur (projet : `.mcp.json` ; machine : `claude mcp add --scope user`). Il vérifie ensuite
la connexion (`doctor`). Si l'installation échoue ou si l'utilisateur refuse, `init` continue et affiche la commande à lancer.
La version installée est fixée dans le repo (compatibilité testée) et la mise à jour passe par `update`.
Une équipe n'a pas à lancer de serveur pour démarrer ; `grist-coder` n'est installé que sur demande, avec sa mise en route
(serveur local, widget) expliquée.

### 6.8 Qualité et tests

CI fournie : `pytest`, `node --test`, `inliner --check` ; pas de déploiement automatique. La CI du kit n'utilise que le faux Grist
et le simulateur d'ACL. Les vérifications en réel (`doctor`, `?aclAsUser_=`, pièges d'ACL) forment une liste manuelle jouée par Bruno
sur un document de son choix, hors dépôt ; les écarts corrigent le simulateur (choix de l'auteur, Bruno n'a pas encore répondu).
Plate-formes de v0.1 : macOS et Linux, Claude Code.

## 7. Premier incrément (v0.1)

Dans le périmètre : `install.sh` (`init`, `update`, `doctor`), `grist-kit`, gabarit de projet, commandes `grist-*` (pipeline
complet et les cinq nouvelles), skills, agents, lib, hooks et gabarits adaptés, `.mcp.json`, workflow CI, tests du kit et de l'installeur,
**les deux profils de widgets (DSFR et La Suite ui-kit)**.
Hors périmètre : Codex et Grok, autres design systems (SCIP), portage des dépôts existants, `lint` de `schema.py`/`acl_rules.py`, déploiement automatique.

## 8. Laissé au constructeur

Nom définitif du repo, de l'organisation GitHub et du package ; liste exacte des fichiers de driven repris ou réécrits (d'après la
décision de licence, §4) ; API publique de `grist-kit` (après comparaison des variantes) ; texte des commandes, skills et gabarits ;
détail du workflow CI ; format du verrou de version.

## 9. Choix de l'auteur (à relire)

- Claude Code seul, macOS et Linux, en v0.1 (le build Node de driven n'est pas repris).
- MCP par défaut `mcp-server-grist` ; `grist-coder` en option.
- Design system : DSFR ou La Suite ui-kit, choisi par l'utilisateur (décision de Bruno, pas de défaut). Pour ui-kit, le paquet amont `@gouvfr-lasuite/ui-components` est
  la dépendance par défaut ; le fork de Bruno (`@barthgve/ui-components`, dossier `ui-kit-augmente`) reste une option de configuration, pas une obligation.
- Écritures de structure uniquement par scripts, jamais par le MCP.
- Flux `main`/`next`, tableau, wiki et semver de driven conservés.
- Le PRD ne garde que les modes « nouveau projet » et « reprise d'un existant » (`grist-continue`) ; le mode « cloner un SaaS » de driven est retiré.
- Sources des pièges Grist : `SP2C/CLAUDE.md`, `SCIP_grist/CLAUDE.md` et `docs/pieges.md`, `sirpa/docs/wiki/Pieges-Grist.md`.
- Vérifications en réel manuelles (voir 6.8).
- Installation du MCP : isolée (`pipx`/`uv tool`), jamais sans l'accord de l'utilisateur ; la clé d'API n'est écrite que dans `.env`.
- Le questionnaire d'installation a des valeurs par défaut, des drapeaux et `--yes` pour automatiser (équipes, CI).
