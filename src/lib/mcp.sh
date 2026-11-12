# Installation et déclaration du MCP Grist (spec §6.7).
# Variables lues : MCP, MCP_SCOPE, YES, DRY_RUN, MCP_SERVER_GRIST_VERSION.
# Jamais d'installation sans accord (--yes vaut accord). Un échec ou un refus
# affiche la commande à lancer et rend 0 : l'init continue.
# Aucune clé ici : les modèles ne contiennent que ${GRIST_API_KEY} et ${GRIST_API_HOST}.

# Version testée avec grist-driven (lit GRIST_API_KEY et GRIST_API_HOST, voir CHANGELOG.md).
MCP_SERVER_GRIST_VERSION=${MCP_SERVER_GRIST_VERSION:-0.2.2}
_MCP_PAQUET="mcp-server-grist==$MCP_SERVER_GRIST_VERSION"

_mcp_a() { command -v "$1" >/dev/null 2>&1; }
_mcp_a_entree() { [ -f .mcp.json ] && grep -q "\"$1\"" .mcp.json; }

# existing | absent : binaire dans PATH, entrée « grist » dans .mcp.json, ou claude mcp list.
mcp_detecter() {
  if _mcp_a mcp-server-grist || _mcp_a_entree grist \
     || { _mcp_a claude && claude mcp list 2>/dev/null | grep -q '^grist[: ]'; }; then
    echo existing
  else
    echo absent
  fi
}

# Python « externally managed » (PEP 668) : pip --user est alors interdit.
_mcp_pep668() {
  local d; d=$(python3 -I -c 'import sysconfig; print(sysconfig.get_path("stdlib"))' 2>/dev/null) || return 1
  [ -e "$d/EXTERNALLY-MANAGED" ]
}

# Commande d'installation à afficher quand rien ne peut s'exécuter.
_mcp_commande_manuelle() { # [--force]
  if _mcp_a pipx || ! _mcp_a uv; then echo "pipx install ${1:+$1 }$_MCP_PAQUET"
  else echo "uv tool install ${1:+$1 }$_MCP_PAQUET"; fi
}

_mcp_echec() { # <raison>
  info "grist-driven : MCP Grist non installé ($1). Pour l'installer, lancer :"
  info "    $(_mcp_commande_manuelle)"
  info "puis « install.sh update » pour le déclarer. L'installation continue."
}

# Accord de l'utilisateur : --yes, sinon question sur le terminal (refus s'il n'y en a pas).
_mcp_accord() { # <question>
  [ "$YES" = true ] && return 0
  { true <&3; } 2>/dev/null || ouvrir_terminal || return 1
  printf '%s [O/n] : ' "$1" >&2
  IFS= read -r REPONSE <&3 || return 1
  case $(printf %s "$REPONSE" | tr 'A-Z' 'a-z') in ""|o|oui|y|yes) return 0;; *) return 1;; esac
}

# Installe isolé, depuis « / » (la config du projet ne peut pas rediriger l'index) : pipx, puis uv tool, puis pip --user (sauf PEP 668). 0 si installé.
mcp_installer() {
  if _mcp_a pipx; then ( cd / && pipx install --force "$_MCP_PAQUET" ) >/dev/null 2>&1
  elif _mcp_a uv; then ( cd / && uv tool install --force "$_MCP_PAQUET" ) >/dev/null 2>&1
  elif _mcp_a pip && ! _mcp_pep668; then ( cd / && pip install --user "$_MCP_PAQUET" ) >/dev/null 2>&1
  else return 1; fi
}

# Version installée du serveur (vide si inconnue).
_mcp_version_installee() {
  { _mcp_a pipx && pipx list --short 2>/dev/null
    _mcp_a uv && uv tool list 2>/dev/null
    _mcp_a pip && pip show mcp-server-grist 2>/dev/null | sed -n 's/^Version: */mcp-server-grist /p'
  } | sed -n 's/^mcp-server-grist[ ]*v\{0,1\}\([0-9][0-9.]*\).*/\1/p' | head -n 1 || true
}

