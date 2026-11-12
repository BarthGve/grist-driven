"""Client Grist en mémoire : assez de l'API pour jouer apply_schema, apply_acl, amorcer, widgets et creer_page."""

import json
import re


class ClientFactice:
    base_url = "https://grist.test/o/demo/api"
    doc_id = "DOC"
    headers = {"Authorization": "Bearer jeton"}

    def __init__(self):
        self.colonnes = {}          # table utilisateur -> ids de colonnes
        self.payloads = {}          # table.colonne -> payload reçu
        self.records = {}           # table (système comprise) -> {id: fields}
        self.champs = {}            # table.colonne -> fields (formule, widgetOptions…) comme les rend Grist
        self.appels = []            # (méthode, endpoint, donnée)
        self._suivant = {}

    # --- aides de test ---
    def ecritures(self):
        return [a for a in self.appels if a[0] != "GET"]

    def ajouter(self, table, fields):
        self._suivant[table] = self._suivant.get(table, 0) + 1
        self.records.setdefault(table, {})[self._suivant[table]] = dict(fields)
        return self._suivant[table]

    def lignes(self, table):
        return [{"id": i, "fields": dict(f)} for i, f in self.records.get(table, {}).items()]

    # --- API ---
    def _make_request(self, methode, endpoint, data=None):
        self.appels.append((methode, endpoint, data))
        if methode == "GET" and endpoint == "/tables":
            return {"tables": [{"id": t} for t in self.colonnes]}
        m = re.fullmatch(r"/tables/(\w+)/columns", endpoint)
        if m and methode == "GET":
            return {"columns": [{"id": c, "fields": dict(self.champs.get(f"{m.group(1)}.{c}", {}))}
                                for c in self.colonnes[m.group(1)]]}
        if m and methode == "POST":
            for col in data["columns"]:
                self.colonnes[m.group(1)].append(col["id"])
                self.payloads[f"{m.group(1)}.{col['id']}"] = col
                self.champs[f"{m.group(1)}.{col['id']}"] = dict(col.get("fields", {}))
            return {}
        if m and methode == "PATCH":
            for col in data["columns"]:
                assert col["id"] in self.colonnes[m.group(1)], col["id"]   # jamais de renommage ni de création
                self.champs.setdefault(f"{m.group(1)}.{col['id']}", {}).update(col["fields"])
            return {}
        if methode == "POST" and endpoint == "/tables":
            for t in data["tables"]:
                self.colonnes[t["id"]] = [c["id"] for c in t["columns"]]
                for c in t["columns"]:
                    self.payloads[f"{t['id']}.{c['id']}"] = c
                    self.champs[f"{t['id']}.{c['id']}"] = dict(c.get("fields", {}))
                self.payloads[f"{t['id']}"] = t
            return {}
        m = re.fullmatch(r"/tables/(\w+)/records", endpoint)
        if m and methode == "GET":
            return {"records": self.lignes(m.group(1))}
        if m and methode == "POST":
            for r in data["records"]:
                self.ajouter(m.group(1), r["fields"])
            return {}
        if methode == "POST" and endpoint == "/apply":
            return self._appliquer(data)
        raise AssertionError((methode, endpoint))

    def _appliquer(self, actions):
        retours = []
        for action in actions:
            type_, table = action[0], action[1]
            if type_ == "AddRecord":
                retours.append(self.ajouter(table, action[3]))
            elif type_ == "UpdateRecord":
                self.records[table][action[2]].update(action[3])
                retours.append(None)
            elif type_ == "RemoveRecord":
                del self.records[table][action[2]]
                retours.append(None)
            elif type_ == "RemoveView":
                del self.records["_grist_Views"][action[1]]
                retours.append(None)
            elif type_ == "CreateViewSection":
                vue = self.ajouter("_grist_Views", {"name": ""})
                section = self.ajouter("_grist_Views_section", {"options": ""})
                retours.append({"viewRef": vue, "sectionRef": section})
            else:
                raise AssertionError(action)
        return {"retValues": retours}


class ReponseFactice:
    def __init__(self, contenu):
        self._contenu = contenu

    def json(self):
        return self._contenu

    def raise_for_status(self):
        pass


class SessionFactice:
    """Session HTTP des écritures du déployeur : applique un PATCH de section sur le client factice."""

    def __init__(self, client, deforme=False):
        self.client, self.deforme, self.patchs = client, deforme, []

    def get(self, url, timeout=None):
        return ReponseFactice({"records": self.client.lignes("_grist_Views_section")})

    def patch(self, url, data=None, timeout=None):
        corps = json.loads(data.decode("utf-8") if isinstance(data, bytes) else data)
        self.patchs.append(corps)
        for r in corps["records"]:
            fields = dict(r["fields"])
            if self.deforme:      # le serveur stocke autre chose que ce qu'on a envoyé
                options = json.loads(fields["options"])
                vue = json.loads(options["customView"])
                vue["widgetOptions"]["_html"] += " "
                options["customView"] = json.dumps(vue)
                fields["options"] = json.dumps(options)
            self.client.records["_grist_Views_section"][r["id"]].update(fields)
        return ReponseFactice({})
