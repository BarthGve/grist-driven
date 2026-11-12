# Tests de la pose du contenu, de update et uninstall (tâche 12).
# Contenu de test minimal : tests/fixtures/payload/.

PAYLOAD_FIXTURE="$REPO/tests/fixtures/payload"
export GRIST_DRIVEN_PAYLOAD

# Copie la fixture dans un dossier modifiable (pour simuler une nouvelle version).
payload_copie() { GRIST_DRIVEN_PAYLOAD="$FAKE_ROOT/payload"; cp -R "$PAYLOAD_FIXTURE" "$GRIST_DRIVEN_PAYLOAD"; }
init_ok() { run_install init --yes --name demo --design-system dsfr "$@"; }

test_init_pose_commandes_skills_gabarits() {
  payload_copie
  init_ok; assert_rc 0 || return 1
  assert_file .claude/commands/grist-demo.md || return 1
  assert_file .claude/skills/grist-demo/SKILL.md || return 1
  assert_file .grist/lib/outil.sh || return 1
  assert_file templates/doc.md || return 1
  assert_file .grist/templates.orig/doc.md || return 1
  assert_file .grist/manifest || return 1
  grep -qx '.claude/commands/grist-demo.md' .grist/manifest || fail "manifeste incomplet : $(cat .grist/manifest)"
  grep -qx 'templates/doc.md' .grist/manifest || fail "gabarit absent du manifeste"
}

test_update_ecrase_un_gabarit_non_modifie() {
  payload_copie; init_ok
  printf '# Gabarit de test\nversion 2\n' > "$GRIST_DRIVEN_PAYLOAD/templates/doc.md"
  run_install update; assert_rc 0 || return 1
  grep -q 'version 2' templates/doc.md || fail "gabarit non mis à jour"
}

test_update_preserve_un_gabarit_modifie_et_previent() {
  payload_copie; init_ok
  printf 'ma version\n' > templates/doc.md
  printf 'version 2\n' > "$GRIST_DRIVEN_PAYLOAD/templates/doc.md"
  run_install update; assert_rc 0 || return 1
  assert_out "templates/doc.md" || return 1
  [ "$(cat templates/doc.md)" = "ma version" ] || fail "gabarit modifié écrasé"
}

test_force_ecrase_un_gabarit_modifie() {
  payload_copie; init_ok
  printf 'ma version\n' > templates/doc.md
  printf 'version 2\n' > "$GRIST_DRIVEN_PAYLOAD/templates/doc.md"
  run_install update --force; assert_rc 0 || return 1
  [ "$(cat templates/doc.md)" = "version 2" ] || fail "gabarit non écrasé : $(cat templates/doc.md)"
}

test_update_ne_touche_pas_au_code_du_projet() {
  payload_copie; init_ok
  mkdir -p src .claude/commands; echo code > src/app.py; echo perso > .claude/commands/ma-commande.md
  run_install update; assert_rc 0 || return 1
  [ "$(cat src/app.py)" = code ] && [ "$(cat .claude/commands/ma-commande.md)" = perso ] || fail "fichier hors manifeste touché"
}

test_uninstall_retire_seulement_le_manifeste() {
  payload_copie; init_ok
  mkdir -p src .claude/commands; echo code > src/app.py; echo perso > .claude/commands/ma-commande.md
  echo SECRET > .env
  run_install uninstall; assert_rc 0 || return 1
  [ ! -e .claude/commands/grist-demo.md ] && [ ! -e templates ] && [ ! -e .grist ] || fail "contenu posé non retiré : $(ls -A . .claude/commands)"
  [ -f src/app.py ] && [ -f .claude/commands/ma-commande.md ] && [ "$(cat .env)" = SECRET ] || fail "fichier hors manifeste retiré"
}

test_init_relance_est_idempotent() {
  payload_copie; init_ok
  echo "CLE=garde-moi" > .env
  printf 'ma version\n' > templates/doc.md
  local m1; m1=$(cat .grist/manifest)
  init_ok; assert_rc 0 || return 1
  [ "$(cat templates/doc.md)" = "ma version" ] || fail "gabarit modifié écrasé par init"
  [ "$(cat .env)" = "CLE=garde-moi" ] || fail ".env réécrit"
  [ "$(cat .grist/manifest)" = "$m1" ] || fail "manifeste changé"
  [ "$(grep -cx '.env' .gitignore)" = 1 ] || fail ".env dupliqué dans .gitignore"
}
