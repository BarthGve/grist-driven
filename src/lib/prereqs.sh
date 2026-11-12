# Vérification des prérequis. Code de sortie 3 s'il en manque.
# Variables lues : GIT_FLOW, DESIGN_SYSTEM.

# Majeur.mineur d'une sortie « Python 3.12.1 » / « v20.11.0 » ; vide si illisible.
_version_de() { "$1" --version 2>/dev/null | sed -n 's/[^0-9]*\([0-9][0-9]*\.[0-9][0-9]*\).*/\1/p' | head -n 1; }

# 0 si $1 (x.y) >= $2 (x.y).
_version_ge() {
  local a=${1%%.*} b=${2%%.*}
  [ -n "$1" ] || return 1
  [ "$a" -gt "$b" ] || { [ "$a" -eq "$b" ] && [ "${1#*.}" -ge "${2#*.}" ]; }
}

verifier_prerequis() {
  local manque="" v
  command -v git >/dev/null 2>&1 || manque="$manque\n  - git"
  v=$(_version_de python3)
  if ! command -v python3 >/dev/null 2>&1 || ! _version_ge "$v" 3.11; then
    manque="$manque\n  - python 3.11 ou plus (trouvé : ${v:-aucun})"
  fi
  if [ "$GIT_FLOW" = true ] && ! command -v gh >/dev/null 2>&1; then
    manque="$manque\n  - gh (requis par le flux git ; ou relancer avec --no-git-flow)"
  fi
  if [ "$DESIGN_SYSTEM" = ui-kit ]; then
    v=$(_version_de node)
    if ! command -v node >/dev/null 2>&1 || ! _version_ge "$v" 20.0; then
      manque="$manque\n  - node 20 ou plus, requis par le design system ui-kit (trouvé : ${v:-aucun})"
    fi
  fi
  [ -z "$manque" ] || die 3 "prérequis manquants :$(printf '%b' "$manque")"
}
