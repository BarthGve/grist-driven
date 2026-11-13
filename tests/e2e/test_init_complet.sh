#!/usr/bin/env bash
# Parcours de bout en bout : « install.sh init » dans un répertoire vierge, pour chaque design system,
# puis doctor et pytest du projet généré. Aucun réseau (kit installé depuis le dépôt), aucun vrai Grist,
# HOME factice (ni ~/.claude.json ni installation globale touchés). Usage : bash tests/e2e/test_init_complet.sh
set -u
REPO=$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)
CLE=cle-factice-e2e
FAIL=0
ko() { echo "    ÉCHEC : $*"; FAIL=1; }

parcours() { # <design system>
  local ds=$1 tmp rc out f
  tmp=$(mktemp -d "${TMPDIR:-/tmp}/gd-e2e.XXXXXX")
  export HOME=$tmp GRIST_KIT_SPEC="$REPO/packages/grist-kit" GRIST_DRIVEN_TTY="$tmp/absent" \
         GRIST_DRIVEN_VENV_ARGS=--system-site-packages \
         GRIST_DRIVEN_PIP_ARGS="--no-index --no-deps --no-build-isolation"
  unset GRIST_API_KEY
  mkdir "$tmp/demo"; cd "$tmp/demo" || return 1

  out=$(bash "$REPO/install.sh" init --yes --name demo --design-system "$ds" --mcp none \
        --no-git-flow --no-hooks --ci </dev/null 2>&1); rc=$?
  if [ "$rc" -ne 0 ]; then ko "$ds : init code $rc : $out"; cd "$REPO"; rm -rf "$tmp"; return; fi

  for f in .claude/commands/grist-prd.md .grist-driven.json .env.example .env .github/workflows/ci.yml; do
    [ -f "$f" ] || ko "$ds : fichier absent : $f"
  done
  grep -q "\"design_system\": *\"$ds\"" .grist-driven.json || ko "$ds : design system absent de .grist-driven.json"
  grep -qxF '.env' .gitignore || ko "$ds : .env non ignoré"
  [ -z "$(sed -n 's/^GRIST_API_KEY=//p' .env)" ] || ko "$ds : .env contient déjà une clé"

  # doctor avant de remplir .env : KO attendu (code 1)
  out=$(bash "$REPO/install.sh" doctor 2>&1); rc=$?
  [ "$rc" -eq 1 ] || ko "$ds : doctor sur .env vide : code $rc au lieu de 1"

  # .env rempli de valeurs factices, sans document (donc aucun appel réseau)
  printf 'GRIST_API_KEY=%s\nGRIST_API_HOST=http://127.0.0.1:9\nGRIST_DOC_ID=\n' "$CLE" > .env
  out=$(bash "$REPO/install.sh" doctor 2>&1); rc=$?
  [ "$rc" -eq 0 ] || ko "$ds : doctor code $rc : $out"
  case $out in *"$CLE"*) ko "$ds : la clé apparaît dans la sortie de doctor";; esac

  out=$(.venv/bin/python -m pytest -q 2>&1) || ko "$ds : pytest du projet généré : $out"
  cd "$REPO" || exit 1
  rm -rf "$tmp"
}

for ds in dsfr ui-kit; do
  echo "== e2e $ds"; parcours "$ds"
done
if [ "$FAIL" -eq 0 ]; then echo "e2e : OK"; else echo "e2e : ÉCHEC"; fi
exit "$FAIL"
