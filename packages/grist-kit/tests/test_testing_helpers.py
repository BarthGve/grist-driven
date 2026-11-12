import datetime as dt
import subprocess
import sys

import pytest

import regles_helpers
import schema_helpers
from grist_kit.testing.acl import permis
from grist_kit.testing.formules import Base

MAINTENANT = dt.datetime(2030, 3, 4, 12, 0, tzinfo=dt.timezone.utc)
PERSONNES = [{"email_cle": "admin@exemple.test", "admin": True},
             {"email_cle": "auteur@exemple.test"},
             {"email_cle": "autre@exemple.test"}]


def monde(**en_plus):
    return Base(schema_helpers, maintenant=MAINTENANT, PERSONNES=PERSONNES,
                DOCS=[{"titre": "Note", "auteur": 2}], **en_plus)


def droit(email, d, **kw):
    base = monde()
    return permis(base, regles_helpers, email, "DOCS", d, rec=base.ligne("DOCS", 1), **kw)


def test_premiere_regle_qui_tranche_gagne():
    assert droit("admin@exemple.test", "D")                 # règle 1 (listée après la règle 3)
    assert droit("auteur@exemple.test", "U")                # règle 2
    assert not droit("auteur@exemple.test", "D")            # rien ne l'accorde
    assert droit("autre@exemple.test", "R")                 # règle 3 : lecture seule
    assert not droit("autre@exemple.test", "U")


def test_ressource_precise_avant_generale():
    assert droit("autre@exemple.test", "R", colonne="titre")
    assert not droit("autre@exemple.test", "R", colonne="secret")   # la colonne cite sa propre ressource
    assert droit("admin@exemple.test", "R", colonne="secret")


def test_droit_refuse_par_defaut():
    base = monde()
    assert not permis(base, regles_helpers, "admin@exemple.test", "PERSONNES", "R")   # aucune règle
    assert not permis(base, regles_helpers, "inconnu@exemple.test", "DOCS", "C")


def test_creation_evalue_newrec():
    base, nouvelle = monde().avec("DOCS", titre="Neuf", auteur=2)
    assert nouvelle.id == 2 and nouvelle.auteur.email_cle == "auteur@exemple.test"
    assert permis(base, regles_helpers, "auteur@exemple.test", "DOCS", "U", rec=nouvelle, apres=nouvelle)


def test_formule_lookuprecords():
    base = Base(schema_helpers, UNITES=[{"code": " a "}, {"code": "b", "parent": 1}, {"code": "c", "parent": 1}])
    assert base.ligne("UNITES", 1).nb_sous == 2
    assert base.ligne("UNITES", 1).code_cle == "A"
    assert base["UNITES"].lookupOne(code="c").id == 3
    assert not base["UNITES"].lookupOne(code="zzz")       # ligne « fausse »
    assert base.ligne("UNITES", 2).parent.code == " a "   # suivi de référence


def test_formule_now_fige_par_maintenant():
    assert monde().ligne("DOCS", 1).annee_courante == 2030
    autre = Base(schema_helpers, maintenant=dt.datetime(2041, 1, 1, tzinfo=dt.timezone.utc), DOCS=[{}])
    assert autre.ligne("DOCS", 1).annee_courante == 2041


def test_colonne_formule_par_defaut_selon_type():
    vide = monde().ligne("DOCS", 0)
    assert (vide.titre, vide.note, vide.etat, vide.echeance, vide.horodatage) == ("", 0.0, "", None, None)
    assert not vide.auteur and vide.auteur.id == 0
    # colonne déclenchée : valeur stockée, jamais recalculée
    assert monde().ligne("DOCS", 1).figee == ""
    monde().toutes_les_formules()                          # test de fumée


def test_datetime_numerique_en_fuseau_declare():
    base = Base(schema_helpers, DOCS=[{"horodatage": 0}])
    assert base.ligne("DOCS", 1).horodatage.hour == 1      # 1970-01-01 00:00 UTC = 01:00 à Paris


def test_helpers_n_importent_aucun_module_de_projet(tmp_path):
    code = ("import sys, grist_kit.testing, grist_kit.testing.acl, grist_kit.testing.formules\n"
            "assert 'sp2c' not in sys.modules and 'schema' not in sys.modules, sorted(sys.modules)\n")
    r = subprocess.run([sys.executable, "-c", code], cwd=tmp_path, capture_output=True, text=True,
                       env={"PATH": "", "PYTHONPATH": ""})
    assert r.returncode == 0, r.stderr
