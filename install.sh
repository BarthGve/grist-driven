#!/usr/bin/env bash
# grist-driven — installeur.
# Usage : install.sh [init|update|doctor|uninstall] [--yes] [--dry-run] [--force]
#   réponses : --name --api-host --org --design-system dsfr|ui-kit
#              --mcp existing|install|coder|none --mcp-scope project|user --doc-id
#              --git-flow|--no-git-flow --hooks|--no-hooks --ci|--no-ci
# La clé d'API vient de GRIST_API_KEY (environnement) ou d'une saisie masquée ;
# jamais d'un drapeau, jamais affichée.
# Codes de sortie : 0 succès, 2 réponse manquante ou invalide, 3 prérequis manquant.
set -euo pipefail

ROOT=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
for f in questions prereqs config payload; do . "$ROOT/src/lib/$f.sh"; done

die() { local c=$1; shift; printf 'grist-driven : %s\n' "$*" >&2; exit "$c"; }
info() { printf '%s\n' "$*"; }

MODE=init YES=false DRY_RUN=false FORCE=false
NAME="" ORG="" API_HOST="" DESIGN_SYSTEM="" MCP="" MCP_SCOPE="" DOC_ID=""
GIT_FLOW="" HOOKS="" CI=""

parse_args() {
  case "${1:-}" in init|update|doctor|uninstall) MODE=$1; shift;; esac
  while [ $# -gt 0 ]; do
    local a=$1 v=""
    case $a in --*=*) v=${a#*=}; a=${a%%=*};; esac
    case $a in
      --yes) YES=true;; --dry-run) DRY_RUN=true;; --force) FORCE=true;;
      --git-flow) GIT_FLOW=true;; --no-git-flow) GIT_FLOW=false;;
      --hooks) HOOKS=true;; --no-hooks) HOOKS=false;;
      --ci) CI=true;; --no-ci) CI=false;;
      --name|--org|--api-host|--design-system|--mcp|--mcp-scope|--doc-id)
        if [ -z "$v" ] && [[ "$1" != *=* ]]; then
          [ $# -ge 2 ] || die 2 "$a attend une valeur"; v=$2; shift
        fi
        case $a in
          --name) NAME=$v;; --org) ORG=$v;; --api-host) API_HOST=$v;;
          --design-system) DESIGN_SYSTEM=$v;; --mcp) MCP=$v;;
          --mcp-scope) MCP_SCOPE=$v;; --doc-id) DOC_ID=$v;;
        esac;;
      *) die 2 "option inconnue : $a";;
    esac
    shift
  done
}

mode_init() {
  poser_questions
  verifier_prerequis
  if [ "$DRY_RUN" = true ]; then
    info "[dry-run] rien n'est écrit. Seraient écrits : .grist-driven.json, .gitignore (.env)"
    config_json
    info "clé d'API : $([ -n "${GRIST_API_KEY:-}" ] && echo fournie || echo plus tard) (jamais affichée)"
    payload_pose "${GRIST_DRIVEN_PAYLOAD:-$ROOT}" "$PWD"
    return 0
  fi
  ignorer_env
  ecrire_config
  info "grist-driven : .grist-driven.json écrit (design system : $DESIGN_SYSTEM)."
  payload_pose "${GRIST_DRIVEN_PAYLOAD:-$ROOT}" "$PWD"
  # Étapes à venir, branchées ici une à une : MCP (13), gabarit (14).
}

# Squelette doctor : remplacé par la tâche 16.
mode_update() {
  [ -f .grist-driven.json ] || die 2 "projet non initialisé : lancer d'abord « install.sh init »."
  payload_pose "${GRIST_DRIVEN_PAYLOAD:-$ROOT}" "$PWD"
}
mode_doctor()    { info "doctor : arrive avec la tâche 16."; }
mode_uninstall() { payload_retire; }

main() { parse_args "$@"; "mode_$MODE"; }
main "$@"