# Déclare le serveur. $1 = project|user, $2 = grist|grist-coder (défaut grist).
mcp_declarer() {
  local portee=$1 nom=${2:-grist} tpl="$ROOT/src/mcp/mcp.json.tpl"
  [ "$nom" = grist-coder ] && tpl="$ROOT/src/mcp/grist-coder.json.tpl"
  if [ "$portee" = user ]; then
    local -a a=(--scope user "$nom" -e 'GRIST_API_KEY=${GRIST_API_KEY}' -e 'GRIST_API_HOST=${GRIST_API_HOST}' -- mcp-server-grist)
    [ "$nom" = grist-coder ] && a=(--scope user --transport http grist-coder 'http://localhost:8000/mcp')
    if _mcp_a claude && claude mcp add "${a[@]}" >/dev/null 2>&1; then
      info "grist-driven : MCP « $nom » déclaré pour l'utilisateur."
    else
      info "grist-driven : déclaration non faite. Pour la poser, lancer :"
      info "    claude mcp add ${a[*]}"
    fi
    return 0
  fi
  _mcp_a_entree "$nom" && return 0
  if [ -f .mcp.json ]; then
    info "grist-driven : .mcp.json existe déjà, non modifié. Y ajouter l'entrée « $nom » :"
    cat "$tpl"; return 0
  fi
  cat "$tpl" > .mcp.json
  info "grist-driven : .mcp.json écrit (variables \${GRIST_API_KEY} et \${GRIST_API_HOST}, aucune clé)."
}

# grist-coder : seulement la déclaration HTTP, puis la mise en route.
_mcp_coder() {
  mcp_declarer "$MCP_SCOPE" grist-coder
  info "grist-driven : grist-coder n'est pas installé. Mise en route : démarrer le serveur local"
  info "    gristcoder_mcp (HTTP, port 8000 par défaut ; GRIST_CODER_URL pour une autre adresse),"
  info "    puis relancer Claude Code. Voir la documentation de gristcoder_mcp."
}

# Étape d'init selon --mcp (existing|install|coder|none).
mcp_etape() {
  case $MCP in
    none) return 0;;
    coder) [ "$DRY_RUN" = true ] && { info "[dry-run] MCP : déclaration grist-coder"; return 0; }
           _mcp_coder; return 0;;
  esac
  if [ "$DRY_RUN" = true ]; then info "[dry-run] MCP : $_MCP_PAQUET ($MCP, portée $MCP_SCOPE)"; return 0; fi
  if [ "$(mcp_detecter)" = absent ]; then
    if [ "$MCP" = existing ]; then
      info "grist-driven : mcp-server-grist introuvable alors que --mcp existing. Relancer avec --mcp install."
      return 0
    fi
    if ! _mcp_accord "Installer le MCP Grist ($_MCP_PAQUET, isolé)"; then _mcp_echec "refusé"; return 0; fi
    mcp_installer || { _mcp_echec "pas de pipx ni d'uv utilisable, ou Python géré par le système (PEP 668)"; return 0; }
    info "grist-driven : MCP Grist installé ($_MCP_PAQUET)."
  fi
  mcp_declarer "$MCP_SCOPE"
}

# update : aligne la version installée sur l'épinglage (avec accord). Sans effet si mcp != install.
mcp_aligner() {
  local m=$MCP v
  [ -n "$m" ] || m=$(sed -n 's/.*"mcp": *"\([a-z]*\)".*/\1/p' .grist-driven.json 2>/dev/null | head -n 1)
  [ "$m" = install ] || return 0
  v=$(_mcp_version_installee)
  [ -n "$v" ] && [ "$v" != "$MCP_SERVER_GRIST_VERSION" ] || return 0
  if [ "$DRY_RUN" = true ]; then info "[dry-run] MCP : $v -> $MCP_SERVER_GRIST_VERSION"; return 0; fi
  if _mcp_accord "MCP Grist en $v, version épinglée $MCP_SERVER_GRIST_VERSION : réinstaller" && mcp_installer; then
    info "grist-driven : MCP Grist aligné sur $MCP_SERVER_GRIST_VERSION."
  else
    info "grist-driven : MCP Grist laissé en $v. Pour l'aligner, lancer :"
    info "    $(_mcp_commande_manuelle --force)"
  fi
}
