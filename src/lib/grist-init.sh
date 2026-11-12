#!/usr/bin/env bash
# grist-init : met en place le flux d'un projet (branches, VERSION, dépôt GitHub, tableau).
#
#   grist-init.sh run [--owner LOGIN] [--repo NOM] [--public|--private] [--title TITRE] [--no-remote] [--yes]
#   grist-init.sh assert-status-ids '<json>'     échoue si un des six statuts n'a pas d'identifiant
#
# Idempotent : branches, VERSION, CHANGELOG.md et .grist/config.json existants ne sont jamais
# réécrits ; sans --yes, chaque création distante demande confirmation (échec net hors terminal).
set -euo pipefail

OUI=0 PUBLIC=0 DISTANT=1 OWNER="" REPO="" TITRE="grist-driven"
STATUTS="backlog,ready,in progress,review,test,shipped"
CHAMP="Statut" # distinct du champ « Status » que GitHub crée par défaut dans un projet

die() { echo "grist-init : $*" >&2; exit 1; }
alerte() { echo "grist-init : ALERTE : $*" >&2; }

confirmer() {
  [ "$OUI" = 1 ] && return 0
  local rep=""
  printf '%s [o/N] ' "$1" >&2
  read -r rep || true
  case "$rep" in o | O | oui | y | Y | yes) ;; *) die "abandon (relancer avec --yes pour répondre oui d'avance)" ;; esac
}

assert_statuts() {
  python3 - "$1" "$STATUTS" <<'PY'
import json, sys

try:
    options = json.loads(sys.argv[1])
except ValueError:
    sys.exit("grist-init : status_option_ids n'est pas un JSON valide")
if not isinstance(options, dict):
    sys.exit("grist-init : status_option_ids doit être un objet")
manque = [s for s in sys.argv[2].split(",") if not str(options.get(s, "")).strip()]
if manque:
    sys.exit("grist-init : identifiants de statut manquants : " + ", ".join(manque))
PY
}

lire_options() {
  while [ $# -gt 0 ]; do
    case "$1" in
      --yes | -y) OUI=1 ;;
      --public) PUBLIC=1 ;;
      --private) PUBLIC=0 ;;
      --no-remote) DISTANT=0 ;;
      --owner) OWNER="${2:-}"; [ -n "$OWNER" ] || die "--owner demande un identifiant"; shift ;;
      --repo) REPO="${2:-}"; [ -n "$REPO" ] || die "--repo demande un nom"; shift ;;
      --title) TITRE="${2:-}"; shift ;;
      *) die "option inconnue : $1" ;;
    esac
    shift
  done
}

commit() { git -c user.name="${GIT_AUTHOR_NAME:-grist-init}" -c user.email="${GIT_AUTHOR_EMAIL:-grist-init@localhost}" commit -q "$@"; }

# --- local : branches et fichiers de version ---------------------------------------------------------
preparer_depot() {
  git rev-parse --git-dir >/dev/null 2>&1 || git init -q -b main
  if ! git rev-parse HEAD >/dev/null 2>&1; then
    [ -f README.md ] || printf '# %s\n' "${REPO:-$(basename "$PWD")}" >README.md
    git add -A
    commit -m "🔧 CHORE: premier commit"
  fi
  git show-ref --verify --quiet refs/heads/main || git branch -M main
  git show-ref --verify --quiet refs/heads/next || git branch next main
  [ -f VERSION ] || printf '0.1.0\n' >VERSION
  [ -f CHANGELOG.md ] || printf '# Journal des changements\n\n## 0.1.0 - à publier\n\n' >CHANGELOG.md
}

# --- distant : dépôt, wiki, protection des branches ------------------------------------------------------
identifier_depot() {
  local origine
  if origine="$(git remote get-url origin 2>/dev/null)" && [[ "$origine" =~ github\.com[:/]([^/]+)/([^/.]+)(\.git)?$ ]]; then
    OWNER="${BASH_REMATCH[1]}" REPO="${BASH_REMATCH[2]}"
  fi
  [ -n "$OWNER" ] || OWNER="$(gh api user -q .login 2>/dev/null || true)"
  [ -n "$OWNER" ] || die "propriétaire introuvable (passer --owner ou connecter gh)"
  [ -n "$REPO" ] || REPO="$(basename "$PWD")"
}

creer_depot_distant() {
  git remote get-url origin >/dev/null 2>&1 && return 0
  confirmer "Créer le dépôt GitHub $OWNER/$REPO ($([ "$PUBLIC" = 1 ] && echo public || echo privé)) ?"
  gh repo create "$OWNER/$REPO" "$([ "$PUBLIC" = 1 ] && echo --public || echo --private)" --source=. --remote=origin --push
}

