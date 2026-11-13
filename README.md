# grist-driven

Une méthode et des outils pour construire une application Grist avec Claude Code, du cadrage au déploiement :
bibliothèque Python `grist-kit` (client, schéma, ACL, widgets, déploiement), commandes et skills `grist-*`,
gabarit de projet (DSFR ou La Suite ui-kit) et MCP Grist.

Version 0.1.0 · macOS et Linux · Claude Code seul · licence MIT (filiation dans `NOTICE`).

## Installation

À la racine du projet :

```bash
curl -fsSL https://raw.githubusercontent.com/BarthGve/grist-driven/main/install.sh | bash
```

Prérequis : `git`, `python3` ≥ 3.11, `curl`, `tar` ; `gh` pour le flux git ; Node ≥ 20 **seulement** pour le design system
`ui-kit`. L'installeur télécharge l'archive du dépôt (`GRIST_DRIVEN_URL` pour une autre source, par exemple un tag),
pose le contenu, crée `.venv` et y installe `grist-kit`. Sans terminal, il échoue net : relancer avec `--yes`
et `--design-system dsfr|ui-kit`.

Autres modes : `install.sh update` (met à jour sans toucher au code du projet ni aux gabarits modifiés),
`install.sh doctor` (versions, `.env`, accès à l'API, MCP, manifeste ; code 1 si un contrôle échoue),
`install.sh uninstall`. `--dry-run` montre ce qui serait fait sans rien écrire ; relancer `init` ne casse rien.

## Les huit questions

Chaque question a un drapeau ; `--yes` accepte les valeurs par défaut (sauf le design system, obligatoire).

| # | Question | Drapeau | Défaut |
|---|---|---|---|
| 1 | Nom de l'application | `--name` | nom du dossier |
| 2 | Organisation et adresse de l'API Grist | `--org`, `--api-host` | `docs`, `https://grist.numerique.gouv.fr/o/<org>/api` |
| 3 | Design system des widgets | `--design-system dsfr\|ui-kit` | **aucun** |
| 4 | MCP Grist, portée | `--mcp existing\|install\|coder\|none`, `--mcp-scope project\|user` | `install`, `project` |
| 5 | Clé d'API | variable `GRIST_API_KEY` ou saisie masquée | plus tard |
| 6 | Document de travail (facultatif) | `--doc-id` | vide |
| 7 | Flux git `main`/`next` et tableau GitHub | `--git-flow` / `--no-git-flow` | oui |
| 8 | Hooks git et workflow CI | `--hooks` / `--no-hooks`, `--ci` / `--no-ci` | oui |

La clé n'est jamais passée en argument ni affichée ; elle n'est écrite que dans `.env`, ignoré par git avant
d'être créé. `.mcp.json` ne contient que `${GRIST_API_KEY}` et `${GRIST_API_HOST}`. Le MCP par défaut,
`mcp-server-grist`, s'installe isolé (`pipx` ou `uv tool`), jamais sans accord ; il sert à lire, jamais à écrire
la structure du document.

## Les deux design systems

| | `dsfr` | `ui-kit` |
|---|---|---|
| Widgets | HTML d'un seul fichier (`widgets/`), logique dans un `core` partagé | React + Vite (`widgets_ui/`), un fichier par widget via `vite-plugin-singlefile` |
| Composants | Système de design de l'État | La Suite (`@gouvfr-lasuite/ui-components`) |
| Node | Tests `node --test` si présent | Node ≥ 20 requis pour le build |
| Déploiement | `inliner` recopie le core, puis `deployer` | `deployer` construit le bundle compressé (Vite), puis le dépose |

Le choix est consigné dans `.grist-driven.json` et pilote le gabarit, les skills et le déployeur.

## Ce que pose `init`

`.claude/commands` et `.claude/skills` (commandes et skills `grist-*`), `.claude/agents`, `.grist/` (scripts et
manifeste), `templates/` (gabarits de documents), le gabarit de projet (paquet Python, `schema.py`,
`acl_rules.py`, tests, widgets du profil), `.env` (droits 600) et `.env.example`, `.mcp.json`, hooks git,
`.github/workflows/ci.yml`. Un fichier du projet existant n'est jamais écrasé.

## Commandes

Pipeline : `/grist-prd` → `/grist-stories` → `/grist-architect` → `/grist-design-system`, puis, par story,
`/grist-research` → `/grist-design` → `/grist-plan` → `/grist-docs`, et par ticket `/grist-execute` →
`/grist-review` → `/grist-ship`. `/grist-orchestrator` enchaîne ces étapes en gardant les validations humaines.

| Commande | Rôle |
|---|---|
| `grist-help`, `grist-status` | afficher le pipeline, l'avancement et la prochaine commande |
| `grist-prd`, `grist-stories`, `grist-stories-review`, `grist-architect`, `grist-design-system` | cadrer le produit (PRD, stories, modèle de données, matrice ACL, design system) |
| `grist-init`, `grist-continue` | mettre en place le flux ; adopter un projet Grist déjà en cours |
| `grist-research`, `grist-design`, `grist-plan`, `grist-docs` | préparer une story |
| `grist-execute`, `grist-review`, `grist-ship`, `grist-orchestrator` | réaliser un ticket en TDD, le relire, le livrer |
| `grist-schema`, `grist-acl`, `grist-widget` | écrire schéma, règles d'accès et widgets (uniquement par les scripts du kit) |
| `grist-deploy`, `grist-recette`, `grist-optimise` | déployer dans l'ordre, essayer les droits en réel, mesurer et optimiser |
| `grist-feature`, `grist-release` | faire évoluer un produit livré ; livrer `next` vers `main` |

Douze skills `grist-*` complètent les commandes (ACL, schéma, widgets, déploiement, recette, MCP, performance, TDD…).

## grist-kit

`python -m grist_kit <commande>` : `apply-schema`, `maj-formules`, `apply-acl`, `amorcer`, `creer-page`,
`deployer`, `inliner`, `versions`. Toutes sont idempotentes et acceptent `--dry-run` et `--doc <id>`.
Les erreurs d'API sont lisibles (403 du pare-feu, 413 d'un bundle trop gros). Le faux Grist et le simulateur d'ACL
(`grist_kit.testing`) permettent de tester sans réseau.

## Développement

```bash
python3 -m venv .venv && .venv/bin/pip install -e packages/grist-kit pytest
.venv/bin/python -m pytest packages/grist-kit tests -q
bash tests/installer/run.sh
bash tests/e2e/test_init_complet.sh      # init dsfr puis ui-kit, doctor, pytest du projet généré
```

Aucun test ne touche le réseau, un vrai Grist ou `~/.claude.json`. La CI (`.github/workflows/ci.yml`) joue les mêmes
trois commandes, sans secret. Les vérifications en réel (`doctor` sur un document, `?aclAsUser_=`) sont une liste
manuelle, hors dépôt. Publication : voir `RELEASING.md`. Choix de conception : `docs/superpowers/`.
