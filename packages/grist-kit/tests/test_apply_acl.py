import copy
import json
import types

import pytest

import regles_exemple
from grist_kit.apply_acl import ETIQUETTE, appliquer, planifier, ressource_a_renommer
from grist_kit.testing.faux_grist import ClientFactice


def _module(**remplace):
    m = types.SimpleNamespace(**{k: copy.deepcopy(getattr(regles_exemple, k))
                                 for k in ("RESOURCES", "RULES", "USER_ATTRIBUTES")})
    for k, v in remplace.items():
        setattr(m, k, v)
    return m


def _regles(client):
    return client.records.get("_grist_ACLRules", {})


def _par_memo(client, etiquette):
    return next((i, r) for i, r in _regles(client).items() if (r.get("memo") or "").startswith(etiquette))


def test_etiquette_accepte_tout_prefixe_de_projet():
    assert ETIQUETTE.match("[demo2:docs_secret#12] texte").groups() == ("docs_secret", "12")
    assert not ETIQUETTE.match("sans etiquette")


def test_regle_nouvelle_est_ajoutee():
    c = ClientFactice()
    plan = appliquer(c, regles_exemple)
    assert len(plan["ajouts"]) == 4 and plan["mises_a_jour"] == [] and plan["obsoletes"] == []
    assert len([r for r in _regles(c).values() if r.get("memo")]) == 4
    # ressources créées, attribut utilisateur posé
    assert {(r["tableId"], r["colIds"]) for r in c.records["_grist_ACLResources"].values()} == {
        ("*", "*"), ("DOCS", "*"), ("DOCS", "secret")}
    attrs = [json.loads(r["userAttributes"]) for r in _regles(c).values() if r.get("userAttributes")]
    assert attrs == [{"name": "Personne", "tableId": "PERSONNES", "lookupColId": "email_cle", "charId": "Email"}]


def test_deuxieme_passage_ne_change_rien():
    c = ClientFactice()
    appliquer(c, regles_exemple)
    avant = len(c.ecritures())
    plan = appliquer(c, regles_exemple)
    assert plan == {"ajouts": [], "mises_a_jour": [], "obsoletes": []}
    assert len(c.ecritures()) == avant


def test_formule_modifiee_met_a_jour_en_place():
    c = ClientFactice()
    appliquer(c, regles_exemple)
    m = _module()
    m.RULES[1]["aclFormula"] = "rec.auteur.id == user.Personne.id and True"
    plan = appliquer(c, m)
    assert plan["ajouts"] == [] and len(plan["mises_a_jour"]) == 1
    assert len([r for r in _regles(c).values() if r.get("memo")]) == 4        # pas de doublon
    assert _par_memo(c, "[demo:docs#2]")[1]["aclFormula"].endswith("and True")


def test_memo_modifie_met_a_jour_en_place():
    # une règle insérée décale les suivantes : leur texte (donc leur numéro) doit suivre
    plan = planifier(
        [{"memo": "[demo:docs#1] nouveau texte", "aclFormula": "", "permissionsText": "+R", "rulePos": 1}],
        [{"id": 7, "memo": "[demo:docs#1] ancien texte", "aclFormula": "", "permissionsText": "+R", "rulePos": 1}])
    assert plan["mises_a_jour"] == [(7, {"memo": "[demo:docs#1] nouveau texte"})]


def test_regle_retiree_signalee_pas_supprimee():
    c = ClientFactice()
    appliquer(c, regles_exemple)
    m = _module()
    m.RULES = m.RULES[:-1]
    plan = appliquer(c, m)
    assert len(plan["obsoletes"]) == 1
    assert len([r for r in _regles(c).values() if r.get("memo")]) == 4


def test_prune_supprime_les_obsoletes():
    c = ClientFactice()
    appliquer(c, regles_exemple)
    m = _module()
    m.RULES = m.RULES[:-1]
    plan = appliquer(c, m, prune=True)
    assert len(plan["obsoletes"]) == 1
    assert len([r for r in _regles(c).values() if r.get("memo")]) == 3
    assert not any((r.get("memo") or "").startswith("[demo:docs_secret#1]") for r in _regles(c).values())


def test_prune_retire_avant_de_mettre_a_jour():
    c = ClientFactice()
    appliquer(c, regles_exemple)
    m = _module()
    m.RULES = m.RULES[1:]                 # retire docs#1 ; docs#2 change de formule
    m.RULES[0]["aclFormula"] = "True"
    appliquer(c, m, prune=True)
    types_ = [a[0] for a in c.appels[-1][2]]
    assert types_.index("RemoveRecord") < types_.index("UpdateRecord")


