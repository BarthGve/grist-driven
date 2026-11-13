# Gabarit de projet (spec §6.5) : fichiers communs + profil du design system, .env, .venv.
# Le gabarit est du code du projet : un fichier existant n'est JAMAIS écrasé (pas même avec --force).
# Substitutions : {{app}}, {{package}}, {{kit_spec}}. Le dossier __package__/ devient le paquet Python.

# ponytail: dépôt et tag supposés (à confirmer à la publication) ; GRIST_KIT_SPEC les surcharge (chemin local en test).
GRIST_KIT_SPEC_DEFAUT="grist-kit @ git+https://github.com/BarthGve/grist-driven.git@v0.1.1#subdirectory=packages/grist-kit"

# Nom de paquet Python : minuscules, chiffres et « _ » ; jamais vide ni commençant par un chiffre.
package_de() {
  local p
  p=$(printf %s "$1" | tr 'A-Z' 'a-z' | sed 's/[^a-z0-9]\{1,\}/_/g; s/^_//; s/_$//')
  [ -n "$p" ] || p=app
  case $p in [0-9]*) p="app_$p";; esac
  printf %s "$p"
}

_sc_src() { local p=${GRIST_DRIVEN_PAYLOAD:-$ROOT}; [ -d "$p/scaffold" ] && echo "$p/scaffold" || echo "$ROOT/src/scaffold"; }
_sc_esc() { printf %s "$1" | sed 's/[\\&|]/\\&/g'; }

# Pose un dossier du gabarit dans le projet courant, sans écraser.
_sc_dossier() { # <dossier source>
  local src=$1 rel dst app pkg spec
  app=$(_sc_esc "$NAME"); pkg=$(_sc_esc "$PACKAGE"); spec=$(_sc_esc "${GRIST_KIT_SPEC:-$GRIST_KIT_SPEC_DEFAUT}")
  [ -d "$src" ] || return 0
  ( cd "$src" && find . -type f | sed 's|^\./||' | sort ) | while IFS= read -r rel; do
    dst=$(printf %s "$rel" | sed "s|^__package__/|$pkg/|")
    if [ -e "$dst" ]; then info "grist-driven : $dst existe, conservé."; continue; fi
    mkdir -p "$(dirname "$dst")"
    sed "s|{{app}}|$app|g; s|{{package}}|$pkg|g; s|{{kit_spec}}|$spec|g" "$src/$rel" > "$dst"
  done
}

# .env : créé seulement s'il n'existe pas, après vérification qu'il est ignoré, droits 600.
env_creer() {
  [ -e .env ] && { info "grist-driven : .env existe, jamais réécrit."; return 0; }
  grep -qxF '.env' .gitignore 2>/dev/null || die 2 ".env n'est pas ignoré par git : écriture refusée."
  ( umask 077
    printf 'GRIST_API_KEY=%s\nGRIST_API_HOST=%s\nGRIST_DOC_ID=%s\n' "${GRIST_API_KEY:-}" "$API_HOST" "$DOC_ID" > .env )
  chmod 600 .env
  info "grist-driven : .env créé (droits 600, ignoré par git)."
}

# .venv + grist-kit depuis GRIST_KIT_SPEC. Un échec ne bloque pas : on affiche la commande.
venv_creer() {
  local spec=${GRIST_KIT_SPEC:-$GRIST_KIT_SPEC_DEFAUT} cmd
  # shellcheck disable=SC2086
  cmd=".venv/bin/pip install ${GRIST_DRIVEN_PIP_ARGS:-} \"$spec\" pytest"
  if [ -x .venv/bin/python ] || python3 -m venv ${GRIST_DRIVEN_VENV_ARGS:-} .venv >/dev/null 2>&1; then
    if [ -x .venv/bin/pip ] && eval "$cmd" >/dev/null 2>&1; then
      info "grist-driven : .venv prêt, grist-kit installé."; return 0
    fi
  fi
  info "grist-driven : .venv ou grist-kit non installé. Lancer : python3 -m venv .venv && $cmd"
}

scaffold_etape() {
  PACKAGE=$(package_de "$NAME")
  if [ "$DRY_RUN" = true ]; then
    info "[dry-run] gabarit : fichiers communs + profil $DESIGN_SYSTEM (paquet $PACKAGE), .env et .venv"
    return 0
  fi
  local src; src=$(_sc_src)
  _sc_dossier "$src/common"
  _sc_dossier "$src/$DESIGN_SYSTEM"
  env_creer
  venv_creer
}
