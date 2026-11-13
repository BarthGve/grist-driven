# Tests du flux git, des hooks, de la CI et du tableau (tâche 15).
# Le git de fake_env est factice : on lie le vrai git le temps de ces tests.

REAL_GIT=$(command -v git)
export GIT_AUTHOR_NAME=t GIT_AUTHOR_EMAIL=t@t GIT_COMMITTER_NAME=t GIT_COMMITTER_EMAIL=t@t

gf_vrai_git() { fake_cmd git "exec \"$REAL_GIT\" \"\$@\""; }
# Dépôt avec un commit sur main ; gate factice qui accepte tout.
gf_depot() {
  gf_vrai_git; git init -q -b main; echo a > a.txt; git add a.txt; git commit -q -m base
}
gf_gate_factice() {
  mkdir -p .grist/hooks; printf '#!/bin/bash\nexit 0\n' > .grist/hooks/grist-gate.sh
}
gf_init() { run_install init --yes --name demo --design-system dsfr --mcp none --git-flow --hooks --no-ci "$@"; }

test_next_cree_sans_toucher_main() {
  gf_depot; local avant; avant=$(git rev-parse main)
  fake_cmd gh 'exit 1'
  gf_init; assert_rc 0 || return 1
  [ "$(git rev-parse main)" = "$avant" ] || fail "main a bougé"
  [ "$(git rev-parse next)" = "$avant" ] || fail "next absent ou pas sur main"
  echo b > b.txt; git add b.txt; git commit -q -m deux; local n; n=$(git rev-parse next)
  gf_init; assert_rc 0 || return 1
  [ "$(git rev-parse next)" = "$n" ] || fail "next existant modifié"
}

test_hook_refuse_env_dans_l_index() {
  gf_depot; fake_cmd gh 'exit 1'; gf_init >/dev/null; gf_gate_factice
  echo "GRIST_API_KEY=" > .env; git add -f .env
  OUT=$(git commit -m x 2>&1); RC=$?
  assert_rc 1 || return 1; assert_out ".env" || return 1
}

test_hook_refuse_cle_en_clair() {
  gf_depot; fake_cmd gh 'exit 1'; gf_init >/dev/null; gf_gate_factice
  echo "GRIST_API_KEY=abcdef123456" > exemple.txt; git add exemple.txt
  OUT=$(git commit -m x 2>&1); RC=$?
  assert_rc 1 || return 1; assert_out "GRIST_API_KEY" || return 1
  case "$OUT" in *abcdef123456*) fail "la clé est réaffichée";; esac
  echo "GRIST_API_KEY=" > exemple.txt; echo '"k": "${GRIST_API_KEY}"' >> exemple.txt; git add exemple.txt
  OUT=$(git commit -m x 2>&1); RC=$?; assert_rc 0 || return 1
}

test_hook_etranger_non_ecrase() {
  gf_depot; mkdir -p .git/hooks; printf '#!/bin/sh\n# mien\n' > .git/hooks/pre-commit
  fake_cmd gh 'exit 1'
  gf_init; assert_rc 0 || return 1
  grep -q mien .git/hooks/pre-commit || fail "hook étranger écrasé"
  assert_out "pre-commit" || return 1
  grep -q grist-driven .git/hooks/pre-push || fail "pre-push non posé"
  gf_init --force; assert_rc 0 || return 1
  grep -q grist-driven .git/hooks/pre-commit || fail "--force n'a pas remplacé le hook"
  grep -q mien .git/hooks/pre-commit.avant-grist || fail "pas de copie de l'ancien hook"
}

test_sans_gh_connecte_continue_avec_message() {
  gf_depot; fake_cmd gh '[ "$1" = auth ] && exit 1; exit 0'
  gf_init; assert_rc 0 || return 1
  assert_out "gh n'est pas connecté" || return 1
  [ ! -e .grist/config.json ] || fail "tableau créé sans gh"
}

test_avec_gh_connecte_lance_la_creation_du_tableau() {
  gf_depot; fake_cmd gh 'exit 0'
  export GRIST_DRIVEN_PAYLOAD="$FAKE_ROOT/vide"; mkdir -p "$GRIST_DRIVEN_PAYLOAD"   # sinon la vraie lib écrase le stub
  mkdir -p .grist/lib; printf '#!/bin/bash\necho "$@" > appel.txt\n' > .grist/lib/grist-init.sh
  gf_init; assert_rc 0 || return 1
  [ "$(cat appel.txt)" = "run --no-remote --yes" ] || fail "appel : $(cat appel.txt 2>&1)"
}

test_ci_posee_sans_ecraser() {
  gf_depot; fake_cmd gh 'exit 1'
  run_install init --yes --name demo --design-system dsfr --mcp none --no-git-flow --no-hooks --ci; assert_rc 0 || return 1
  assert_file .github/workflows/ci.yml || return 1
  echo perso > .github/workflows/ci.yml
  run_install init --yes --name demo --design-system dsfr --mcp none --no-git-flow --no-hooks --ci; assert_rc 0 || return 1
  [ "$(cat .github/workflows/ci.yml)" = perso ] || fail "CI existante écrasée"
}

test_uninstall_retire_nos_hooks_seulement() {
  gf_depot; mkdir -p .git/hooks; printf '#!/bin/sh\n# mien\n' > .git/hooks/pre-commit
  fake_cmd gh 'exit 1'; gf_init >/dev/null
  run_install uninstall; assert_rc 0 || return 1
  [ ! -e .git/hooks/pre-push ] || fail "pre-push resté"
  grep -q mien .git/hooks/pre-commit || fail "hook étranger retiré"
}