def test_ordre_relatif_force_si_different():
    existantes = [
        {"id": 1, "memo": "[demo:docs#1] a", "aclFormula": "x", "permissionsText": "+R", "rulePos": 2},
        {"id": 2, "memo": "[demo:docs#2] b", "aclFormula": "y", "permissionsText": "+R", "rulePos": 1},
    ]
    souhaitees = [
        {"memo": "[demo:docs#1] a", "aclFormula": "x", "permissionsText": "+R", "rulePos": 1},
        {"memo": "[demo:docs#2] b", "aclFormula": "y", "permissionsText": "+R", "rulePos": 2},
    ]
    plan = planifier(souhaitees, existantes)
    assert sorted(plan["mises_a_jour"]) == [(1, {"rulePos": 1}), (2, {"rulePos": 2})]
    # ordre déjà bon (positions fractionnées par Grist) : rien à forcer
    existantes[0]["rulePos"], existantes[1]["rulePos"] = 1.5, 1.75
    assert planifier(souhaitees, existantes)["mises_a_jour"] == []


def test_regle_sans_etiquette_refusee():
    c = ClientFactice()
    m = _module()
    m.RULES[2]["memo"] = "Lecture pour tous."
    with pytest.raises(ValueError, match="étiquette"):
        appliquer(c, m)
    assert c.appels == []                 # aucun appel réseau, aucun ajout


def test_etiquettes_en_double_refusees():
    c = ClientFactice()
    m = _module()
    m.RULES[1]["memo"] = m.RULES[0]["memo"]
    with pytest.raises(ValueError, match="double"):
        appliquer(c, m)
    assert c.appels == []


def test_regles_module_obligatoire():
    with pytest.raises(TypeError):
        appliquer(ClientFactice())


def test_dry_run_n_ecrit_rien():
    c = ClientFactice()
    plan = appliquer(c, regles_exemple, dry_run=True)
    assert c.ecritures() == [] and len(plan["ajouts"]) == 4


def test_le_post_apply_envoie_les_actions_a_la_racine():
    c = ClientFactice()
    appliquer(c, regles_exemple)
    posts = [a for a in c.appels if a[:2] == ("POST", "/apply")]
    assert posts and all(isinstance(a[2], list) for a in posts)       # pas {"actions": [...]}
    assert all(isinstance(act, list) for a in posts for act in a[2])


def test_colonnes_changees_renomment_la_ressource_au_lieu_d_en_creer_une():
    c = ClientFactice()
    appliquer(c, regles_exemple)
    m = _module()
    m.RESOURCES[2]["colIds"] = "secret,autre"
    appliquer(c, m)
    cols = [r["colIds"] for r in c.records["_grist_ACLResources"].values() if r["tableId"] == "DOCS"]
    assert sorted(cols) == ["*", "secret,autre"]


def test_ressource_a_renommer():
    existantes = [{"id": 1, "resource": 10, "memo": "[demo:docs#1] x"}]
    ressources = {10: {"tableId": "DOCS"}}
    assert ressource_a_renommer("docs", "DOCS", existantes, ressources) == 10
    assert ressource_a_renommer("autre", "DOCS", existantes, ressources) is None
    assert ressource_a_renommer("docs", "AUTRE", existantes, ressources) is None


def test_attribut_utilisateur_modifie_est_mis_a_jour():
    c = ClientFactice()
    appliquer(c, regles_exemple)
    m = _module()
    m.USER_ATTRIBUTES[0]["lookupColId"] = "courriel"
    # dry-run : signalé dans le plan, rien d'écrit
    avant = len(c.ecritures())
    plan = appliquer(c, m, dry_run=True)
    assert len(plan["mises_a_jour"]) == 1 and len(c.ecritures()) == avant
    plan = appliquer(c, m)
    attrs = [json.loads(r["userAttributes"]) for r in _regles(c).values() if r.get("userAttributes")]
    assert len(attrs) == 1 and attrs[0]["lookupColId"] == "courriel"
    assert appliquer(c, m) == {"ajouts": [], "mises_a_jour": [], "obsoletes": []}


def test_regle_changee_de_ressource_est_mise_a_jour():
    # dérive : la règle a été déplacée sur une autre ressource dans le document
    c = ClientFactice()
    appliquer(c, regles_exemple)
    id_defaut = next(i for i, r in c.records["_grist_ACLResources"].items() if r["tableId"] == "*")
    id_regle, regle = _par_memo(c, "[demo:docs#3]")
    voulue = regle["resource"]
    regle["resource"] = id_defaut
    plan = appliquer(c, regles_exemple)
    assert plan["mises_a_jour"] == [(id_regle, {"resource": voulue})] and plan["ajouts"] == []
    assert _par_memo(c, "[demo:docs#3]")[1]["resource"] == voulue


def test_etiquette_incoherente_avec_resource_key_refusee():
    c = ClientFactice()
    m = _module()
    m.RULES[2]["resource_key"] = "default"        # étiquette `docs`, ressource `default`
    with pytest.raises(ValueError, match="resource_key"):
        appliquer(c, m)
    assert c.appels == []
