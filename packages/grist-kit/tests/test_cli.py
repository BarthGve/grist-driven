"""CLI `python -m grist_kit` : projet temporaire, client factice injecté, aucun réseau."""

import json
import shutil
import sys
from pathlib import Path

import pytest

from grist_kit import __main__ as cli
from grist_kit.projet import charger_projet
from grist_kit.testing.faux_grist import ClientFactice

TESTS = Path(__file__).parent
CORE = "const a = 1;"
PAGE = "<h1>T</h1>\n<script>\n/* === CORE BEGIN === */\nvieux\n/* === CORE END === */\n</script>\n"


def _projet(tmp_path, design_system="dsfr", amorcer=None):
    cfg = {"version": "0.1.0", "app": "demo", "package": "appdemo", "design_system": design_system,
           "widgets_dir": "widgets" if design_system == "dsfr" else "widgets_ui", "core": "widgets/core.js"}
    (tmp_path / ".grist-driven.json").write_text(json.dumps(cfg), encoding="utf-8")
    pkg = tmp_path / "appdemo"
    pkg.mkdir()
    (pkg / "__init__.py").write_text("", encoding="utf-8")
    shutil.copy(TESTS / "schema_exemple.py", pkg / "schema.py")
    shutil.copy(TESTS / "regles_exemple.py", pkg / "acl_rules.py")
    if amorcer:
        (pkg / "amorcer.py").write_text(amorcer, encoding="utf-8")
    (tmp_path / "widgets").mkdir()
    (tmp_path / "widgets" / "core.js").write_text(CORE, encoding="utf-8")
    (tmp_path / "widgets" / "w.html").write_text(PAGE, encoding="utf-8")
    return tmp_path


@pytest.fixture(autouse=True)
def _isole(monkeypatch):
    monkeypatch.delenv("GRIST_DOC_ID", raising=False)
    monkeypatch.delenv("GRIST_API_KEY", raising=False)
    avant = list(sys.path)
    yield
    sys.path[:] = avant
    for nom in [n for n in sys.modules if n == "appdemo" or n.startswith("appdemo.")]:
        del sys.modules[nom]


def _lancer(racine, *argv, client=None):
    return cli.main(list(argv), racine=racine, client=client)


def test_charger_projet_lit_la_config(tmp_path):
    p = charger_projet(_projet(tmp_path))
    assert (p.app, p.package, p.design_system) == ("demo", "appdemo", "dsfr")
    assert p.schema.TABLES and p.regles.RULES


def test_apply_schema_sans_doc_dit_quoi_faire(tmp_path, capsys):
    assert _lancer(_projet(tmp_path), "apply-schema") == 1
    assert "GRIST_DOC_ID" in capsys.readouterr().err


def test_design_system_inconnu_refuse(tmp_path, capsys):
    racine = _projet(tmp_path)
    f = racine / ".grist-driven.json"
    f.write_text(f.read_text().replace('"dsfr"', '"bootstrap"'), encoding="utf-8")
    assert _lancer(racine, "inliner") == 1
    err = capsys.readouterr().err
    assert "bootstrap" in err and "dsfr" in err and "ui-kit" in err


def test_sans_config_dit_quoi_faire(tmp_path, capsys):
    assert _lancer(tmp_path, "inliner") == 1
    assert ".grist-driven.json" in capsys.readouterr().err


def test_apply_schema_ecrit_puis_dry_run_ecrit_rien(tmp_path):
    racine = _projet(tmp_path)
    c = ClientFactice()
    assert _lancer(racine, "apply-schema", "--dry-run", client=c) == 0
    assert c.ecritures() == []
    assert _lancer(racine, "apply-schema", client=c) == 0
    assert set(c.colonnes) == {"CATEGORIES", "PROJETS", "TACHES"}


def test_dry_run_n_ecrit_rien_pour_chaque_sous_commande(tmp_path):
    racine = _projet(tmp_path, amorcer=(
        "def executer(client, dry_run):\n    assert dry_run is True\n    print('amorçage simulé')\n"))
    c = ClientFactice()
    assert _lancer(racine, "apply-schema", client=c) == 0
    c.appels.clear()
    c.ajouter("_grist_Tables", {"tableId": "PROJETS"})
    (racine / "widgets" / "w.html").write_text(PAGE, encoding="utf-8")
    for argv in (["apply-schema"], ["maj-formules"], ["apply-acl"], ["apply-acl", "--prune"], ["amorcer"],
                 ["creer-page", "w", "PROJETS", "--titre", "T"], ["inliner"]):
        assert _lancer(racine, *argv, "--dry-run", client=c) == 0, argv
        assert c.ecritures() == [], argv
    assert "vieux" in (racine / "widgets" / "w.html").read_text()
    assert not (racine / "widgets.json").exists()


