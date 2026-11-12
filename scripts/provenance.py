#!/usr/bin/env python3
"""Audit de provenance : quels fichiers de driven sont restés proches de killer-saas.

Usage : python scripts/provenance.py <dossier src de driven> <dépôt git de driven> [sortie.md]
Stdlib seulement. L'amont est le dernier commit de l'auteur « Mike Codeur ».
"""
import re
import subprocess
import sys
from difflib import SequenceMatcher
from pathlib import Path

AUTEUR_AMONT = "Mike Codeur"
SEUIL = 0.5
_PREFIXE = re.compile(r"\b(?:ks|dm|grist)-")


def normaliser(texte: str) -> str:
    """Préfixes ks-/dm-/grist- ramenés à un jeton commun, espaces réduits."""
    return " ".join(_PREFIXE.sub("PFX-", texte).split())


def similarite(a: str, b: str) -> float:
    # Comparaison par mots : le niveau caractère est lent et faussé par l'autojunk.
    return SequenceMatcher(None, normaliser(a).split(), normaliser(b).split(), autojunk=False).ratio()


def _lire(chemin: Path) -> str | None:
    try:
        return chemin.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return None  # binaire (images…) : sans objet


def auditer(driven: Path, amont: dict[str, str], seuil: float = SEUIL) -> list[tuple[str, float, str, str]]:
    """(chemin driven, meilleur rapport, chemin amont le plus proche, verdict) pour chaque fichier."""
    mots_amont = {c: normaliser(t).split() for c, t in amont.items()}
    resultats = []
    for f in sorted(p for p in driven.rglob("*") if p.is_file() and p.name != ".DS_Store"):
        texte = _lire(f)
        if texte is None:
            continue
        mots = normaliser(texte).split()
        meilleur, proche = 0.0, ""
        for chemin, autres in mots_amont.items():  # chaque fichier amont, pas seulement le même chemin
            m = SequenceMatcher(None, mots, autres, autojunk=False)
            if m.real_quick_ratio() <= meilleur or m.quick_ratio() <= meilleur:
                continue  # bornes hautes : ne peut pas battre le meilleur
            r = m.ratio()
            if r > meilleur:
                meilleur, proche = r, chemin
        verdict = "reecrire" if meilleur >= seuil else "libre"
        resultats.append((f.relative_to(driven).as_posix(), round(meilleur, 4), proche, verdict))
    return resultats


def _git(depot: Path, *args: str) -> bytes:
    return subprocess.run(["git", "-C", str(depot), *args], check=True, capture_output=True).stdout


def charger_amont(depot: Path) -> dict[str, str]:
    """Tous les fichiers texte du dernier commit de l'auteur amont (lecture seule, sans checkout)."""
    commit = _git(depot, "log", f"--author={AUTEUR_AMONT}", "-1", "--format=%H").decode().strip()
    if not commit:
        raise SystemExit(f"aucun commit de {AUTEUR_AMONT} dans {depot}")
    amont = {}
    for chemin in _git(depot, "ls-tree", "-r", "--name-only", "-z", commit).decode().split("\0"):
        if not chemin:
            continue
        try:
            amont[chemin] = _git(depot, "show", f"{commit}:{chemin}").decode("utf-8")
        except UnicodeDecodeError:
            pass
    return amont


def rapport(resultats: list[tuple[str, float, str, str]], seuil: float = SEUIL) -> str:
    n = {v: sum(1 for r in resultats if r[3] == v) for v in ("reecrire", "libre")}
    lignes = [
        "# Audit de provenance",
        "",
        "Généré par `scripts/provenance.py` : chaque fichier de driven est comparé à chaque fichier du dernier",
        f"commit de {AUTEUR_AMONT} (killer-saas), après normalisation des préfixes `ks-`/`dm-`/`grist-`.",
        f"Seuil : {seuil}. Le document ne cite que des chemins, jamais de contenu hérité.",
        "",
        "## Résumé",
        "",
        f"- `reecrire` : {n['reecrire']}",
        f"- `libre` : {n['libre']}",
        f"- total : {len(resultats)}",
        "",
        "## Fichiers",
        "",
        "| Fichier driven | Rapport | Plus proche équivalent amont | Verdict |",
        "|---|---|---|---|",
    ]
    for chemin, r, proche, verdict in sorted(resultats, key=lambda x: (x[3] != "reecrire", -x[1], x[0])):
        lignes.append(f"| `{chemin}` | {r:.2f} | {f'`{proche}`' if proche else '—'} | {verdict} |")
    return "\n".join(lignes) + "\n"


if __name__ == "__main__":
    src, depot = Path(sys.argv[1]), Path(sys.argv[2])
    sortie = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("docs/provenance.md")
    sortie.write_text(rapport(auditer(src, charger_amont(depot))), encoding="utf-8")
    print(f"écrit : {sortie}")
