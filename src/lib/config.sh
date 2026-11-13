# Écriture de .grist-driven.json et protection de .env. Aucune clé ici.

_json() { printf %s "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'; }

config_json() {
  local v=0.0.0; [ -f "$ROOT/VERSION" ] && v=$(head -n 1 "$ROOT/VERSION")
  cat <<JSON
{
  "version": "$(_json "$v")",
  "app": "$(_json "$NAME")",
  "package": "$(_json "$(package_de "$NAME")")",
  "design_system": "$DESIGN_SYSTEM",
  "api_host": "$(_json "$API_HOST")",
  "mcp": "$MCP",
  "mcp_scope": "$MCP_SCOPE",
  "git_flow": $GIT_FLOW,
  "hooks": $HOOKS,
  "ci": $CI
}
JSON
}

# .env doit être ignoré AVANT toute écriture de clé (idempotent). Les dossiers générés (venv, caches,
# dépendances npm) le sont aussi, pour qu'un « git add -A » ne les emporte pas.
ignorer_env() {
  local m
  for m in .env .venv/ __pycache__/ .pytest_cache/ node_modules/; do
    grep -qxF "$m" .gitignore 2>/dev/null || printf '%s\n' "$m" >> .gitignore
  done
}

ecrire_config() { config_json > .grist-driven.json; }
