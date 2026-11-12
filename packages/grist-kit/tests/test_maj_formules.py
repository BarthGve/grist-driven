import json

import pytest

import schema_exemple
from grist_kit.apply_schema import appliquer as appliquer_schema
from grist_kit.client import GristErreur
from grist_kit.maj_formules import _options, appliquer
from grist_kit.testing.faux_grist import ClientFactice


def _document():
    client = ClientFactice()
    appliquer_schema(client, schema_exemple)
    return client


def _patchs(client):
    return [a for a in client.ecritures() if a[0] == "PATCH"]


def test_formule_modifiee_est_mise_a_jour():
    client = _document()
    client.champs["PROJETS.titre_cle"]["formula"] = "$titre"       # ancienne règle métier
    rapport = appliquer(client, schema_exemple)
    assert rapport["mises_a_jour"] == ["PROJETS.titre_cle"]
    assert client.champs["PROJETS.titre_cle"]["formula"] == '($titre or "").strip().lower()'
    assert client.champs["PROJETS.titre_cle"]["isFormula"] is True


def test_dry_run_liste_sans_ecrire():
    client = _document()
    client.champs["PROJETS.titre_cle"]["formula"] = "$titre"
    avant = len(client.ecritures())
    rapport = appliquer(client, schema_exemple, dry_run=True)
    assert rapport["mises_a_jour"] == ["PROJETS.titre_cle"]
    assert len(client.ecritures()) == avant
    assert client.champs["PROJETS.titre_cle"]["formula"] == "$titre"


def test_table_manquante_refuse_d_ecrire():
    client = _document()
    client.champs["PROJETS.titre_cle"]["formula"] = "$titre"
    del client.colonnes["TACHES"]
    avant = len(client.ecritures())
    with pytest.raises(GristErreur, match="TACHES"):
        appliquer(client, schema_exemple)
    assert len(client.ecritures()) == avant
    assert client.champs["PROJETS.titre_cle"]["formula"] == "$titre"


def test_colonne_manquante_refuse_d_ecrire():
    client = _document()
    client.colonnes["PROJETS"].remove("titre_cle")
    with pytest.raises(GristErreur, match="PROJETS.titre_cle"):
        appliquer(client, schema_exemple)
    assert not _patchs(client)


def test_colonne_de_donnees_non_formule_est_dite_divergente():
    client = _document()
    client.champs["PROJETS.titre_cle"].update(isFormula=False, formula="")
    rapport = appliquer(client, schema_exemple)
    assert [d.split(" :")[0] for d in rapport["divergentes"]] == ["PROJETS.titre_cle"]
    assert rapport["mises_a_jour"] == []
    assert not _patchs(client)
    assert client.champs["PROJETS.titre_cle"]["isFormula"] is False


def test_choix_alignes_sur_le_schema():
    client = _document()
    client.champs["TACHES.priorite"]["widgetOptions"] = json.dumps(
        {"choices": ["haut", "perso"], "alignment": "left"})
    rapport = appliquer(client, schema_exemple)
    assert rapport["mises_a_jour"] == ["TACHES.priorite"]
    options = json.loads(client.champs["TACHES.priorite"]["widgetOptions"])
    assert options["choices"] == ["haut", "perso", "bas", "moyen"]    # ordre et ajouts manuels conservés
    assert options["alignment"] == "left"


def test_idempotent():
    client = _document()
    client.champs["PROJETS.titre_cle"]["formula"] = "$titre"
    client.champs["TACHES.priorite"]["widgetOptions"] = json.dumps({"choices": ["bas"]})
    appliquer(client, schema_exemple)
    avant = len(client.ecritures())
    rapport = appliquer(client, schema_exemple)
    assert rapport["mises_a_jour"] == []
    assert "PROJETS.titre_cle" in rapport["inchangees"]
    assert len(client.ecritures()) == avant


def test_widget_options_illisibles_ne_sont_pas_touchees():
    client = _document()
    client.champs["TACHES.priorite"]["widgetOptions"] = "{pas du json"
    rapport = appliquer(client, schema_exemple)
    assert rapport["illisibles"] == ["TACHES.priorite"]
    assert client.champs["TACHES.priorite"]["widgetOptions"] == "{pas du json"


def test_options_lecture():
    assert _options("") == {}
    assert _options(None) == {}
    assert _options('{"choices": ["a"]}') == {"choices": ["a"]}
    assert _options("{cassé") is None
