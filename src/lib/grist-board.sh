#!/usr/bin/env bash
# grist-board : tableau GitHub (Issues + Project V2) du flux.
#
# Statuts : backlog → ready → in progress → review → test → shipped (retours : voir TRANSITIONS).
# Une story (clé `s01-x`) a un statut dérivé de ses tickets (clé `s01-x/t01-y`) et n'est jamais `ready`.
# Un ticket est repéré par le titre de son issue : « [<clé>] titre ».
#
#   status-get <clé>                         statut courant
#   status-set <clé> <statut>                déplace un ticket (transitions contrôlées)
#   status-all                               « <clé><TAB><statut> » pour chaque issue du flux
#   require-ready <story>/<ticket>           échoue si le ticket n'est pas ready ni in progress
#   parent-sync <story>                      recalcule le statut de la story depuis ses tickets
#   issue-create-us <story> <titre> <corps.md>
#   issue-create-ticket <story> <ticket> <titre> <corps.md>
#   issue-adopt <clé> <n° d'issue> <titre>   rattache au flux une issue écrite à la main
set -euo pipefail

ICI="$(CDPATH= cd -- "$(dirname "$0")" && pwd)"
# shellcheck source=grist-config.sh
source "$ICI/grist-config.sh"

die() { echo "grist-board : $*" >&2; exit 1; }

# Transitions permises depuis chaque statut d'un ticket.
transitions_depuis() {
  case "$1" in
    backlog) echo "ready" ;;
    ready) echo "in progress|backlog" ;;
    "in progress") echo "review|ready" ;;
    review) echo "test|in progress" ;;
    test) echo "shipped|in progress" ;;
    *) echo "" ;;
  esac
}

# --- lecture des issues ---------------------------------------------------------------------
# La liste est lue une fois par exécution (chaque page de 100 coûte un point GraphQL).
# Toute commande lit après sa dernière écriture ; sinon vider "$CACHE" entre les deux.
CACHE="$(mktemp)"
trap 'rm -f "$CACHE"' EXIT
LIMITE="${GRIST_LIMITE_ISSUES:-5000}" # ponytail : au-delà, liste tronquée avec alerte ; relever la limite si besoin.

issues() {
  if [ ! -s "$CACHE" ]; then
    gh issue list -R "$(grist_config_depot)" --state all --limit "$LIMITE" \
      --json title,number,id,projectItems >"$CACHE"
    [ "$(python3 -c 'import json,sys; print(len(json.load(open(sys.argv[1]))))' "$CACHE")" -lt "$LIMITE" ] \
      || echo "grist-board : ALERTE, $LIMITE issues lues (la limite) : des plus anciennes peuvent manquer" >&2
  fi
  cat "$CACHE"
}

# Interrogation du cache : trouver|statut|champ|enfants|tous.
interroger() {
  issues >/dev/null
  python3 - "$CACHE" "$@" <<'PY'
import json, re, sys

fichier, mode, *a = sys.argv[1:]
liste = json.load(open(fichier))
statut = lambda i: ((i.get("projectItems") or [{}])[0].get("status") or {}).get("name", "")
cle = lambda i: (re.match(r"\[([^\]]+)\]", i.get("title", "")) or [None, None])[1]
par_cle = {cle(i): i for i in liste if cle(i)}

if mode == "tous":
    for k, i in par_cle.items():
        print(f"{k}\t{statut(i) or '-'}")
    sys.exit(0)
if mode == "enfants":
    print("\n".join(s for k, i in par_cle.items() if k.startswith(a[0] + "/") for s in [statut(i)] if s))
    sys.exit(0)
i = par_cle.get(a[0])
if i is None:
    sys.exit(f"grist-board : issue introuvable pour la clé {a[0]!r}")
if mode == "statut":
    if not statut(i):
        sys.exit(f"grist-board : {a[0]!r} n'est pas sur le tableau (aucun statut)")
    print(statut(i), end="")
elif mode == "champ":
    items = i.get("projectItems") or []
    valeur = {"item": items[0].get("id") if items else None, "id": i.get("id"), "numero": i.get("number")}[a[1]]
    if valeur is None:
        sys.exit(f"grist-board : {a[0]!r} n'a pas d'élément de tableau")
    print(valeur, end="")
PY
}

statut_de() { interroger statut "$1"; }

