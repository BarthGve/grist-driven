#!/usr/bin/env bash
# grist-wiki : publie les documents produit des stories livrées dans le wiki GitHub du dépôt.
#
#   grist-wiki.sh publish <racine-du-projet> <version> <story>...
#
# Chaque docs/product/<story>.md devient la page <story> du wiki ; Home.md est reconstruit
# (version + stories publiées). GRIST_WIKI_URL remplace l'adresse du wiki (tests, miroir).
set -euo pipefail

ICI="$(CDPATH= cd -- "$(dirname "$0")" && pwd)"
# shellcheck source=grist-config.sh
source "$ICI/grist-config.sh"

die() { echo "grist-wiki : $*" >&2; exit 1; }

publier() {
  local racine="${1:-}" version="${2:-}"
  shift 2 || true
  [ -n "$racine" ] && [ -n "$version" ] && [ "$#" -ge 1 ] || die "usage : publish <racine> <version> <story>..."

  local story
  for story in "$@"; do
    [ -f "$racine/docs/product/$story.md" ] || die "document produit introuvable : docs/product/$story.md"
  done
  grist_config_charger "$racine"

  local url="${GRIST_WIKI_URL:-https://github.com/$(grist_config_depot).wiki.git}"
  local -a auth=()
  # Le jeton ne passe ni par l'URL (visible dans `ps`) ni par .git/config : un assistant
  # d'identifiants le lit dans l'environnement. Le premier `credential.helper=` vide la liste
  # des assistants déjà configurés.
  local jeton="${GH_TOKEN:-${GITHUB_TOKEN:-}}"
  [ -n "$jeton" ] || jeton="$(gh auth token 2>/dev/null || true)"
  if [ -n "$jeton" ] && [ -z "${GRIST_WIKI_URL:-}" ]; then
    export GRIST_WIKI_JETON="$jeton"
    auth=(-c "credential.helper=" \
      -c 'credential.helper=!f(){ echo username=x-access-token; echo "password=$GRIST_WIKI_JETON"; }; f')
  fi

  local tmp wiki
  tmp="$(mktemp -d "${TMPDIR:-/tmp}/grist-wiki.XXXXXX")"
  trap "rm -rf '$tmp'" EXIT # valeur figée : `tmp` est locale et n'existera plus à la sortie
  wiki="$tmp/wiki"
  if ! git ${auth[@]+"${auth[@]}"} clone -q --depth 1 "$url" "$wiki" 2>/dev/null; then
    # Wiki encore vide (la première page n'existe pas) : on part d'un dépôt neuf.
    git init -q -b master "$wiki"
    git -C "$wiki" remote add origin "$url"
  fi

  for story in "$@"; do cp "$racine/docs/product/$story.md" "$wiki/$story.md"; done

  python3 - "$wiki" "$version" "$GRIST_REPO" <<'PY'
import pathlib, sys

dossier, version, depot = pathlib.Path(sys.argv[1]), sys.argv[2], sys.argv[3]
pages = sorted(p.stem for p in dossier.glob("*.md") if p.name != "Home.md")
lignes = [f"# {depot} : wiki produit", "", f"**Version :** {version}", "", "## Stories livrées", ""]
lignes += [f"- [{p}]({p})" for p in pages]
(dossier / "Home.md").write_text("\n".join(lignes) + "\n")
PY

  git -C "$wiki" add -A
  if git -C "$wiki" diff --cached --quiet; then
    echo "grist-wiki : rien à publier"
    return 0
  fi
  git -C "$wiki" -c user.name="${GIT_AUTHOR_NAME:-grist-wiki}" -c user.email="${GIT_AUTHOR_EMAIL:-grist-wiki@localhost}" \
    commit -q -m "docs: wiki produit de la v$version"
  local branche
  branche="$(git -C "$wiki" rev-parse --abbrev-ref HEAD)"
  git -C "$wiki" ${auth[@]+"${auth[@]}"} push -q -u origin "HEAD:$branche" 2>/dev/null \
    || git -C "$wiki" ${auth[@]+"${auth[@]}"} push -q -u origin HEAD:master \
    || die "publication refusée (wiki activé ? droits d'écriture ?)"
  echo "grist-wiki : v$version publiée ($# stories)"
}

case "${1:-}" in
  publish) shift; publier "$@" ;;
  *) die "usage : grist-wiki.sh publish <racine> <version> <story>..." ;;
esac
