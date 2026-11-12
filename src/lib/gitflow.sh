# Flux git main/next, hooks git, workflow CI, tableau GitHub (spec §6.2, questions 7 et 8).
# Rien ici n'écrase l'existant sans --force ; aucun échec de gh ne bloque l'installation.

_GF_MARQUE='grist-driven'   # présent dans chaque hook posé par nous

# Dossier source d'un contenu : la charge utile si elle le porte, sinon src/ du repo.
_gf_src() { local p=${GRIST_DRIVEN_PAYLOAD:-$ROOT}; [ -e "$p/$1" ] && echo "$p/$1" || echo "$ROOT/src/$1"; }

_gf_commit() { git -c user.name="${GIT_AUTHOR_NAME:-grist-driven}" -c user.email="${GIT_AUTHOR_EMAIL:-grist-driven@localhost}" commit -q --no-verify "$@"; }

# Crée next depuis main si absent. Ne touche ni à main ni à un next existant.
gitflow_init() {
  if [ "$DRY_RUN" = true ]; then info "[dry-run] flux git : branche next créée depuis main si absente"; return 0; fi
  git rev-parse --git-dir >/dev/null 2>&1 || git init -q -b main
  if ! git rev-parse HEAD >/dev/null 2>&1; then   # dépôt neuf : un premier commit vide pour que next existe
    _gf_commit --allow-empty -m "🔧 CHORE: initialisation"
  fi
  if git show-ref --verify --quiet refs/heads/next; then
    info "grist-driven : la branche next existe déjà, conservée."
    return 0
  fi
  local base=main
  git show-ref --verify --quiet refs/heads/main || base=HEAD
  git branch next "$base"
  info "grist-driven : branche next créée depuis $([ "$base" = main ] && echo main || echo "la branche courante (pas de main)")."
}

# Pose pre-commit et pre-push dans .git/hooks/. Un hook étranger n'est écrasé qu'avec --force (copie .avant-grist).
hooks_poser() {
  if [ "$DRY_RUN" = true ]; then info "[dry-run] hooks git : pre-commit, pre-push"; return 0; fi
  local dir h src dst
  dir=$(git rev-parse --git-path hooks 2>/dev/null) && [ -n "$dir" ] || { info "grist-driven : pas de dépôt git, hooks non posés."; return 0; }
  mkdir -p "$dir"
  for h in pre-commit pre-push; do
    src=$(_gf_src hooks)/$h; dst=$dir/$h
    if [ -e "$dst" ] && ! grep -q "$_GF_MARQUE" "$dst"; then
      if [ "$FORCE" != true ]; then
        info "grist-driven : hook $h existant (pas le nôtre), conservé. --force pour le remplacer (copie dans $h.avant-grist)."
        continue
      fi
      cp "$dst" "$dst.avant-grist"
    fi
    cp "$src" "$dst" && chmod +x "$dst"
  done
}

# uninstall : retire seulement nos hooks.
hooks_retirer() {
  local dir h
  dir=$(git rev-parse --git-path hooks 2>/dev/null) && [ -n "$dir" ] || return 0
  for h in pre-commit pre-push; do
    [ -f "$dir/$h" ] && grep -q "$_GF_MARQUE" "$dir/$h" && rm -f "$dir/$h"
  done
  return 0
}

# Workflow CI : posé s'il n'existe pas (ou avec --force).
ci_poser() {
  if [ "$DRY_RUN" = true ]; then info "[dry-run] CI : .github/workflows/ci.yml"; return 0; fi
  if [ -e .github/workflows/ci.yml ] && [ "$FORCE" != true ]; then
    info "grist-driven : .github/workflows/ci.yml existe, conservé."
    return 0
  fi
  mkdir -p .github/workflows && cp "$(_gf_src ci)/ci.yml" .github/workflows/ci.yml
}

# Tableau GitHub : seulement si gh est connecté ; sinon message et on continue.
tableau_creer() {
  if [ "$DRY_RUN" = true ]; then info "[dry-run] tableau GitHub créé via gh si connecté"; return 0; fi
  if ! gh auth status >/dev/null 2>&1; then
    info "grist-driven : gh n'est pas connecté : tableau GitHub non créé. Lancer « gh auth login » puis .grist/lib/grist-init.sh run."
    return 0
  fi
  local init=.grist/lib/grist-init.sh args="--yes"
  [ -f "$init" ] || init=$(_gf_src lib)/grist-init.sh
  git remote get-url origin >/dev/null 2>&1 || args="--no-remote --yes"   # jamais de dépôt distant créé sans origin
  # shellcheck disable=SC2086
  bash "$init" run $args || info "grist-driven : création du tableau échouée : relancer .grist/lib/grist-init.sh run."
}

# Étape d'init : selon les réponses du questionnaire.
gitflow_etape() {
  [ "$GIT_FLOW" = true ] && { gitflow_init; tableau_creer; }
  [ "$HOOKS" = true ] && hooks_poser
  [ "$CI" = true ] && ci_poser
  return 0
}