# --- écriture du statut -----------------------------------------------------------------------
ecrire_statut() { # <clé> <statut> : sans contrôle de transition
  local item option
  item="$(interroger champ "$1" item)"
  option="$(grist_config_option "$2")"
  gh project item-edit --id "$item" --project-id "$GRIST_PROJECT_ID" \
    --field-id "$GRIST_STATUS_FIELD_ID" --single-select-option-id "$option" >/dev/null
}

cmd_status_get() {
  [ -n "${1:-}" ] || die "usage : status-get <clé>"
  grist_config_charger
  statut_de "$1"
  echo
}

cmd_status_set() {
  local cle="${1:-}" cible="${2:-}" actuel permis
  [ -n "$cle" ] && [ -n "$cible" ] || die "usage : status-set <clé> <statut>"
  case "$cible" in
    backlog | ready | "in progress" | review | test | shipped) ;;
    *) die "statut invalide « $cible » (backlog|ready|in progress|review|test|shipped)" ;;
  esac
  case "$cle" in
    */*) ;;
    *) [ "$cible" != ready ] || die "une story (parent) n'est jamais « ready »" ;;
  esac
  grist_config_charger
  actuel="$(statut_de "$cle")"
  [ "$actuel" != "$cible" ] || return 0
  case "$cle" in
    */*)
      permis="$(transitions_depuis "$actuel")"
      case "|$permis|" in
        *"|$cible|"*) ;;
        *) die "transition interdite « $actuel » → « $cible » pour $cle (permis : ${permis:-aucune})" ;;
      esac
      ;;
  esac
  ecrire_statut "$cle" "$cible"
}

cmd_require_ready() {
  local cle="${1:-}" st
  case "$cle" in
    */*) ;;
    *) die "require-ready ne vaut que pour un ticket <story>/<ticket> (reçu « $cle »)" ;;
  esac
  grist_config_charger
  st="$(statut_de "$cle")"
  case "$st" in
    ready | "in progress") ;;
    *) die "$cle est « $st » (il faut ready ou in progress)" ;;
  esac
}

# --- story dérivée de ses tickets ---------------------------------------------------------------
statut_parent() { # lit un statut de ticket par ligne
  python3 -c "$(cat <<'PY'
import sys
s = [l.strip() for l in sys.stdin if l.strip()]
if s and all(x == "shipped" for x in s):
    print("shipped", end="")
elif s and all(x in ("test", "shipped") for x in s):
    print("test", end="")
elif any(x in ("in progress", "review", "test", "shipped") for x in s):
    print("in progress", end="")
else:
    print("backlog", end="")
PY
)"
}

cmd_parent_sync() {
  local story="${1:-}" voulu actuel
  [ -n "$story" ] || die "usage : parent-sync <story>"
  case "$story" in */*) die "parent-sync attend une clé de story seule" ;; esac
  grist_config_charger
  voulu="$(interroger enfants "$story" | statut_parent)"
  actuel="$(statut_de "$story")" || die "story « $story » introuvable"
  [ "$actuel" = "$voulu" ] || ecrire_statut "$story" "$voulu"
  echo "$voulu"
}

cmd_status_all() {
  grist_config_charger
  interroger tous
}

# --- création d'issues ---------------------------------------------------------------------------
numero_depuis_url() {
  local n="${1##*/issues/}"
  [[ "$n" =~ ^[0-9]+$ ]] || die "URL d'issue illisible : $1"
  echo "$n"
}

# Ajoute l'issue au tableau (une nouvelle tentative) puis la met en backlog ; affiche son numéro.
mettre_au_tableau() { # <url> <clé>
  local url="$1" cle="$2" n essai ajoute=0
  n="$(numero_depuis_url "$url")"
  if [ -n "${GRIST_PROJECT_NUMBER:-}" ]; then
    for essai in 1 2; do
      gh project item-add "$GRIST_PROJECT_NUMBER" --owner "$GRIST_OWNER" --url "$url" --format json \
        >/dev/null 2>&1 && { ajoute=1; break; }
      [ "$essai" = 2 ] || echo "grist-board : ajout de l'issue #$n ($cle) au tableau échoué, nouvelle tentative" >&2
    done
    [ "$ajoute" = 1 ] || echo "grist-board : ALERTE, l'issue #$n ($cle) n'a pas pu être ajoutée au tableau" >&2
  fi
  : >"$CACHE" # l'issue vient d'être créée : relire
  if interroger champ "$cle" item >/dev/null 2>&1; then
    ecrire_statut "$cle" backlog
  else
    echo "grist-board : ALERTE, l'issue #$n ($cle) n'est pas sur le tableau" >&2
  fi
  echo "$n"
}

