"""Refus de la sélection d'environnement (faux environnement, git et réseau absents)."""
import pytest

from scripts import grist_env as g

ENV = {"GRIST_DOC_ID_PREPROD": "pre1", "GRIST_DOC_ID_PRODUCTION": "prod1", "GRIST_DOC_ID": "rec1"}
OK = lambda racine: None  # noqa: E731


def choisir(niveau, branche, env=ENV, version=OK):
    return g.choisir(niveau, branche, env, ".", version)


def test_auto_suit_la_branche():
    assert choisir("auto", "next") == ("preprod", "pre1")
    assert choisir("auto", "main") == ("production", "prod1")


@pytest.mark.parametrize("niveau,branche", [("preprod", "main"), ("preprod", "feature/s01"), ("production", "next"), ("auto", "feature/s01")])
def test_refus_hors_branche(niveau, branche):
    with pytest.raises(g.Refus):
        choisir(niveau, branche)


@pytest.mark.parametrize("cle", ["GRIST_DOC_ID_PREPROD", "GRIST_DOC_ID_PRODUCTION"])
@pytest.mark.parametrize("valeur", [None, "", "  "])
def test_refus_identifiant_absent(cle, valeur):
    env = {**ENV, cle: valeur}
    niveau, branche = ("preprod", "next") if cle.endswith("PREPROD") else ("production", "main")
    with pytest.raises(g.Refus, match="absent"):
        choisir(niveau, branche, env)


@pytest.mark.parametrize("autre", ["GRIST_DOC_ID_PREPROD", "GRIST_DOC_ID"])
def test_refus_production_egale_a_un_autre_niveau(autre):
    with pytest.raises(g.Refus, match="propre document") as e:
        choisir("production", "main", {**ENV, "GRIST_DOC_ID_PRODUCTION": ENV[autre]})
    assert ENV[autre] not in str(e.value)


def test_refus_preprod_egale_a_la_recette():
    with pytest.raises(g.Refus):
        choisir("preprod", "next", {**ENV, "GRIST_DOC_ID_PREPROD": "rec1"})


def test_version_refusee_bloque_la_production_seulement():
    def non(racine):
        raise g.Refus("version")
    with pytest.raises(g.Refus):
        choisir("production", "main", version=non)
    assert choisir("preprod", "next", version=non)[0] == "preprod"


def test_version_et_changelog(tmp_path):
    (tmp_path / "VERSION").write_text("1.0.0\n")
    (tmp_path / "CHANGELOG.md").write_text("## 1.0.0 - à publier\n")
    with pytest.raises(g.Refus, match="CHANGELOG"):
        g.verifier_version(tmp_path, git=lambda *a: "")
    (tmp_path / "CHANGELOG.md").write_text("## 1.0.0 - 2026-11-25\n")
    g.verifier_version(tmp_path, git=lambda *a: "")
    # fusion dont le premier parent portait déjà la même VERSION
    with pytest.raises(g.Refus, match="inchangée"):
        g.verifier_version(tmp_path, git=lambda racine, *a: "x" if a[0] == "rev-parse" else "1.0.0")


def test_main_refuse_sans_rien_afficher(tmp_path, capsys, monkeypatch):
    monkeypatch.setattr(g, "_git", lambda *a: "feature/x")
    (tmp_path / ".env").write_text("GRIST_DOC_ID_PREPROD=secretpre\n")
    assert g.main(["preprod"], racine=tmp_path, environ={}) == 1
    sortie = capsys.readouterr()
    assert "secret" not in sortie.out + sortie.err


def test_main_pose_la_variable_pour_la_commande_seule(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(g, "_git", lambda *a: "next")
    (tmp_path / ".env").write_text("GRIST_DOC_ID_PREPROD=secretpre\nGRIST_DOC_ID=rec\n")
    vu = {}
    monkeypatch.setattr(g.subprocess, "run", lambda cmd, cwd, env: vu.update(env=env) or type("R", (), {"returncode": 0})())
    assert g.main(["preprod", "--", "echo"], racine=tmp_path, environ={}) == 0
    assert vu["env"]["GRIST_DOC_ID"] == "secretpre"
    assert "secret" not in "".join(capsys.readouterr())


def test_main_refuse_doc_en_ligne_de_commande(tmp_path, monkeypatch):
    monkeypatch.setattr(g, "_git", lambda *a: "next")
    (tmp_path / ".env").write_text("GRIST_DOC_ID_PREPROD=p\n")
    assert g.main(["preprod", "--", "x", "--doc", "autre"], racine=tmp_path, environ={}) == 1
