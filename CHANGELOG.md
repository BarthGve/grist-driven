# Journal des modifications

## 0.1.0

### MCP Grist : version épinglée

- Version épinglée : `mcp-server-grist==0.2.2` (`MCP_SERVER_GRIST_VERSION` dans `src/lib/mcp.sh`),
  la plus récente publiée au 12 nov. 2026 (0.1.0, 0.1.1, 0.2.0, 0.2.1, 0.2.2 existent).
- Vérifié sur la roue 0.2.2 (téléchargée dans un répertoire temporaire, rien d'installé), point d'entrée
  `mcp-server-grist = mcp_server_grist:main`, Python ≥ 3.10 : le client lit `GRIST_API_KEY` (obligatoire)
  et `GRIST_API_HOST` (repli de `GRIST_API_URL`, qui est prioritaire si elle est définie ; défaut
  `https://docs.getgrist.com/api`). Le modèle `.mcp.json` (`${GRIST_API_KEY}`, `${GRIST_API_HOST}`) convient.
- Attention : si `GRIST_API_URL` est définie dans l'environnement, elle l'emporte sur `GRIST_API_HOST`.
