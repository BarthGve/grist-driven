import json

import schema_exemple
from grist_kit.apply_schema import appliquer
from grist_kit.testing.faux_grist import ClientFactice


def _ids(client, table):
    return client.colonnes[table]


def test_cree_tables_et_colonnes_manquantes():
    c = ClientFactice()
    rapport = appliquer(c, schema_exemple)
    assert rapport["tables_creees"] == ["CATEGORIES", "PROJETS", "TACHES"]
    assert set(_ids(c, "TACHES")) == {"intitule", "projet", "priorite", "creee_le"}
    assert json.loads(c.payloads["TACHES.priorite"]["fields"]["widgetOptions"]) == {"choices": ["bas", "moyen", "haut"]}
    # formule déclenchée : donnée calculée une fois, jamais réécrite
    f = c.payloads["TACHES.creee_le"]["fields"]
    assert f["isFormula"] is False and f["recalcWhen"] == 0
    assert c.payloads["PROJETS.titre_cle"]["fields"]["isFormula"] is True


def test_deuxieme_passage_ne_change_rien():
    c = ClientFactice()
    appliquer(c, schema_exemple)
    avant = len(c.ecritures())
    rapport = appliquer(c, schema_exemple)
    assert rapport["tables_creees"] == [] and rapport["colonnes_ajoutees"] == []
    assert sorted(rapport["inchangees"]) == ["CATEGORIES", "PROJETS", "TACHES"]
    assert len(c.ecritures()) == avant


def test_dry_run_n_ecrit_rien():
    c = ClientFactice()
    rapport = appliquer(c, schema_exemple, dry_run=True)
    assert c.ecritures() == []
    assert rapport["tables_creees"] == ["CATEGORIES", "PROJETS", "TACHES"]
    assert "CATEGORIES.parent" in rapport["colonnes_ajoutees"]


def test_dry_run_sur_document_a_jour_ne_signale_rien():
    c = ClientFactice()
    appliquer(c, schema_exemple)
    rapport = appliquer(c, schema_exemple, dry_run=True)
    assert rapport["tables_creees"] == [] and rapport["colonnes_ajoutees"] == []


def test_colonne_auto_referente_creee_en_deuxieme_passe():
    c = ClientFactice()
    rapport = appliquer(c, schema_exemple)
    creation = next(a for a in c.appels if a[:2] == ("POST", "/tables") and a[2]["tables"][0]["id"] == "CATEGORIES")
    assert [col["id"] for col in creation[2]["tables"][0]["columns"]] == ["nom"]   # sans `parent`
    assert "CATEGORIES.parent" in rapport["colonnes_ajoutees"]
    assert c.payloads["CATEGORIES.parent"]["fields"]["type"] == "Ref:CATEGORIES"
    ajout = [a for a in c.ecritures() if a[1] == "/tables/CATEGORIES/columns"]
    assert len(ajout) == 1 and c.appels.index(ajout[0]) > c.appels.index(creation)


def test_ne_supprime_jamais():
    c = ClientFactice()
    c.colonnes["PROJETS"] = ["titre", "colonne_en_trop"]
    appliquer(c, schema_exemple)
    assert "colonne_en_trop" in _ids(c, "PROJETS")
    assert all(a[0] in ("GET", "POST") for a in c.appels)


def test_colonne_de_donnees_ajoutee_a_table_existante_n_est_pas_formule():
    # Grist crée une colonne sans formule avec isFormula vrai ; un non-propriétaire verrait son écriture refusée.
    c = ClientFactice()
    c.colonnes["PROJETS"] = ["titre"]
    rapport = appliquer(c, schema_exemple)
    assert "PROJETS.categorie" in rapport["colonnes_ajoutees"]
    assert c.payloads["PROJETS.categorie"]["fields"]["isFormula"] is False
    assert c.payloads["PROJETS.titre_cle"]["fields"]["isFormula"] is True   # vraie formule : inchangée


def test_table_creee_formules_ajoutees_une_a_une():
    # Le pare-feu refuse parfois une table envoyée d'un bloc avec ses formules (403).
    c = ClientFactice()
    appliquer(c, schema_exemple)
    creation = next(a for a in c.appels if a[:2] == ("POST", "/tables") and a[2]["tables"][0]["id"] == "PROJETS")
    assert [col["id"] for col in creation[2]["tables"][0]["columns"]] == ["titre", "categorie"]
    assert any(a[1] == "/tables/PROJETS/columns" and a[2]["columns"][0]["id"] == "titre_cle" for a in c.ecritures())
