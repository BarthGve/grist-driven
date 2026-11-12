import json

import pytest

from grist_kit import pages
from grist_kit.testing.faux_grist import ClientFactice


@pytest.fixture
def client():
    c = ClientFactice()
    c.ajouter("_grist_Tables", {"tableId": "PROPOSITIONS_IA"})
    return c


def config_vide():
    return {"doc_id": "", "widgets": {}}


def test_cree_page_et_section_puis_consigne(client):
    config = config_vide()
    entree = pages.creer(client, config, "propositions-ia", "PROPOSITIONS_IA", "Propositions")
    assert entree == {"fichier": "propositions-ia.html", "table_ref": 1, "table_id": "PROPOSITIONS_IA",
                      "section_id": 1, "view_ref": 1, "acces": "full"}
    assert config["widgets"]["propositions-ia"] == entree
    assert client.records["_grist_Views"][1]["name"] == "Propositions"
    options = json.loads(client.records["_grist_Views_section"][1]["options"])
    vue = json.loads(options["customView"])
    assert vue["access"] == "full" and vue["widgetId"] == pages.BUILDER["widgetId"]


def test_deuxieme_appel_ne_cree_rien(client):
    config = config_vide()
    premiere = pages.creer(client, config, "w", "PROPOSITIONS_IA", "T")
    nb = len(client.ecritures())
    assert pages.creer(client, config, "w", "PROPOSITIONS_IA", "T") == premiere
    assert len(client.ecritures()) == nb


def test_table_inconnue_message_clair(client):
    with pytest.raises(ValueError, match="INCONNUE"):
        pages.creer(client, config_vide(), "w", "INCONNUE", "T")
    assert client.ecritures() == []


def test_acces_invalide_refuse(client):
    with pytest.raises(ValueError, match="accès"):
        pages.creer(client, config_vide(), "w", "PROPOSITIONS_IA", "T", acces="none")
    assert client.ecritures() == []


def test_doc_id_consigne_a_la_premiere_creation(client):
    config = config_vide()
    pages.creer(client, config, "w", "PROPOSITIONS_IA", "T")
    assert config["doc_id"] == client.doc_id


def test_creer_sur_un_autre_doc_que_celui_de_widgets_json_refuse(client):
    config = {"doc_id": "AUTRE", "widgets": {}}
    with pytest.raises(ValueError, match="AUTRE"):
        pages.creer(client, config, "w", "PROPOSITIONS_IA", "T")
    assert client.ecritures() == []
    assert config["widgets"] == {}


def test_config_aller_retour(tmp_path):
    chemin = tmp_path / "widgets.json"
    assert pages.charger_config(chemin) == config_vide()
    pages.ecrire_config(chemin, {"doc_id": "D", "widgets": {"é": {}}})
    assert pages.charger_config(chemin) == {"doc_id": "D", "widgets": {"é": {}}}
    assert chemin.read_text(encoding="utf-8").endswith("\n")