def test_creer_page_ecrit_widgets_json(tmp_path):
    racine = _projet(tmp_path)
    c = ClientFactice()
    c.ajouter("_grist_Tables", {"tableId": "PROJETS"})
    assert _lancer(racine, "creer-page", "w", "PROJETS", "--titre", "Projets", "--acces", "read table", client=c) == 0
    cfg = json.loads((racine / "widgets.json").read_text())
    assert cfg["doc_id"] == "DOC" and cfg["widgets"]["w"]["acces"] == "read table"


def test_inliner_recopie_et_check(tmp_path):
    racine = _projet(tmp_path)
    assert _lancer(racine, "inliner", "--check") == 1
    assert _lancer(racine, "inliner") == 0
    assert CORE in (racine / "widgets" / "w.html").read_text()
    assert _lancer(racine, "inliner", "--check") == 0


def test_amorcer_absent_n_echoue_pas(tmp_path, capsys):
    assert _lancer(_projet(tmp_path), "amorcer", client=ClientFactice()) == 0
    assert "rien à faire" in capsys.readouterr().out


def test_amorcer_appelle_executer(tmp_path):
    racine = _projet(tmp_path, amorcer="def executer(client, dry_run):\n    client.add_record('X', {'a': 1})\n")
    c = ClientFactice()
    assert _lancer(racine, "amorcer", client=c) == 0
    assert c.ecritures()


def test_versions_synchronise_le_changelog(tmp_path):
    racine = _projet(tmp_path)
    journal = [{"version": "0.1.0", "date": "2026-11-12", "notes": [{"texte": "Début", "widgets": ["w"]}]}]
    (racine / "widgets" / "core.js").write_text(
        f"{CORE}\n/* VERSIONS BEGIN */{json.dumps(journal)}/* VERSIONS END */", encoding="utf-8")
    c = ClientFactice()
    assert _lancer(racine, "versions", "--dry-run", client=c) == 0
    assert c.ecritures() == [] and not (racine / "CHANGELOG.md").exists()
    assert _lancer(racine, "versions", client=c) == 0
    assert c.lignes("CHANGELOG")[0]["fields"]["version"] == "0.1.0"
    assert "0.1.0" in (racine / "CHANGELOG.md").read_text()


@pytest.mark.parametrize("profil, attendu", [("dsfr", "deployer"), ("ui-kit", "uikit")])
def test_deployer_choisit_le_profil_selon_design_system(tmp_path, monkeypatch, profil, attendu):
    racine = _projet(tmp_path, design_system=profil)
    (racine / "widgets.json").write_text(json.dumps({"doc_id": "DOC", "widgets": {"w": {}}}), encoding="utf-8")
    appels = []
    monkeypatch.setattr(cli.deployer, "deployer", lambda *a, **k: appels.append(("deployer", a, k)) or 0)
    monkeypatch.setattr(cli.build_uikit, "deployer_uikit", lambda *a, **k: appels.append(("uikit", a, k)) or 0)
    monkeypatch.setattr(cli.build_uikit, "construire", lambda *a, **k: appels.append(("construire", a, k)) or {})
    assert _lancer(racine, "deployer", "w", "--check", client=ClientFactice()) == 0
    assert [a[0] for a in appels if a[0] != "construire"] == [attendu]
    assert not any(a[0] == "construire" for a in appels)     # --check ne construit pas
    appels.clear()
    assert _lancer(racine, "deployer", "w", client=ClientFactice()) == 0
    assert ("construire" in [a[0] for a in appels]) == (profil == "ui-kit")


def test_erreur_du_kit_est_un_message_pas_une_trace(tmp_path, capsys):
    racine = _projet(tmp_path)
    assert _lancer(racine, "deployer", "inconnu", client=ClientFactice()) == 1
    assert "Traceback" not in capsys.readouterr().err
