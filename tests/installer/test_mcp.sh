# Tests de l'installation et de la déclaration du MCP (tâche 13).
# Binaires factices pipx/uv/pip/claude : aucun réseau, aucune vraie installation.
# Les appels sont consignés dans $FAKE_ROOT/calls.

MCP_FLAGS="--yes --name demo --org docs --design-system dsfr --no-git-flow --no-hooks --no-ci"

# fake_enregistreur <cmd> [corps supplémentaire]
fake_enregistreur() { fake_cmd "$1" "echo \"$1 \$*\" >> $FAKE_ROOT/calls; ${2:-}"; }
appels() { cat "$FAKE_ROOT/calls" 2>/dev/null; }
assert_appel() { case "$(appels)" in *"$1"*) ;; *) fail "appel « $1 » absent : $(appels)";; esac; }
assert_aucun_appel() { [ -z "$(appels)" ] || fail "appels inattendus : $(appels)"; }

test_deja_installe_ne_reinstalle_pas() {
  fake_cmd mcp-server-grist 'exit 0'
  fake_enregistreur pipx
  run_install init $MCP_FLAGS --mcp install
  assert_rc 0 || return 1
  assert_aucun_appel || return 1
  grep -q '"grist"' .mcp.json || fail ".mcp.json non posé"
}

test_installe_avec_pipx_puis_declare_dans_mcp_json() {
  fake_enregistreur pipx
  fake_enregistreur uv
  run_install init $MCP_FLAGS --mcp install
  assert_rc 0 || return 1
  assert_appel "pipx install --force mcp-server-grist==0.2.2" || return 1
  case "$(appels)" in *uv*) fail "uv appelé alors que pipx est là"; return 1;; esac
  grep -q '"command": "mcp-server-grist"' .mcp.json || fail ".mcp.json sans le serveur"
}

test_repli_uv_si_pas_de_pipx() {
  fake_enregistreur uv
  run_install init $MCP_FLAGS --mcp install
  assert_rc 0 || return 1
  assert_appel "uv tool install --force mcp-server-grist==0.2.2" || return 1
  assert_file .mcp.json
}

test_pep668_sans_outils_affiche_la_commande_et_continue() {
  mkdir -p "$FAKE_ROOT/stdlib"; : > "$FAKE_ROOT/stdlib/EXTERNALLY-MANAGED"
  fake_cmd python3 'case "$*" in *-c*) echo "$FAKE_STDLIB";; *) echo "Python 3.12.1";; esac'
  fake_enregistreur pip
  FAKE_STDLIB="$FAKE_ROOT/stdlib" run_install init $MCP_FLAGS --mcp install
  assert_rc 0 || return 1
  assert_aucun_appel || return 1
  assert_out "pipx install mcp-server-grist==0.2.2" || return 1
  assert_file .grist-driven.json || return 1
  [ ! -e .mcp.json ] || fail ".mcp.json posé alors que le serveur n'est pas installé"
}

test_pip_user_en_dernier_recours() {
  fake_enregistreur pip
  run_install init $MCP_FLAGS --mcp install
  assert_rc 0 || return 1
  assert_appel "pip install --user mcp-server-grist==0.2.2"
}

test_refus_n_installe_rien() {
  fake_enregistreur pipx
  printf '%s\n' monapp monorg "" dsfr "" "" "" "" n n n n > "$FAKE_ROOT/rep"
  GRIST_DRIVEN_TTY="$FAKE_ROOT/rep" run_install init
  assert_rc 0 || return 1
  assert_aucun_appel || return 1
  assert_out "pipx install mcp-server-grist==0.2.2" || return 1
  assert_file .grist-driven.json
}

test_mcp_json_ne_contient_que_des_variables() {
  local k="CLE-SECRETE-DE-TEST-123"
  fake_cmd mcp-server-grist 'exit 0'
  GRIST_API_KEY=$k run_install init $MCP_FLAGS --mcp install --api-host https://hote.example/o/x/api
  assert_rc 0 || return 1
  grep -q '${GRIST_API_KEY}' .mcp.json && grep -q '${GRIST_API_HOST}' .mcp.json || fail "variables absentes"
  ! grep -q "$k" .mcp.json || fail "clé dans .mcp.json"
  ! grep -q 'hote.example' .mcp.json || fail "hôte littéral dans .mcp.json"
  case "$OUT" in *"$k"*) fail "clé dans la sortie"; return 1;; esac
}

test_portee_utilisateur_appelle_claude_mcp_add() {
  fake_cmd mcp-server-grist 'exit 0'
  fake_enregistreur claude
  run_install init $MCP_FLAGS --mcp install --mcp-scope user
  assert_rc 0 || return 1
  assert_appel "claude mcp add --scope user grist" || return 1
  assert_appel 'GRIST_API_KEY=${GRIST_API_KEY}' || return 1
  [ ! -e .mcp.json ] || fail ".mcp.json posé en portée utilisateur"
}

test_portee_utilisateur_sans_claude_affiche_la_commande() {
  fake_cmd mcp-server-grist 'exit 0'
  run_install init $MCP_FLAGS --mcp install --mcp-scope user
  assert_rc 0 || return 1
  assert_out "claude mcp add --scope user grist" || return 1
}

test_option_none_ne_pose_rien() {
  fake_enregistreur pipx
  fake_enregistreur claude
  run_install init $MCP_FLAGS --mcp none
  assert_rc 0 || return 1
  assert_aucun_appel || return 1
  [ ! -e .mcp.json ] || fail ".mcp.json posé avec --mcp none"
}

test_coder_pose_la_declaration_http_sans_installer() {
  fake_enregistreur pipx
  run_install init $MCP_FLAGS --mcp coder
  assert_rc 0 || return 1
  assert_aucun_appel || return 1
  grep -q '"grist-coder"' .mcp.json && grep -q '"type": "http"' .mcp.json || fail "déclaration HTTP absente"
  assert_out "grist-coder" || return 1
}

test_update_aligne_la_version_du_mcp_sur_l_epinglage() {
  fake_enregistreur pipx 'case "$*" in "list --short") echo "mcp-server-grist ${FAKE_MCP_V:-0.1.0}";; esac'
  run_install init $MCP_FLAGS --mcp install
  assert_rc 0 || return 1
  : > "$FAKE_ROOT/calls"
  FAKE_MCP_V=0.1.0 run_install update --yes
  assert_rc 0 || return 1
  assert_appel "pipx install --force mcp-server-grist==0.2.2" || return 1
  : > "$FAKE_ROOT/calls"
  FAKE_MCP_V=0.2.2 run_install update --yes
  assert_rc 0 || return 1
  case "$(appels)" in *"install"*) fail "réinstallation alors que la version est alignée : $(appels)"; return 1;; esac
}

test_update_sans_accord_ne_reinstalle_pas() {
  fake_enregistreur pipx 'case "$*" in "list --short") echo "mcp-server-grist 0.1.0";; esac'
  run_install init $MCP_FLAGS --mcp install
  : > "$FAKE_ROOT/calls"
  run_install update
  assert_rc 0 || return 1
  case "$(appels)" in *"install"*) fail "réinstallé sans accord"; return 1;; esac
  assert_out "pipx install --force mcp-server-grist==0.2.2" || return 1
}
