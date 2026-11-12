#!/usr/bin/env bash
# grist-version : version du projet (fichier VERSION, semver) et journal des changements.
#
#   grist-version.sh current              affiche la version
#   grist-version.sh bump major|minor|patch
#
# `bump` réécrit VERSION, aligne pyproject.toml et package.json quand ils existent et
# ouvre, dans CHANGELOG.md, une section « ## x.y.z - AAAA-MM-JJ » au-dessus des précédentes.
set -euo pipefail

die() { echo "grist-version : $*" >&2; exit 1; }

# Tout le travail sur les fichiers se fait en Python : le calcul semver et les trois
# réécritures sont validés avant d'écrire quoi que ce soit.
cmd_bump() {
  [ -f VERSION ] || die "VERSION introuvable (lancer /grist-init)"
  python3 - "$1" <<'PY'
import datetime, json, pathlib, re, sys

partie = sys.argv[1]
v = pathlib.Path("VERSION")
actuelle = v.read_text().strip()
m = re.fullmatch(r"(\d+)\.(\d+)\.(\d+)", actuelle)
if not m:
    sys.exit(f"grist-version : VERSION invalide « {actuelle} » (attendu x.y.z)")
maj, mino, pat = map(int, m.groups())
suivante = {"major": (maj + 1, 0, 0), "minor": (maj, mino + 1, 0), "patch": (maj, mino, pat + 1)}[partie]
nouvelle = ".".join(map(str, suivante))

v.write_text(nouvelle + "\n")

pyproject = pathlib.Path("pyproject.toml")
if pyproject.exists():
    texte = pyproject.read_text()
    texte = re.sub(r'(?ms)(^\[project\].*?^version\s*=\s*")[^"]+(")', rf"\g<1>{nouvelle}\g<2>", texte, count=1)
    pyproject.write_text(texte)

paquet = pathlib.Path("package.json")
if paquet.exists():
    donnees = json.loads(paquet.read_text())
    if "version" in donnees:
        donnees["version"] = nouvelle
        paquet.write_text(json.dumps(donnees, indent=2, ensure_ascii=False) + "\n")

journal = pathlib.Path("CHANGELOG.md")
if journal.exists():
    titre = f"## {nouvelle} - {datetime.date.today().isoformat()}"
    texte = journal.read_text()
    if titre not in texte:
        premiere = re.search(r"^## ", texte, re.M)
        if premiere:
            texte = texte[: premiere.start()] + titre + "\n\n" + texte[premiere.start():]
        else:
            texte = texte.rstrip("\n") + "\n\n" + titre + "\n\n"
        journal.write_text(texte)
print(nouvelle)
PY
}

case "${1:-}" in
  current)
    [ -f VERSION ] || die "VERSION introuvable"
    tr -d '[:space:]' <VERSION
    echo
    ;;
  bump)
    case "${2:-}" in
      major | minor | patch) cmd_bump "$2" ;;
      *) die "usage : bump major|minor|patch" ;;
    esac
    ;;
  *) die "usage : grist-version.sh current | bump major|minor|patch" ;;
esac
