# Pose du contenu : commandes, skills, agents, lib, gabarits. Manifeste et baseline.
# Source : $GRIST_DRIVEN_PAYLOAD (défaut : la racine du repo). Cible : le projet.
#   .grist/manifest          une ligne par fichier posé (chemin relatif au projet)
#   .grist/templates.orig/   copie des gabarits tels que posés (détecte les modifs locales)

# Couples « dossier source -> dossier cible ». Les gabarits sont traités à part.
_PAYLOAD_MAP="commands:.claude/commands skills:.claude/skills agents:.claude/agents lib:.grist/lib hooks:.grist/hooks"

_payload_copier() { mkdir -p "$(dirname "$2")" && cp "$1" "$2"; }

# Pose un gabarit : écrase seulement s'il est resté identique à la baseline.
_payload_gabarit() { # <rel> (relatif à templates/)
  local rel=$1 src="$_SRC/templates/$1" dst="templates/$1" orig=".grist/templates.orig/$1"
  if [ ! -e "$dst" ] || [ "$FORCE" = true ] \
     || { [ -e "$orig" ] && cmp -s "$dst" "$orig"; } \
     || cmp -s "$dst" "$src"; then
    _payload_copier "$src" "$dst"
  else
    info "grist-driven : gabarit modifié localement, conservé : $dst (--force pour l'écraser)" >&2
    return 0
  fi
  _payload_copier "$src" "$orig"
}

payload_pose() { # <source> <cible>
  local _SRC=$1 cible=$2 old="" pair d rel f
  cd "$cible" || return 1
  if [ "$DRY_RUN" = true ]; then
    info "[dry-run] seraient posés : commandes, skills, agents, lib, gabarits ($_SRC)"
    return 0
  fi
  mkdir -p .grist
  [ -f .grist/manifest ] && old=$(cat .grist/manifest)
  { [ -n "$old" ] && printf '%s\n' "$old"
    for pair in $_PAYLOAD_MAP; do
      d=$_SRC/${pair%%:*}
      [ -d "$d" ] || continue
      ( cd "$d" && find . -type f ! -name .gitkeep | sed 's|^\./||' ) | while IFS= read -r rel; do
        _payload_copier "$d/$rel" "${pair#*:}/$rel" && printf '%s\n' "${pair#*:}/$rel"
      done
    done
    if [ -d "$_SRC/templates" ]; then
      ( cd "$_SRC/templates" && find . -type f | sed 's|^\./||' ) | while IFS= read -r rel; do
        _payload_gabarit "$rel" && printf '%s\n' "templates/$rel"
      done
    fi
  } | sort -u > .grist/manifest.new
  mv .grist/manifest.new .grist/manifest
}

# Retire seulement les fichiers du manifeste (et la baseline), puis les dossiers vides.
payload_retire() {
  [ -f .grist/manifest ] || { info "grist-driven : rien à désinstaller (pas de manifeste)."; return 0; }
  if [ "$DRY_RUN" = true ]; then
    info "[dry-run] seraient retirés :"; cat .grist/manifest; return 0
  fi
  local f
  while IFS= read -r f; do rm -f -- "$f"; done < .grist/manifest
  rm -rf .grist/templates.orig .grist/manifest .grist/manifest.new .grist-driven.json
  # Dossiers vides laissés par la pose (jamais un dossier contenant du code du projet).
  find .claude .grist templates -depth -type d -exec rmdir {} \; 2>/dev/null || true
  rmdir .claude .grist templates 2>/dev/null || true
}
