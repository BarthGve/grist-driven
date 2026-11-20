import copy
import types

import pytest

import regles_exemple
from grist_kit.apply_acl import appliquer
from grist_kit.testing.acl import _bits, permis
from grist_kit.testing.faux_grist import ClientFactice
from grist_kit.testing.formules import Base
import schema_helpers


@pytest.mark.parametrize("texte, attendu", [
    ("+CRUD", dict(C=True, R=True, U=True, D=True)),
    ("-R", dict(R=False)),
    ("all", dict(C=True, R=True, U=True, D=True, S=True)),
    ("none", dict(C=False, R=False, U=False, D=False, S=False)),
    ("+R-CUD", dict(R=True, C=False, U=False, D=False)),
    ("-CUD+R", dict(R=True, C=False, U=False, D=False)),
    ("+CR-UD", dict(C=True, R=True, U=False, D=False)),
    ("+S", dict(S=True)),
    ("-S", dict(S=False)),
])
def test_bits(texte, attendu):
    assert _bits(texte) == attendu


SPECIAL = {"key": "schema", "tableId": "*SPECIAL", "colIds": "SchemaEdit"}
REGLES = types.SimpleNamespace(
    RESOURCES=[{"key": "docs", "tableId": "DOCS", "colIds": "*"}, SPECIAL],
    USER_ATTRIBUTES=[],
    RULES=[
        {"resource_key": "docs", "rulePos": 1, "permissionsText": "+R-CUD", "aclFormula": "",
         "memo": "[demo:docs#1] Lecture seule."},
        {"resource_key": "schema", "rulePos": 1, "permissionsText": "+S", "aclFormula": 'user.Access == "owners"',
         "memo": "[demo:schema#1] Propriétaires : structure."},
        {"resource_key": "schema", "rulePos": 2, "permissionsText": "-S", "aclFormula": "",
         "memo": "[demo:schema#2] Les autres : jamais."},
    ])


def _p(droit, acces, table="DOCS"):
    base = Base(schema_helpers, PERSONNES=[], DOCS=[])
    return permis(base, REGLES, "a@exemple.test", table, droit, acces=acces)


def test_mixte_refuse_cud_accorde_r():
    assert _p("R", "editors")
    assert not any(_p(d, "editors") for d in "CUD")


def test_schemaedit_refuse_editeur_accorde_proprietaire():
    assert not _p("S", "editors")
    assert _p("S", "owners")


def test_schemaedit_sans_regle_defaut_grist():
    sans = types.SimpleNamespace(RESOURCES=[], RULES=[], USER_ATTRIBUTES=[])
    base = Base(schema_helpers, PERSONNES=[], DOCS=[])
    assert permis(base, sans, "a@exemple.test", "DOCS", "S", acces="editors")
    assert not permis(base, sans, "a@exemple.test", "DOCS", "S", acces="viewers")


def test_apply_acl_special_idempotent():
    c = ClientFactice()
    plan = appliquer(c, REGLES)
    assert len(plan["ajouts"]) == 3
    assert ("*SPECIAL", "SchemaEdit") in {(r["tableId"], r["colIds"]) for r in c.records["_grist_ACLResources"].values()}
    ecritures = len(c.ecritures())
    assert appliquer(c, REGLES) == {"ajouts": [], "mises_a_jour": [], "obsoletes": []}
    assert len(c.ecritures()) == ecritures
