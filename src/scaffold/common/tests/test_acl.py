from grist_kit import apply_acl
from grist_kit.testing.acl import permis
from grist_kit.testing.faux_grist import ClientFactice
from grist_kit.testing.formules import Base

from {{package}} import acl_rules, schema


def _base():
    return Base(schema, EXEMPLES=[{"titre": "A"}])


def test_proprietaire_supprime_lecteur_non():
    base = _base()
    ligne = base.ligne("EXEMPLES", 1)
    assert permis(base, acl_rules, "a@exemple.test", "EXEMPLES", "D", rec=ligne, acces="owners")
    assert not permis(base, acl_rules, "b@exemple.test", "EXEMPLES", "D", rec=ligne, acces="editors")
    assert permis(base, acl_rules, "b@exemple.test", "EXEMPLES", "R", rec=ligne, acces="editors")


def test_acl_dry_run_ne_leve_rien():
    apply_acl.appliquer(ClientFactice(), acl_rules, dry_run=True)
