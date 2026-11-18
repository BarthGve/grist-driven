"""Sélection d'environnement de déploiement : preprod = branche next, production = branche main.

    .venv/bin/python scripts/grist_env.py auto|preprod|production [-- commande…]

Pose `GRIST_DOC_ID` pour la seule commande lancée (jamais dans `.env`) à partir de
`GRIST_DOC_ID_PREPROD` / `GRIST_DOC_ID_PRODUCTION`. Sans commande : vérifie et sort.
N'affiche jamais un identifiant ni une clé. Aucun accès réseau.
"""
import os
import subprocess
import sys
from pathlib import Path

from dotenv import dotenv_values

BRANCHE = {"preprod": "next", "production": "main"}
VAR = {"preprod": "GRIST_DOC_ID_PREPROD", "production": "GRIST_DOC_ID_PRODUCTION"}


class Refus(Exception):
    pass


def _git(racine, *args):
    r = subprocess.run(["git", "-C", str(racine), *args], capture_output=True, text=True)
    return r.stdout.strip() if r.returncode == 0 else ""


def verifier_version(racine, git=_git):
    """Même exigence que la porte du flux : VERSION bumpée, CHANGELOG qui la mentionne."""
    version = (Path(racine) / "VERSION").read_text().strip() if (Path(racine) / "VERSION").exists() else ""
    if not version:
        raise Refus("VERSION absent : production refusée")
    journal = Path(racine) / "CHANGELOG.md"
    lignes = [l for l in journal.read_text().splitlines() if version in l] if journal.exists() else []
    if not lignes or any("à publier" in l for l in lignes):
        raise Refus(f"CHANGELOG.md ne publie pas la version {version} : production refusée")
    # ponytail: bump contrôlé seulement si HEAD est une fusion (premier parent = main précédent) ;
    # un fast-forward n'est vérifié que par le CHANGELOG, la porte de push couvrant le reste.
    if git(racine, "rev-parse", "--verify", "-q", "HEAD^2") and git(racine, "show", "HEAD^1:VERSION") == version:
        raise Refus(f"VERSION inchangée depuis la production précédente ({version}) : production refusée")


def choisir(niveau, branche, env, racine, version=verifier_version):
    """Renvoie (niveau, identifiant) ou lève Refus. Le message ne contient jamais d'identifiant."""
    if niveau == "auto":
        niveau = next((n for n, b in BRANCHE.items() if b == branche), None)
        if niveau is None:
            raise Refus(f"branche « {branche} » sans environnement : seuls next (preprod) et main (production) se déploient ; la recette utilise GRIST_DOC_ID du .env du worktree")
    if niveau not in VAR:
        raise Refus(f"niveau inconnu « {niveau} » (auto, preprod, production)")
    if branche != BRANCHE[niveau]:
        raise Refus(f"{niveau} se déploie depuis {BRANCHE[niveau]}, pas depuis « {branche} »")
    doc = (env.get(VAR[niveau]) or "").strip()
    if not doc:
        raise Refus(f"{VAR[niveau]} absent ou vide dans .env")
    autres = {k: (env.get(k) or "").strip() for k in ("GRIST_DOC_ID", *VAR.values()) if k != VAR[niveau]}
    if niveau == "production":
        egal = [k for k, v in autres.items() if v == doc]
    else:
        egal = [k for k in ("GRIST_DOC_ID", VAR["production"]) if autres[k] == doc]
    if egal:
        raise Refus(f"{VAR[niveau]} égal à {', '.join(egal)} : un niveau doit avoir son propre document")
    if niveau == "production":
        version(racine)
    return niveau, doc


def main(argv=None, racine=None, environ=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    racine = Path(racine or Path(__file__).resolve().parent.parent)
    cmd = argv[argv.index("--") + 1:] if "--" in argv else []
    tete = argv[:argv.index("--")] if "--" in argv else argv
    if len(tete) != 1:
        print("usage : grist_env.py auto|preprod|production [-- commande…]", file=sys.stderr)
        return 2
    environ = dict(os.environ if environ is None else environ)
    env = {**dotenv_values(racine / ".env"), **{k: v for k, v in environ.items() if k.startswith("GRIST_DOC_ID")}}
    try:
        if any(a == "--doc" or a.startswith("--doc=") for a in cmd):
            raise Refus("--doc contourne la sélection d'environnement : retirer l'option")
        niveau, doc = choisir(tete[0], _git(racine, "rev-parse", "--abbrev-ref", "HEAD"), env, racine)
    except Refus as e:
        print(f"grist-env : {e}", file=sys.stderr)
        return 1
    print(f"grist-env : niveau {niveau}", file=sys.stderr)
    if not cmd:
        return 0
    return subprocess.run(cmd, cwd=racine, env={**environ, "GRIST_DOC_ID": doc}).returncode


if __name__ == "__main__":
    sys.exit(main())
