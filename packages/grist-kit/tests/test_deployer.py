import json

import pytest

from grist_kit import deployer as d
from grist_kit import pages
from grist_kit.client import GristErreur
from grist_kit.testing.faux_grist import ClientFactice, SessionFactice

PAGE = """<h1>Titre</h1>
<script src="https://exemple.test/grist.js"></script>
<script>
  console.log("é");
</script>
"""


@pytest.fixture
def env(tmp_path):
    client = ClientFactice()
    client.ajouter("_grist_Tables", {"tableId": "PROPOSITIONS_IA"})
    config = {"doc_id": "", "widgets": {}}
    pages.creer(client, config, "w", "PROPOSITIONS_IA", "T")
    client.records["_grist_Views_section"][1]["tableRef"] = 1   # le faux client ne le renseigne pas
    (tmp_path / "w.html").write_text(PAGE, encoding="utf-8")
    return client, config, tmp_path


def stocke(client):
    options = json.loads(client.records["_grist_Views_section"][1]["options"])
    return json.loads(options["customView"])["widgetOptions"]


def test_separe_html_et_js():
    html, js = d.separer_html_et_js(PAGE)
    assert html == "<h1>Titre</h1>\n"      # le script à `src` est écarté : le builder fournit déjà grist
    assert js == '  console.log("é");\n'


def test_widget_a_jour_renvoie_0(env):
    client, config, racine = env
    assert d.deployer(client, config, "w", racine, session=SessionFactice(client)) == 0
    avant = len(client.ecritures())
    assert d.deployer(client, config, "w", racine, session=SessionFactice(client)) == 0
    assert len(client.ecritures()) == avant


def test_ecart_en_check_renvoie_1_sans_ecrire(env):
    client, config, racine = env
    s, nb = SessionFactice(client), len(client.ecritures())
    assert d.deployer(client, config, "w", racine, check=True, session=s) == 1
    assert len(client.ecritures()) == nb and s.patchs == []


def test_depot_relit_et_verifie(env):
    client, config, racine = env
    s = SessionFactice(client)
    assert d.deployer(client, config, "w", racine, session=s) == 0
    html, js = d.separer_html_et_js(PAGE)
    assert len(s.patchs) == 1
    assert stocke(client)["_html"] == html and stocke(client)["_js"] == d.chargeur(js)
    assert d.deployer(client, config, "w", racine, check=True, session=s) == 0


def test_section_absente_message_clair(env):
    client, config, racine = env
    config["widgets"]["w"]["section_id"] = 99
    s = SessionFactice(client)
    with pytest.raises(ValueError, match="creer-page"):
        d.deployer(client, config, "w", racine, session=s)
    assert s.patchs == []


def test_section_d_un_autre_widget_refusee(env):
    client, config, racine = env
    client.ajouter("_grist_Tables", {"tableId": "AUTRE"})
    config["widgets"]["w"]["table_ref"] = 2      # même section, autre table : ce n'est pas celle du widget
    config["widgets"]["w"]["table_id"] = "AUTRE"
    nb, s = len(client.ecritures()), SessionFactice(client)
    with pytest.raises(ValueError, match="creer-page"):
        d.deployer(client, config, "w", racine, session=s)
    assert len(client.ecritures()) == nb and s.patchs == []


def test_section_non_personnalisee_refusee(env):
    client, config, racine = env
    client.records["_grist_Views_section"][1]["options"] = "{}"
    with pytest.raises(ValueError, match="creer-page"):
        d.verifier_section(client, config, "w")


def test_doc_different_de_widgets_json_refuse(env):
    client, config, racine = env
    config["doc_id"] = "AUTRE"
    nb, s = len(client.appels), SessionFactice(client)
    with pytest.raises(ValueError, match="AUTRE"):
        d.deployer(client, config, "w", racine, session=s)
    assert len(client.appels) == nb and s.patchs == []


def test_colonne_ajoutee_declaree_dans_la_section(env):
    client, config, racine = env
    client.ajouter("_grist_Tables_column", {"parentId": 1, "colId": "A"})
    client.ajouter("_grist_Tables_column", {"parentId": 1, "colId": "manualSort"})
    client.ajouter("_grist_Tables_column", {"parentId": 2, "colId": "AILLEURS"})
    assert d.synchroniser_champs(client, 1, 1) == ["A"]
    assert d.synchroniser_champs(client, 1, 1) == []     # idempotent
    champs = client.lignes("_grist_Views_section_field")
    assert [c["fields"]["colRef"] for c in champs] == [1]


def test_ecriture_non_conforme_leve_erreur(env):
    client, config, racine = env
    with pytest.raises(GristErreur, match="non conforme"):
        d.deployer(client, config, "w", racine, session=SessionFactice(client, deforme=True))


def test_refus_403_message_pare_feu(env):
    client, config, racine = env

    class Refus:
        status_code, text = 403, "Request unsuccessful. Incapsula incident"

        def json(self):
            return {}

        def raise_for_status(self):
            raise RuntimeError("trace brute")

    class SessionRefusee(SessionFactice):
        def patch(self, url, data=None, timeout=None):
            return Refus()

    with pytest.raises(GristErreur, match="pare-feu"):
        d.deployer(client, config, "w", racine, session=SessionRefusee(client))