lien_parent_par_corps() { # <n° enfant> <n° parent> <corps.md> : repli quand les sous-issues manquent
  local tmp
  tmp="$(mktemp)"
  cat "$3" >"$tmp"
  grep -qx "Parent: #$2" "$tmp" || printf '\n\nParent: #%s\n' "$2" >>"$tmp"
  gh label create ticket -R "$(grist_config_depot)" --force >/dev/null 2>&1 \
    || echo "grist-board : ALERTE, étiquette « ticket » non créée" >&2
  gh issue edit "$1" -R "$(grist_config_depot)" --body-file "$tmp" --add-label ticket >/dev/null \
    || echo "grist-board : ALERTE, « Parent: #$2 » non écrit sur l'issue #$1" >&2
  rm -f "$tmp"
}

cmd_issue_create_us() {
  local story="${1:-}" titre="${2:-}" corps="${3:-}" url
  [ -n "$story" ] && [ -n "$titre" ] && [ -n "$corps" ] || die "usage : issue-create-us <story> <titre> <corps.md>"
  [ -f "$corps" ] || die "fichier de corps introuvable : $corps"
  grist_config_charger
  url="$(gh issue create -R "$(grist_config_depot)" -t "[$story] $titre" -F "$corps")"
  mettre_au_tableau "$url" "$story"
}

cmd_issue_create_ticket() {
  local story="${1:-}" ticket="${2:-}" titre="${3:-}" corps="${4:-}" cle url n parent_id enfant_id parent_n
  [ -n "$story" ] && [ -n "$ticket" ] && [ -n "$titre" ] && [ -n "$corps" ] \
    || die "usage : issue-create-ticket <story> <ticket> <titre> <corps.md>"
  [ -f "$corps" ] || die "fichier de corps introuvable : $corps"
  grist_config_charger
  cle="$story/$ticket"
  url="$(gh issue create -R "$(grist_config_depot)" -t "[$cle] $titre" -F "$corps")"
  n="$(mettre_au_tableau "$url" "$cle")"
  if parent_id="$(interroger champ "$story" id 2>/dev/null)"; then
    parent_n="$(interroger champ "$story" numero)"
    enfant_id="$(interroger champ "$cle" id 2>/dev/null || true)"
    if [ -z "$enfant_id" ] || ! gh api graphql \
      -f query='mutation($p:ID!,$c:ID!){addSubIssue(input:{issueId:$p,subIssueId:$c}){issue{id}}}' \
      -f p="$parent_id" -f c="$enfant_id" >/dev/null 2>&1; then
      echo "grist-board : sous-issue indisponible pour $cle, repli sur « Parent: #$parent_n » et l'étiquette ticket" >&2
      lien_parent_par_corps "$n" "$parent_n" "$corps"
    fi
  fi
  echo "$n"
}

# Une issue écrite à la main n'est pas sur le tableau : status-set ne la retrouverait pas.
cmd_issue_adopt() {
  local cle="${1:-}" n="${2:-}" titre="${3:-}"
  [ -n "$cle" ] && [ -n "$n" ] && [ -n "$titre" ] || die "usage : issue-adopt <clé> <n° d'issue> <titre>"
  grist_config_charger
  gh issue edit "$n" -R "$(grist_config_depot)" --title "[$cle] $titre" >/dev/null
  mettre_au_tableau "https://github.com/$(grist_config_depot)/issues/$n" "$cle"
}

cmd="${1:-}"
[ $# -eq 0 ] || shift
case "$cmd" in
  status-get) cmd_status_get "$@" ;;
  status-set) cmd_status_set "$@" ;;
  status-all) cmd_status_all ;;
  require-ready) cmd_require_ready "$@" ;;
  parent-sync) cmd_parent_sync "$@" ;;
  issue-create-us) cmd_issue_create_us "$@" ;;
  issue-create-ticket) cmd_issue_create_ticket "$@" ;;
  issue-adopt) cmd_issue_adopt "$@" ;;
  *) die "usage : grist-board.sh status-get|status-set|status-all|require-ready|parent-sync|issue-create-us|issue-create-ticket|issue-adopt …" ;;
esac
