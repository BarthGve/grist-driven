# Journal des modifications

## 0.1.0 - 2026-11-13

Première version publique.

### Installeur
- `install.sh` : `init`, `update`, `doctor`, `uninstall` ; questionnaire en huit questions (lu sur le terminal même en
  `curl … | bash`), drapeaux équivalents, `--yes`, `--dry-run`. Design system obligatoire, sans défaut.
- Amorçage `curl … | bash` : le script seul télécharge l'archive du dépôt (`GRIST_DRIVEN_URL` pour une autre source).
- Secrets : `.env` ignoré par git avant d'être écrit, droits 600 ; `.mcp.json` n'utilise que des variables d'environnement.
- MCP Grist : `mcp-server-grist` installé isolé, jamais sans accord ; `grist-coder` sur demande.
- Flux git `main`/`next`, tableau GitHub, hooks git, workflow CI du projet.

### grist-kit
- Client Grist, `apply-schema`, `maj-formules`, `apply-acl`, `amorcer`, `creer-page`, `deployer`, `inliner`, `versions` ;
  idempotents, `--dry-run`, `--doc`. Faux Grist et simulateur d'ACL pour tester sans réseau.
- Erreurs d'API lisibles (403 du pare-feu, 413 d'un bundle trop gros).
- Deux profils de widgets : DSFR (HTML d'un seul fichier) et La Suite ui-kit (React + Vite).

### Contenu
- Commandes `grist-*` (pipeline complet, `grist-continue` pour reprendre un projet existant), 12 skills, 4 agents,
  gabarits de documents, hooks.
- Tests : kit, contenu, gabarit généré, installeur (binaires factices), parcours de bout en bout ; CI sans secret.

### MCP Grist : version épinglée

- Version épinglée : `mcp-server-grist==0.2.2` (`MCP_SERVER_GRIST_VERSION` dans `src/lib/mcp.sh`),
  la plus récente publiée au 12 nov. 2026 (0.1.0, 0.1.1, 0.2.0, 0.2.1, 0.2.2 existent).
- Vérifié sur la roue 0.2.2 (téléchargée dans un répertoire temporaire, rien d'installé), point d'entrée
  `mcp-server-grist = mcp_server_grist:main`, Python ≥ 3.10 : le client lit `GRIST_API_KEY` (obligatoire)
  et `GRIST_API_HOST` (repli de `GRIST_API_URL`, qui est prioritaire si elle est définie ; défaut
  `https://docs.getgrist.com/api`). Le modèle `.mcp.json` (`${GRIST_API_KEY}`, `${GRIST_API_HOST}`) convient.
- Attention : si `GRIST_API_URL` est définie dans l'environnement, elle l'emporte sur `GRIST_API_HOST`.