proteger() { # <branche> : PR obligatoire, pas de force-push ni de suppression
  local branche="$1"
  gh api -X PUT "repos/$OWNER/$REPO/branches/$branche/protection" -H "Accept: application/vnd.github+json" --input - \
    >/dev/null <<JSON || alerte "« $branche » n'est PAS protégée : à régler dans GitHub (Settings → Branches)"
{"required_status_checks": null, "enforce_admins": $([ "$branche" = main ] && echo true || echo false),
 "required_pull_request_reviews": {"required_approving_review_count": 0},
 "restrictions": null, "allow_force_pushes": false, "allow_deletions": false}
JSON
}

configurer_distant() {
  gh api -X PATCH "repos/$OWNER/$REPO" -f has_wiki=true >/dev/null || alerte "wiki non activé sur $OWNER/$REPO"
  proteger main
  proteger next
}

# --- tableau et .grist/config.json --------------------------------------------------------------------------
creer_tableau() {
  if [ -f .grist/config.json ]; then
    echo "grist-init : .grist/config.json existe déjà, tableau conservé"
    return 0
  fi
  confirmer "Créer le projet GitHub « $TITRE » et son tableau de statuts ?"
  local projet numero champ liste
  projet="$(gh project create --owner "$OWNER" --title "$TITRE" --format json)"
  numero="$(python3 -c 'import json,sys; p=json.loads(sys.argv[1]); assert p.get("id"); print(p["number"])' "$projet")" \
    || die "réponse de gh illisible : projet sans identifiant"
  champ="$(gh project field-create "$numero" --owner "$OWNER" --name "$CHAMP" --data-type SINGLE_SELECT \
    --single-select-options "$STATUTS" --format json)"
  gh project link "$numero" --owner "$OWNER" --repo "$REPO" >/dev/null 2>&1 || true
  liste="$(gh project field-list "$numero" --owner "$OWNER" --format json)"

  mkdir -p .grist
  python3 - "$OWNER" "$REPO" "$projet" "$champ" "$liste" "$STATUTS" >.grist/config.json.tmp <<'PY' \
    || { rm -f .grist/config.json.tmp; die "tableau créé mais statuts incomplets : config non écrite"; }
import json, sys

owner, repo, projet, champ, liste, statuts = sys.argv[1:]
projet, champ, liste = json.loads(projet), json.loads(champ), json.loads(liste)
options = {o["name"]: o["id"] for o in champ.get("options", [])}
for f in liste.get("fields", []):  # repli : le champ créé, relu dans la liste du projet
    if f.get("id") == champ.get("id"):
        options = {**{o["name"]: o["id"] for o in f.get("options", [])}, **options}
manque = [s for s in statuts.split(",") if not options.get(s)]
if manque:
    sys.exit("identifiants de statut manquants : " + ", ".join(manque))
config = {"owner": owner, "repo": repo, "project_id": projet["id"], "project_number": projet["number"],
          "status_field_id": champ["id"], "status_option_ids": {s: options[s] for s in statuts.split(",")}}
print(json.dumps(config, indent=2))
PY
  mv .grist/config.json.tmp .grist/config.json
}

publier_branches() {
  git remote get-url origin >/dev/null 2>&1 || return 0
  git push -q -u origin main 2>/dev/null || true
  git push -q -u origin next 2>/dev/null || true
}

cmd_run() {
  command -v gh >/dev/null || die "la CLI gh est requise"
  command -v python3 >/dev/null || die "python3 est requis"
  preparer_depot
  if [ "$DISTANT" = 1 ]; then
    identifier_depot
    creer_depot_distant
    configurer_distant
  else
    [ -n "$OWNER" ] || OWNER="$(gh api user -q .login 2>/dev/null || true)"
    [ -n "$OWNER" ] || die "avec --no-remote, passer --owner"
    [ -n "$REPO" ] || REPO="$(basename "$PWD")"
  fi
  creer_tableau
  publier_branches
  echo "grist-init : terminé, $OWNER/$REPO (VERSION $(tr -d '[:space:]' <VERSION))"
}

case "${1:-}" in
  run) shift; lire_options "$@"; cmd_run ;;
  assert-status-ids) assert_statuts "${2:-}" ;;
  *) die "usage : grist-init.sh run [--owner L] [--repo N] [--public|--private] [--title T] [--no-remote] [--yes] | assert-status-ids '<json>'" ;;
esac
