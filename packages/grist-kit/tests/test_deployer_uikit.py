import base64
import gzip
import json
import random
import re
import stat

import pytest

from grist_kit import build_uikit, deployer as d, pages
from grist_kit.client import GristErreur
from grist_kit.testing.faux_grist import ClientFactice, SessionFactice

PAGE = '<html><body><div id="root"></div><script>console.log("é");</script></body></html>\n'


def extraire(chargeur):
    """Charge base64 d'un chargeur gzip, décompressée en Python."""
    return gzip.decompress(base64.b64decode(re.search(r'atob\("([^"]+)"\)', chargeur).group(1))).decode("utf-8")


@pytest.fixture
def env(tmp_path):
    client = ClientFactice()
    client.ajouter("_grist_Tables", {"tableId": "ELEMENTS"})
    config = {"doc_id": "", "widgets": {}}
    pages.creer(client, config, "liste", "ELEMENTS", "T")
    client.records["_grist_Views_section"][1]["tableRef"] = 1
    config["widgets"]["liste"]["entree"] = "liste"
    ui = tmp_path / "widgets_ui"
    (ui / "dist").mkdir(parents=True)
    (ui / "dist" / "liste.html").write_text(PAGE, encoding="utf-8")
    return client, config, ui


def binaire(dossier, nom, corps):
    f = dossier / nom
    f.write_text("#!/bin/sh\n" + corps, encoding="utf-8")
    f.chmod(f.stat().st_mode | stat.S_IEXEC)


def test_chargeur_gzip_aller_retour():
    js = 'var a = "é — 𝄞";\nconsole.log(a);\n'
    assert extraire(build_uikit.chargeur_gzip(js)) == js


def test_chargeur_gzip_deterministe():
    js = "x" * 500
    assert build_uikit.chargeur_gzip(js) == build_uikit.chargeur_gzip(js)
    assert "DecompressionStream" in build_uikit.chargeur_gzip(js)


def test_bundle_trop_gros_refuse_avec_message(env, monkeypatch):
    client, config, ui = env
    alea = random.Random(0)
    gros = "".join(chr(alea.randrange(33, 126)) for _ in range(50_000))
    (ui / "dist" / "liste.html").write_text(f"<script>{gros}</script>", encoding="utf-8")
    monkeypatch.setattr(build_uikit, "LIMITE_API_OCTETS", 20_000)
    s, nb = SessionFactice(client), len(client.ecritures())
    with pytest.raises(GristErreur) as e:
        build_uikit.deployer_uikit(client, config, "liste", ui, session=s)
    assert "413" in str(e.value) and "réduire" in str(e.value).lower()
    assert s.patchs == [] and len(client.ecritures()) == nb


def test_limite_par_defaut():
    assert build_uikit.LIMITE_API_OCTETS == 1_000_000


def test_node_absent_message_clair(tmp_path, monkeypatch):
    vide = tmp_path / "vide"
    vide.mkdir()
    monkeypatch.setenv("PATH", str(vide))
    with pytest.raises(GristErreur, match="Node"):
        build_uikit.construire(tmp_path)


def test_node_trop_ancien_message_clair(tmp_path, monkeypatch):
    bin_ = tmp_path / "bin"
    bin_.mkdir()
    binaire(bin_, "node", 'echo v18.19.0\n')
    binaire(bin_, "npm", "exit 0\n")
    monkeypatch.setenv("PATH", str(bin_))
    with pytest.raises(GristErreur, match="20"):
        build_uikit.construire(tmp_path)


def test_construire_lance_npm_ci_puis_build(tmp_path, monkeypatch):
    bin_ = tmp_path / "bin"
    bin_.mkdir()
    journal = tmp_path / "journal"
    binaire(bin_, "npm", f'echo "npm $@" >> {journal}\n')
    binaire(bin_, "node", f'if [ "$1" = "--version" ]; then echo v20.11.0; exit 0; fi\n'
                          f'echo "node $@" >> {journal}\n'
                          'echo "liste : 42 Ko"\n')
    monkeypatch.setenv("PATH", str(bin_))
    assert build_uikit.construire(tmp_path, ["liste"]) == {"liste": 42}
    assert journal.read_text().splitlines() == ["npm ci", "node build.mjs liste"]


def test_depot_gzip_relu_et_check_compare_au_dist(env):
    client, config, ui = env
    s = SessionFactice(client)
    assert build_uikit.deployer_uikit(client, config, "liste", ui, check=True, session=s) == 1
    assert s.patchs == []
    assert build_uikit.deployer_uikit(client, config, "liste", ui, session=s) == 0
    options = json.loads(client.records["_grist_Views_section"][1]["options"])
    stocke = json.loads(options["customView"])["widgetOptions"]
    _, js = d.separer_html_et_js(PAGE)
    assert extraire(stocke["_js"]) == js
    assert build_uikit.deployer_uikit(client, config, "liste", ui, check=True, session=s) == 0
    (ui / "dist" / "liste.html").write_text(PAGE.replace("é", "è"), encoding="utf-8")
    nb = len(s.patchs)
    assert build_uikit.deployer_uikit(client, config, "liste", ui, check=True, session=s) == 1
    assert len(s.patchs) == nb


def test_dist_absent_dit_de_construire(env):
    client, config, ui = env
    (ui / "dist" / "liste.html").unlink()
    with pytest.raises(GristErreur, match="npm ci"):
        build_uikit.deployer_uikit(client, config, "liste", ui, session=SessionFactice(client))
