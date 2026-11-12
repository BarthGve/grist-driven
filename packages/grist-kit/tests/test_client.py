import pytest

from grist_kit import GristClient, GristErreur
from grist_kit.testing.faux_grist import ClientFactice


@pytest.fixture(autouse=True)
def _env_propre(monkeypatch):
    for v in ("GRIST_API_KEY", "GRIST_DOC_ID", "GRIST_API_HOST"):
        monkeypatch.delenv(v, raising=False)


def test_cle_absente_leve_valueerror():
    with pytest.raises(ValueError, match="GRIST_API_KEY"):
        GristClient(doc_id="DOC")


def test_doc_absent_leve_valueerror():
    with pytest.raises(ValueError, match="GRIST_DOC_ID"):
        GristClient(api_key="k")


def test_hote_lu_dans_l_environnement(monkeypatch):
    monkeypatch.setenv("GRIST_API_HOST", "https://grist.exemple.test/api")
    c = GristClient(api_key="k", doc_id="DOC")
    assert c.base_url == "https://grist.exemple.test/api"
    monkeypatch.delenv("GRIST_API_HOST")
    assert GristClient(api_key="k", doc_id="DOC").base_url == "https://grist.numerique.gouv.fr/api"


class _Reponse:
    def __init__(self, code, texte):
        self.status_code, self.text, self.headers = code, texte, {}

    def json(self):
        return {}


class _Session:
    def __init__(self, reponse):
        self.reponse, self.appels = reponse, 0

    def request(self, *a, **k):
        self.appels += 1
        return self.reponse


def _client(reponse):
    c = GristClient(api_key="k", doc_id="DOC", base_url="https://grist.exemple.test/api")
    c.cadence = 0
    c.pause_refus = 0
    c._session = _Session(reponse)
    return c


def test_requete_403_leve_erreur_lisible():
    c = _client(_Reponse(403, "Request unsuccessful. Incapsula incident ID: 1"))
    with pytest.raises(GristErreur) as e:
        c._make_request("GET", "/tables")
    msg = str(e.value)
    assert "pare-feu" in msg and "403" in msg
    assert c._session.appels == 3  # 1 essai + 2 nouvelles tentatives


def test_requete_413_message_clair():
    c = _client(_Reponse(413, "too big"))
    with pytest.raises(GristErreur, match="413"):
        c._make_request("POST", "/apply", [])


def test_fetch_table_via_faux_client():
    faux = ClientFactice()
    faux.colonnes["T"] = ["a"]
    faux.ajouter("T", {"a": 1})
    # fetch_table / add_record / update_record de GristClient, branchés sur le faux transport
    c = GristClient(api_key="k", doc_id="DOC")
    c._make_request = faux._make_request
    assert c.fetch_table("T") == [{"id": 1, "fields": {"a": 1}}]
