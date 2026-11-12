#!/usr/bin/env bash
# grist-gate : garde-fous du flux, appliqués par git (hooks pre-commit et pre-push).
#
# Branches : main = production (mise à jour par next seulement) ; next = intégration ;
# feature/<story> = cadrage, documents seulement ; feature/<story>/<ticket> = code d'un ticket.
#
#   grist-gate.sh pre-commit               refuse le code sans plan validé ni ticket prêt
#   grist-gate.sh pre-push                 lit les références poussées sur l'entrée standard
#   grist-gate.sh plan-validated <id>      docs/plans/<story>.md contient « validated: yes »
#   grist-gate.sh ship-allowed <id>        dernier verdict de docs/reviews/<id>.md : « Ship allowed: yes »
#   grist-gate.sh ready-ok [story/ticket]  ticket ready ou in progress sur le tableau
set -euo pipefail

PROD=main
INTEGRATION=next

racine() { git rev-parse --show-toplevel 2>/dev/null || pwd; }
refus() { echo "grist-gate : $*" >&2; return 1; }

# feature/<story>[/<ticket>] → <story>[/<ticket>] ; autre branche → vide
id_de_branche() { case "$1" in feature/*) printf '%s' "${1#feature/}" ;; esac; }
story_de() { printf '%s' "${1%%/*}"; }
ticket_de() { case "$1" in */*) printf '%s' "${1#*/}" ;; esac; }

# Le tableau s'installe dans .grist/lib ; à défaut, le dossier lib voisin de ce hook.
trouver_tableau() {
  local ici
  ici="$(CDPATH= cd -- "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
  local c
  for c in "$(racine)/.grist/lib/grist-board.sh" "$ici/../lib/grist-board.sh"; do
    [ -f "$c" ] && { printf '%s' "$c"; return 0; }
  done
  return 1
}

plan_valide() {
  local story plan
  story="$(story_de "$1")"
  plan="$(racine)/docs/plans/$story.md"
  [ -f "$plan" ] || refus "pas de plan pour « $story » (docs/plans/$story.md absent) ; lancer /grist-plan $story" || return 1
  grep -qE '^validated:[[:space:]]*yes[[:space:]]*$' "$plan" \
    || refus "plan « $story » non validé (« validated: yes » absent de docs/plans/$story.md)" || return 1
}

# Les tours de relecture s'ajoutent au fichier : seul le dernier verdict compte.
livraison_permise() {
  local revue
  revue="$(racine)/docs/reviews/$1.md"
  [ -f "$revue" ] || refus "pas de revue pour « $1 » (docs/reviews/$1.md absent) ; lancer /grist-review $1" || return 1
  [ "$(grep -E '^Ship allowed:' "$revue" | tail -n 1 | tr -d '[:space:]')" = "Shipallowed:yes" ] \
    || refus "livraison bloquée pour « $1 » : dernier verdict de docs/reviews/$1.md différent de « Ship allowed: yes »" || return 1
}

doc_produit_present() {
  local story
  story="$(story_de "$1")"
  [ -f "$(racine)/docs/product/$story.md" ] \
    || refus "docs/product/$story.md absent : un ticket ne rejoint next qu'avec le document produit de sa story" || return 1
}

# Version : VERSION doit avoir changé depuis main, et CHANGELOG.md (s'il existe) la mentionner.
version_publiable() {
  local tete="$1" base="${2:-}" v_tete v_base=""
  v_tete="$(git show "$tete:VERSION" 2>/dev/null | tr -d '[:space:]' || true)"
  [ -z "$base" ] || v_base="$(git show "$base:VERSION" 2>/dev/null | tr -d '[:space:]' || true)"
  [ -n "$v_tete" ] || refus "VERSION absent de $INTEGRATION" || return 1
  [ "$v_tete" != "$v_base" ] || refus "VERSION inchangé depuis $PROD ($v_tete) : incrémenter avant de publier" || return 1
  if git cat-file -e "$tete:CHANGELOG.md" 2>/dev/null && ! git show "$tete:CHANGELOG.md" | grep -Fq "$v_tete"; then
    refus "CHANGELOG.md ne mentionne pas $v_tete" || return 1
  fi
}

