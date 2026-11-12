# grist-driven

Outils et méthode pour construire des applications Grist : bibliothèque Python
`grist-kit` (client, schéma, ACL, widgets), commandes `grist-*` pour Claude Code,
gabarit de projet (DSFR ou La Suite ui-kit) et MCP Grist.

Statut : v0.1.0 en construction. Voir `docs/superpowers/` pour la spec et le plan.

## Tests du kit

```bash
python3 -m venv .venv && .venv/bin/pip install -e packages/grist-kit
cd packages/grist-kit && ../../.venv/bin/python -m pytest -q
```

Licence MIT ; filiation dans `NOTICE`.
