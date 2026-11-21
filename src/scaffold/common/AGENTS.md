# {{app}}

Application Grist construite avec grist-driven. Réponses, commentaires et commits en français.

## Règles

- Le schéma, les règles d'accès et les widgets s'écrivent **uniquement** par `grist_kit` ; le MCP lit, explore
  et manipule les données, jamais la structure.
- Tout script : `--dry-run` d'abord, lire le plan, puis appliquer. Les commandes sont idempotentes.
- `{{package}}/schema.py` et `{{package}}/acl_rules.py` sont des données pures ; les tests vivent dans `tests/`
  (`grist_kit.testing` : faux Grist, simulateur d'ACL, formules).
- `.env` n'est jamais commité ni affiché ; `.mcp.json` n'utilise que `${GRIST_API_KEY}` et `${GRIST_API_HOST}`.
- Environnements : recette = `GRIST_DOC_ID` (un document par worktree, facultatif) ; preprod = branche `next`,
  `GRIST_DOC_ID_PREPROD` ; production = branche `main`, `GRIST_DOC_ID_PRODUCTION`. Tout déploiement sur preprod ou
  production passe par `.venv/bin/python scripts/grist_env.py auto -- <commande>` (refus : mauvaise branche,
  identifiant absent ou partagé entre niveaux, production sans `VERSION` bumpée ni `CHANGELOG.md`). Jamais
  d'identifiant en clair, jamais `--doc` sur ces niveaux.
- GitHub : uniquement l'API REST (`gh api repos/...`), jamais `gh issue`, `gh pr`, `gh project` ni GraphQL : le quota
  GraphQL, partagé entre sessions, s'épuise. Le tableau passe par `.grist/lib/grist-board.sh` (REST). Seule
  exception, `grist-init` une fois par projet (création du projet et de ses six statuts).
- Une règle métier tenue en deux endroits (formule Grist et JavaScript) se teste des deux côtés.

## Commandes

```bash
.venv/bin/python -m grist_kit apply-schema --dry-run
.venv/bin/python -m grist_kit apply-acl --dry-run
.venv/bin/python -m pytest -q
```

Méthode : commandes `/grist-*` et skills `grist-*` (voir `.claude/`).
