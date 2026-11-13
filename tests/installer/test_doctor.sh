# Tests de « install.sh doctor » (tâche 16). Serveur Grist factice : python -m http.server local.
DOC_PY=$(command -v python3)   # le vrai python (fake_env en pose un factice dans le PATH)
DOC_KEY=cle-secrete-de-test

# Démarre le serveur factice (document « d1 » lisible) ; pose DOC_PORT. Arrêté à la fin du test.
doc_serveur() {
  mkdir -p "$FAKE_ROOT/srv/docs/d1"; echo '{"tables":[]}' > "$FAKE_ROOT/srv/docs/d1/tables"
  DOC_PORT=$("$DOC_PY" -c 'import socket;s=socket.socket();s.bind(("127.0.0.1",0));print(s.getsockname()[1])')
  "$DOC_PY" -m http.server "$DOC_PORT" --bind 127.0.0.1 --directory "$FAKE_ROOT/srv" >/dev/null 2>&1 &
  trap 'kill $! 2>/dev/null' EXIT
  local i; for i in 1 2 3 4 5 6 7 8 9 10; do curl -s -o /dev/null "http://127.0.0.1:$DOC_PORT/" && return 0; sleep 0.3; done
  fail "serveur factice muet"
}

# Projet initialisé complet. $1 = adresse API (défaut : serveur factice), $2 = clé, $3 = doc.
doc_projet() {
  local host=${1:-http://127.0.0.1:$DOC_PORT} key=${2-$DOC_KEY} doc=${3-d1}
  printf '{\n  "version": "0.1.0",\n  "mcp": "install"\n}\n' > .grist-driven.json
  printf 'GRIST_API_KEY=%s\nGRIST_API_HOST=%s\nGRIST_DOC_ID=%s\n' "$key" "$host" "$doc" > .env
  printf '{"mcpServers":{"grist":{"command":"mcp-server-grist"}}}\n' > .mcp.json
  mkdir -p .grist .venv/bin
  echo x > .grist/lib.sh; printf '.grist/lib.sh\n' > .grist/manifest
  printf '#!/bin/bash\necho 0.1.0\n' > .venv/bin/python; chmod +x .venv/bin/python
  fake_cmd mcp-server-grist 'exit 0'
}

test_tout_ok_code_0() {
  doc_serveur || return 1; doc_projet
  run_install doctor; assert_rc 0 || return 1
  assert_out "OK  API Grist joignable" || return 1
  assert_out "OK  manifeste cohérent" || return 1
  case "$OUT" in *KO*|*"$DOC_KEY"*) fail "KO ou clé dans la sortie : $OUT";; esac
}

test_cle_absente_ko_sans_afficher_de_valeur() {
  doc_serveur || return 1; doc_projet "" "" ""
  printf 'GRIST_API_KEY=\nGRIST_API_HOST=http://127.0.0.1:%s\nGRIST_DOC_ID=d1\n' "$DOC_PORT" > .env
  run_install doctor; assert_rc 1 || return 1
  assert_out "KO  GRIST_API_KEY absente" || return 1
  case "$OUT" in *"127.0.0.1"*) fail "valeur de .env affichée : $OUT";; esac
}

test_api_injoignable_ko_message() {
  doc_projet "http://127.0.0.1:1"
  run_install doctor; assert_rc 1 || return 1
  assert_out "KO  API Grist injoignable" || return 1
}

test_mcp_manquant_ko_avec_commande() {
  doc_serveur || return 1; doc_projet; unfake_cmd mcp-server-grist; echo '{}' > .mcp.json
  run_install doctor; assert_rc 1 || return 1
  assert_out "pipx install mcp-server-grist==" || return 1
  assert_out "KO  entrée MCP" || return 1
}

test_doctor_sans_document_ignore_l_api() {
  doc_projet "http://127.0.0.1:1" "$DOC_KEY" ""
  run_install doctor; assert_rc 0 || return 1
  assert_out "API Grist ignorée" || return 1
}

test_document_inconnu_ko_404() {
  doc_serveur || return 1; doc_projet "" "$DOC_KEY" autre
  run_install doctor; assert_rc 1 || return 1
  assert_out "introuvable (HTTP 404)" || return 1
}

test_manifeste_incoherent_ko() {
  doc_serveur || return 1; doc_projet; rm .grist/lib.sh
  run_install doctor; assert_rc 1 || return 1
  assert_out "KO  manifeste" || return 1
}

test_doctor_projet_non_initialise_code_2() {
  run_install doctor; assert_rc 2
}

test_doctor_ne_modifie_rien() {
  doc_serveur || return 1; doc_projet
  local avant apres
  avant=$(find . -type f -exec cksum {} + | sort)
  run_install doctor
  apres=$(find . -type f -exec cksum {} + | sort)
  [ "$avant" = "$apres" ] || fail "fichiers modifiés par doctor"
}
