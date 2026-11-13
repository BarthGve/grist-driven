# Tests de install.sh : modes, prérequis, questionnaire (tâche 11).
# Chargé par run.sh ; chaque fonction test_* tourne dans un projet temporaire.

FLAGS_OK="--yes --name demo --org docs --design-system dsfr"

test_sans_terminal_ni_yes_echoue_code_2() {
  run_install init
  assert_rc 2 || return 1
  assert_out "--yes et --design-system" || return 1
  [ ! -e .grist-driven.json ] || fail "fichier écrit malgré l'échec"
}

test_yes_sans_design_system_echoue_code_2() {
  run_install init --yes --name demo
  assert_rc 2 || return 1
  assert_out "design-system" || return 1
  [ ! -e .grist-driven.json ] || fail "fichier écrit malgré l'échec"
}

test_yes_avec_drapeaux_ecrit_grist_driven_json() {
  run_install init --yes --name demo --org monorg --design-system ui-kit \
    --mcp coder --mcp-scope user --no-git-flow --no-hooks --ci
  assert_rc 0 || return 1
  assert_file .grist-driven.json || return 1
  local j; j=$(cat .grist-driven.json)
  for want in '"app": "demo"' '"package": "demo"' '"design_system": "ui-kit"' \
    '"api_host": "https://grist.numerique.gouv.fr/o/monorg/api"' '"mcp": "coder"' \
    '"mcp_scope": "user"' '"git_flow": false' '"hooks": false' '"ci": true' "\"version\": \"$(tr -d '[:space:]' < "$REPO/VERSION")\""; do
    case "$j" in *"$want"*) ;; *) fail "json sans $want : $j"; return 1;; esac
  done
  grep -qx '.env' .gitignore || fail ".env non ignoré"
}

test_prerequis_manquant_code_3() {
  FAKE_PY_VERSION=3.10.4 run_install init $FLAGS_OK
  assert_rc 3 || return 1
  assert_out "python" || return 1
  fake_cmd python3 'echo "Python 3.12.1"'
  unfake_cmd git
  run_install init $FLAGS_OK
  assert_rc 3 || return 1
  assert_out "git" || return 1
  [ ! -e .grist-driven.json ] || fail "fichier écrit malgré l'échec"
}

test_dry_run_n_ecrit_aucun_fichier() {
  run_install init $FLAGS_OK --dry-run
  assert_rc 0 || return 1
  [ -z "$(ls -A)" ] || fail "fichiers écrits : $(ls -A)"
}

test_design_system_invalide_refuse() {
  run_install init --yes --name demo --design-system bootstrap
  assert_rc 2 || return 1
  assert_out "dsfr" || return 1
}

test_la_cle_n_apparait_pas_dans_la_sortie_ni_les_fichiers_dry_run() {
  local k="CLE-SECRETE-DE-TEST-123"
  GRIST_API_KEY=$k run_install init $FLAGS_OK --dry-run
  assert_rc 0 || return 1
  case "$OUT" in *"$k"*) fail "clé dans la sortie"; return 1;; esac
  GRIST_API_KEY=$k run_install init $FLAGS_OK
  assert_rc 0 || return 1
  case "$OUT" in *"$k"*) fail "clé dans la sortie"; return 1;; esac
  ! grep -rq --exclude=.env "$k" . || fail "clé écrite ailleurs que dans .env"
}

# --- tests en plus du plan -------------------------------------------------
test_le_drapeau_cle_api_n_existe_pas() {
  run_install init $FLAGS_OK --api-key abc
  assert_rc 2 || return 1
}

test_questionnaire_interactif_lit_le_terminal() {
  printf '%s\n' "monapp" "monorg" "" "dsfr" "" "" "" "" "n" "n" "n" > "$FAKE_ROOT/rep"
  GRIST_DRIVEN_TTY="$FAKE_ROOT/rep" run_install init
  assert_rc 0 || return 1
  local j; j=$(cat .grist-driven.json)
  for want in '"app": "monapp"' '"design_system": "dsfr"' '"git_flow": false' '"ci": false'; do
    case "$j" in *"$want"*) ;; *) fail "json sans $want : $j"; return 1;; esac
  done
}
