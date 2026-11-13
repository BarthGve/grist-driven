# install.sh doctor : diagnostic en lecture seule, une ligne OK/KO par contrôle.
# Ne modifie rien, n'affiche jamais la valeur d'une variable de .env (clé comprise).
# Variables lues : ROOT, MCP_SERVER_GRIST_VERSION. Code de sortie 1 s'il y a un KO.

_DOC_KO=0
_doc_ok() { info "OK  $*"; }
_doc_ko() { info "KO  $*"; _DOC_KO=$((_DOC_KO + 1)); }
_doc_na() { info "--  $*"; }

# Valeur d'une variable de .env (sans exécuter le fichier) ; vide si absente.
_doc_env() { sed -n "s/^$1=//p" .env 2>/dev/null | head -n 1 | tr -d '\r"'"'"; }

_doc_versions() {
  local v=0.0.0 posee kit
  [ -f "$ROOT/VERSION" ] && v=$(head -n 1 "$ROOT/VERSION")
  posee=$(sed -n 's/.*"version": *"\([^"]*\)".*/\1/p' .grist-driven.json | head -n 1)
  _doc_ok "installeur $v (projet posé avec ${posee:-version inconnue})"
  kit=$(.venv/bin/python -c 'import importlib.metadata as m; print(m.version("grist-kit"))' 2>/dev/null) || kit=""
  if [ -n "$kit" ]; then _doc_ok "grist-kit $kit"
  else _doc_ko "grist-kit introuvable dans .venv : relancer « install.sh init » ou « .venv/bin/pip install <grist-kit> »"; fi
}

_doc_env_vars() {
  if [ ! -f .env ]; then
    _doc_ko ".env absent : copier .env.example en .env et le remplir"; return 0
  fi
  _doc_ok ".env présent"
  local n
  for n in GRIST_API_KEY GRIST_API_HOST; do
    if [ -n "$(_doc_env $n)" ]; then _doc_ok "$n renseignée"; else _doc_ko "$n absente ou vide dans .env"; fi
  done
  if [ -n "$(_doc_env GRIST_DOC_ID)" ]; then _doc_ok "GRIST_DOC_ID renseignée"
  else _doc_na "GRIST_DOC_ID vide (facultatif)"; fi
}

# GET /docs/<id>/tables ; la clé passe par stdin de curl (ni argument, ni sortie).
_doc_api() {
  local host key doc code
  host=$(_doc_env GRIST_API_HOST); key=$(_doc_env GRIST_API_KEY); doc=$(_doc_env GRIST_DOC_ID)
  [ -n "$doc" ] || { _doc_na "API Grist ignorée : pas de document (GRIST_DOC_ID)"; return 0; }
  [ -n "$host" ] && [ -n "$key" ] || { _doc_ko "API Grist non testée : adresse ou clé manquante"; return 0; }
  case $host in http://*|https://*) ;; *) _doc_ko "GRIST_API_HOST doit commencer par http:// ou https://"; return 0;; esac
  case $doc in *[!A-Za-z0-9_-]*) _doc_ko "GRIST_DOC_ID invalide (lettres, chiffres, - et _ seulement)"; return 0;; esac
  command -v curl >/dev/null 2>&1 || { _doc_ko "curl absent : accès à l'API non testé"; return 0; }
  code=$(printf 'header = "Authorization: Bearer %s"\n' "$key" \
    | curl -s -o /dev/null -w '%{http_code}' --max-time 10 --config - "${host%/}/docs/$doc/tables" 2>/dev/null) || code=000
  case $code in
    2??) _doc_ok "API Grist joignable (document lu)";;
    401|403) _doc_ko "API Grist : accès refusé (HTTP $code), vérifier la clé ou le pare-feu";;
    404) _doc_ko "API Grist : document introuvable (HTTP 404), vérifier GRIST_DOC_ID";;
    000) _doc_ko "API Grist injoignable : vérifier GRIST_API_HOST et le réseau";;
    *) _doc_ko "API Grist : réponse inattendue (HTTP $code)";;
  esac
}

_doc_entree_mcp() { # <nom>
  _mcp_a_entree "$1" || { _mcp_a claude && claude mcp list 2>/dev/null | grep -q "^$1[: ]"; }
}

_doc_mcp() {
  local m v nom=grist
  m=$(sed -n 's/.*"mcp": *"\([a-z]*\)".*/\1/p' .grist-driven.json | head -n 1)
  [ "$m" != none ] || { _doc_na "MCP non utilisé (choix à l'installation)"; return 0; }
  [ "$m" = coder ] && nom=grist-coder
  if [ "$nom" = grist ]; then
    if _mcp_a mcp-server-grist; then
      v=$(_mcp_version_installee)
      _doc_ok "mcp-server-grist installé (version ${v:-inconnue}, épinglée $MCP_SERVER_GRIST_VERSION)"
    else
      _doc_ko "mcp-server-grist introuvable. Lancer : $(_mcp_commande_manuelle)"
    fi
  fi
  if _doc_entree_mcp "$nom"; then _doc_ok "entrée MCP « $nom » déclarée"
  else _doc_ko "entrée MCP « $nom » absente de .mcp.json. Relancer « install.sh init » ou « claude mcp add »"; fi
}

_doc_manifeste() {
  [ -f .grist/manifest ] || { _doc_ko "manifeste .grist/manifest absent : relancer « install.sh update »"; return 0; }
  local f manque=0 total=0
  while IFS= read -r f; do
    [ -n "$f" ] || continue
    total=$((total + 1))
    [ -e "$f" ] || { manque=$((manque + 1)); [ "$manque" -gt 5 ] || info "      fichier manquant : $f"; }
  done < .grist/manifest
  if [ "$manque" -eq 0 ]; then _doc_ok "manifeste cohérent ($total fichiers)"
  else _doc_ko "manifeste : $manque fichier(s) manquant(s) sur $total. Lancer « install.sh update »"; fi
}

doctor_run() {
  [ -f .grist-driven.json ] || die 2 "projet non initialisé : lancer d'abord « install.sh init »."
  _DOC_KO=0
  _doc_versions; _doc_env_vars; _doc_api; _doc_mcp; _doc_manifeste
  if [ "$_DOC_KO" -eq 0 ]; then info "doctor : tout est OK."; return 0; fi
  info "doctor : $_DOC_KO contrôle(s) en échec."; return 1
}
