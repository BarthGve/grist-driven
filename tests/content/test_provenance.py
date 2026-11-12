"""Audit de provenance : tests sur des dépôts git temporaires, sans toucher à ai-driven-dev."""
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))
import provenance  # noqa: E402

TEXTE = "\n".join(f"Ligne numéro {i} : la commande /ks-plan produit un plan détaillé du ticket." for i in range(40))
AUTRE = "\n".join(f"Phrase {i * 7} sur un tout autre sujet : maillage Grist, ACL et widgets." for i in range(40))


def _ecrire(racine: Path, fichiers: dict[str, str]) -> None:
    for chemin, contenu in fichiers.items():
        cible = racine / chemin
        cible.parent.mkdir(parents=True, exist_ok=True)
        cible.write_text(contenu, encoding="utf-8")


def test_fichiers_identiques_rapport_1(tmp_path):
    _ecrire(tmp_path, {"a.md": TEXTE})
    res = provenance.auditer(tmp_path, {"amont/a.md": TEXTE})
    assert res[0][1] == 1.0 and res[0][3] == "reecrire"


def test_fichier_reecrit_sous_le_seuil_est_libre(tmp_path):
    _ecrire(tmp_path, {"a.md": AUTRE})
    res = provenance.auditer(tmp_path, {"amont/a.md": TEXTE})
    assert res[0][1] < 0.5 and res[0][3] == "libre"


def test_fichier_renomme_reste_detecte(tmp_path):
    _ecrire(tmp_path, {"commands/dm-plan.md": TEXTE.replace("ks-", "dm-")})
    res = provenance.auditer(tmp_path, {"commands/ks-autre.md": AUTRE, "commands/ks-plan.md": TEXTE})
    chemin, rapport, proche, verdict = res[0]
    assert (proche, verdict) == ("commands/ks-plan.md", "reecrire") and rapport > 0.99


def test_fichier_sans_equivalent_amont_est_libre(tmp_path):
    _ecrire(tmp_path, {"lib/dm-quota.sh": AUTRE})
    res = provenance.auditer(tmp_path, {})
    assert res == [("lib/dm-quota.sh", 0.0, "", "libre")]


def test_audit_liste_tous_les_fichiers_de_src(tmp_path):
    _ecrire(tmp_path, {"a.md": TEXTE, "x/b.md": AUTRE, "x/y/c.sh": "echo ok\n"})
    res = provenance.auditer(tmp_path, {"amont/a.md": TEXTE})
    assert sorted(r[0] for r in res) == ["a.md", "x/b.md", "x/y/c.sh"]


def _git(depot: Path, *args: str, auteur: str = "Bruno") -> None:
    env = {"GIT_AUTHOR_NAME": auteur, "GIT_COMMITTER_NAME": auteur,
           "GIT_AUTHOR_EMAIL": "a@example.org", "GIT_COMMITTER_EMAIL": "a@example.org",
           "PATH": "/usr/bin:/bin:/usr/local/bin:/opt/homebrew/bin", "HOME": str(depot)}
    subprocess.run(["git", "-C", str(depot), *args], check=True, capture_output=True, env=env)


def test_charger_amont_lit_le_dernier_commit_de_l_auteur_amont(tmp_path):
    _git(tmp_path, "init", "-q")
    _ecrire(tmp_path, {"old.md": "v1", "image.bin": ""})
    (tmp_path / "image.bin").write_bytes(b"\xff\xfe\x00")
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-qm", "amont", auteur="Mike Codeur")
    _ecrire(tmp_path, {"old.md": "v2", "neuf.md": "bruno"})
    _git(tmp_path, "add", "-A")
    _git(tmp_path, "commit", "-qm", "fork")
    amont = provenance.charger_amont(tmp_path)
    assert amont == {"old.md": "v1"}  # état du dernier commit amont, binaire ignoré
