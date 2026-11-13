#!/usr/bin/env bash
# Lance tous les tests de l'installeur : bash tests/installer/run.sh
# Chaque test tourne dans un répertoire temporaire, avec des binaires factices
# en tête de PATH (seul PATH factice : aucun accès réseau, aucun vrai git/gh).
set -u
HERE=$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)
REPO=$(cd "$HERE/../.." && pwd)
INSTALL="$REPO/install.sh"
export HERE REPO INSTALL

# --- aides communes -------------------------------------------------------
# Crée un PATH factice : outils système liés, git/gh/node/python3 factices.
fake_env() {
  FAKE_ROOT=$(mktemp -d "${TMPDIR:-/tmp}/gd-test.XXXXXX")
  FAKE_BIN="$FAKE_ROOT/bin"; PROJECT="$FAKE_ROOT/projet"
  mkdir -p "$FAKE_BIN" "$PROJECT"
  local t p
  for t in bash env cat mkdir dirname basename sed tr grep rm ls head cut awk sort uname date mv cp chmod printf cmp find rmdir curl sleep cksum; do
    p=$(command -v "$t" 2>/dev/null) && [ -x "$p" ] && ln -sf "$p" "$FAKE_BIN/$t"
  done
  fake_cmd git 'exit 0'
  fake_cmd gh 'exit 0'
  fake_cmd node 'echo "v20.11.0"'
  fake_cmd python3 'echo "Python ${FAKE_PY_VERSION:-3.12.1}"'
  PATH="$FAKE_BIN"; export PATH
  # Pas de terminal par défaut ; un test interactif fournit un fichier de réponses.
  GRIST_DRIVEN_TTY="$FAKE_ROOT/absent"; export GRIST_DRIVEN_TTY
  unset GRIST_API_KEY
  cd "$PROJECT" || exit 1
}
fake_cmd() { printf '#!/bin/bash\n%s\n' "$2" > "$FAKE_BIN/$1"; chmod +x "$FAKE_BIN/$1"; }
unfake_cmd() { rm -f "$FAKE_BIN/$1"; }

# Lance l'installeur ; stdout+stderr dans $OUT, code dans $RC.
run_install() { OUT=$("$BASH_BIN" "$INSTALL" "$@" </dev/null 2>&1); RC=$?; }
BASH_BIN=$(command -v bash)

fail() { echo "    ÉCHEC : $*"; return 1; }
assert_rc() { [ "$RC" -eq "$1" ] || fail "code $RC attendu $1 ; sortie : $OUT"; }
assert_out() { case "$OUT" in *"$1"*) ;; *) fail "sortie sans « $1 » : $OUT";; esac; }
assert_file() { [ -f "$1" ] || fail "fichier absent : $1"; }

# --- exécution ------------------------------------------------------------
for f in "$HERE"/test_*.sh; do . "$f"; done
PASS=0; FAILN=0
for fn in $(declare -F | awk '{print $3}' | grep '^test_'); do
  if ( fake_env; "$fn" ) ; then PASS=$((PASS+1)); echo "ok   $fn"
  else FAILN=$((FAILN+1)); echo "FAIL $fn"; fi
done
rm -rf "${TMPDIR:-/tmp}"/gd-test.* 2>/dev/null
echo "$PASS réussi(s), $FAILN échec(s)"
[ "$FAILN" -eq 0 ]