# Ticket prêt sur le tableau. Sans .grist/config.json le tableau n'existe pas encore : porte levée.
ticket_pret() {
  local id="${1:-}" tableau statut
  if [ ! -f "$(racine)/.grist/config.json" ]; then
    echo "grist-gate : pas de .grist/config.json, porte « ticket prêt » ignorée (lancer /grist-init)" >&2
    return 0
  fi
  [ -n "$id" ] || id="$(id_de_branche "$(git rev-parse --abbrev-ref HEAD 2>/dev/null || true)")"
  case "$id" in */*) ;; *) return 0 ;; esac # une story n'est jamais « prête » : seuls les tickets le sont
  tableau="$(trouver_tableau)" || refus "tableau configuré mais grist-board.sh introuvable : « $id » invérifiable" || return 1
  statut="$(GRIST_RACINE="$(racine)" "$tableau" status-get "$id" 2>/dev/null | head -n1 | tr -d '\r')" \
    || refus "statut de « $id » illisible sur le tableau (il faut ready ou in progress)" || return 1
  case "$statut" in
    ready | "in progress") ;;
    *) refus "« $id » est « ${statut:-inconnu} » sur le tableau (il faut ready ou in progress)" || return 1 ;;
  esac
}

pre_commit() {
  local branche id fichier code=0
  branche="$(git rev-parse --abbrev-ref HEAD 2>/dev/null || true)"
  id="$(id_de_branche "$branche")"
  [ -n "$id" ] || return 0 # hors flux (correctif direct sur next, par exemple)
  while IFS= read -r fichier; do
    case "$fichier" in "" | docs/*) ;; *) code=1 ;; esac
  done < <(git diff --cached --name-only)
  [ "$code" = 1 ] || return 0 # les commits de documents passent toujours
  [ -n "$(ticket_de "$id")" ] \
    || refus "code refusé sur $branche : une branche de cadrage ne reçoit que des documents (le code va sur feature/<story>/<ticket>)" || return 1
  plan_valide "$id" || return 1
  ticket_pret "$id"
}

pre_push() {
  local ref_locale sha_local ref_distante sha_distant rc=0 zero=0000000000000000000000000000000000000000
  local plage id branche
  while read -r ref_locale sha_local ref_distante sha_distant; do
    [ -n "${ref_locale:-}" ] && [ "$sha_local" != "$zero" ] || continue
    [ "$sha_distant" != "$zero" ] || sha_distant=""

    if [ "$ref_distante" = "refs/heads/$PROD" ]; then
      if [ "$ref_locale" != "refs/heads/$INTEGRATION" ]; then
        refus "push vers $PROD depuis ${ref_locale#refs/heads/} refusé : seule $INTEGRATION met la production à jour" || rc=1
      else
        version_publiable "$sha_local" "$sha_distant" || rc=1
      fi
      continue
    fi

    [ "$ref_distante" = "refs/heads/$INTEGRATION" ] || continue
    plage="${sha_distant:+$sha_distant..}$sha_local"
    branche="${ref_locale#refs/heads/}"
    id="$(id_de_branche "$branche")"
    if [ -n "$(ticket_de "$id")" ]; then # branche de ticket : revue passée et document produit obligatoires
      livraison_permise "$id" || rc=1
      doc_produit_present "$id" || rc=1
    fi
    # Tickets fusionnés dans la plage poussée : même exigence.
    while IFS= read -r id; do
      case "$id" in */*) livraison_permise "$id" || rc=1; doc_produit_present "$id" || rc=1 ;; esac
    done < <(git log --merges --format='%s' "$plage" 2>/dev/null \
      | sed -n "s#.*Merge branch 'feature/\([^']*\)'.*#\1#p" | sort -u)
  done
  return "$rc"
}

case "${1:-}" in
  pre-commit) pre_commit ;;
  pre-push) pre_push ;;
  plan-validated) plan_valide "${2:?identifiant de story requis}" ;;
  ship-allowed) livraison_permise "${2:?identifiant de story ou de ticket requis}" ;;
  ready-ok) ticket_pret "${2:-}" ;;
  *)
    echo "usage : grist-gate.sh pre-commit | pre-push | plan-validated <id> | ship-allowed <id> | ready-ok [story/ticket]" >&2
    exit 2
    ;;
esac
