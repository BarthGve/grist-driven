# Tests du gabarit de projet et de .env (tâche 14). python3 factice : pas de .venv ici
# (l'installation réelle du kit est couverte par tests/test_projet_genere.py).

sc_init() { run_install init --yes --name "${SC_NAME:-demo}" --design-system "${SC_DS:-dsfr}" --mcp none \
  --no-git-flow --no-hooks --no-ci "$@"; }

test_env_existant_jamais_reecrit() {
  printf 'GRIST_API_KEY=ancienne\n' > .env
  GRIST_API_KEY=nouvelle sc_init; assert_rc 0 || return 1
  [ "$(cat .env)" = "GRIST_API_KEY=ancienne" ] || fail ".env réécrit : $(cat .env)"
}

test_env_cree_ignore_par_git_avant_ecriture() {
  GRIST_API_KEY=secretxyz sc_init --doc-id abc123; assert_rc 0 || return 1
  grep -qx '.env' .gitignore || fail ".env non ignoré"
  grep -qx 'GRIST_API_KEY=secretxyz' .env || fail "clé absente de .env"
  grep -qx 'GRIST_DOC_ID=abc123' .env || fail "document absent de .env"
  [ "$(ls -l .env | cut -c1-10)" = "-rw-------" ] || fail "droits de .env : $(ls -l .env)"
  case "$OUT" in *secretxyz*) fail "la clé est affichée";; esac
  # .gitignore sans .env et impossible à compléter : rien n'est écrit.
  rm -rf .env .gitignore .grist-driven.json; : > .gitignore; chmod 444 .gitignore
  GRIST_API_KEY=secretxyz sc_init
  [ "$RC" -ne 0 ] || fail "échec attendu"
  [ ! -e .env ] || fail ".env écrit avant d'être ignoré"
}

test_substitution_app_et_package() {
  SC_NAME="Mon App" sc_init; assert_rc 0 || return 1
  assert_file mon_app/schema.py || return 1
  assert_file mon_app/acl_rules.py || return 1
  assert_file mon_app/__init__.py || return 1
  grep -q '"package": "mon_app"' .grist-driven.json || fail "package absent de la config"
  grep -q 'Mon App' AGENTS.md || fail "app non substituée dans AGENTS.md"
  [ "$(cat CLAUDE.md)" = "@AGENTS.md" ] || fail "CLAUDE.md"
  ! grep -rq '{{' mon_app AGENTS.md widgets tests .env.example widgets.json pytest.ini || fail "marqueur {{…}} restant"
  assert_file .env.example || return 1
  grep -q '^GRIST_DOC_ID=' .env.example || fail ".env.example incomplet"
  grep -q '"widgets": {}' widgets.json || fail "widgets.json"
}

test_profil_dsfr_pose_widgets_html() {
  SC_DS=dsfr sc_init; assert_rc 0 || return 1
  assert_file widgets/exemple.html || return 1
  assert_file widgets/core.js || return 1
  assert_file tests/core.test.js || return 1
  grep -q '@gouvfr/dsfr@1.14.4' widgets/exemple.html || fail "DSFR 1.14.4 non épinglé"
  grep -q 'CORE BEGIN' widgets/exemple.html || fail "marqueurs CORE absents"
  [ ! -e widgets_ui ] || fail "widgets_ui posé pour dsfr"
}

test_profil_uikit_pose_widgets_ui() {
  SC_DS=ui-kit sc_init; assert_rc 0 || return 1
  local f; for f in package.json build.mjs vite.config.ts tsconfig.json src/exemple.html src/exemple.tsx; do
    assert_file "widgets_ui/$f" || return 1
  done
  grep -q '@gouvfr-lasuite/ui-components' widgets_ui/package.json || fail "dépendance ui-kit absente"
  [ ! -e widgets ] || fail "widgets/ posé pour ui-kit"
}

test_scaffold_relance_n_ecrase_pas_les_fichiers_du_projet() {
  sc_init; assert_rc 0 || return 1
  echo '# modifié' >> demo/schema.py; echo 'mien' > widgets/exemple.html
  sc_init --force; assert_rc 0 || return 1
  grep -q '# modifié' demo/schema.py || fail "schema.py écrasé"
  [ "$(cat widgets/exemple.html)" = mien ] || fail "widget écrasé"
}

test_dry_run_n_ecrit_aucun_gabarit() {
  sc_init --dry-run; assert_rc 0 || return 1
  [ ! -e demo ] && [ ! -e .env ] && [ ! -e AGENTS.md ] || fail "fichiers écrits en dry-run"
  assert_out "gabarit" || return 1
}
