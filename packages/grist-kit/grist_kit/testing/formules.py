"""Petit Grist en mémoire pour exécuter les formules du schéma du projet hors du document.

`Base` charge des lignes brutes (références = identifiants), résout `$col` sur la ligne courante,
suit les références (`$unite.type`), calcule les colonnes de formule à la demande et expose
`lookupRecords` / `lookupOne` / `all` comme Grist. Une référence vide (id 0) donne une ligne
« fausse » dont les colonnes valent leur valeur par défaut, comme dans Grist.
"""

import datetime as dt
import re
import textwrap
from zoneinfo import ZoneInfo


DEFAUTS = {"Text": "", "Int": 0, "Numeric": 0.0, "Bool": False, "Choice": "", "Date": None}


def _defaut(col):
    if col["type"].startswith("Ref:"):
        return 0
    if col["type"].startswith("DateTime"):
        return None
    return DEFAUTS[col["type"]]


class Ligne:
    def __init__(self, base, table, id_, valeurs):
        self._base, self._table, self.id, self._valeurs, self._memo = base, table, id_, valeurs, {}

    def __bool__(self):
        return self.id != 0

    def __getattr__(self, nom):
        if nom.startswith("_"):
            raise AttributeError(nom)
        if nom in self._memo:
            return self._memo[nom]
        col = self._base.colonne(self._table, nom)
        if col is None:
            raise AttributeError(f"{self._table}.{nom}")
        if self.id == 0:
            valeur = _defaut(col)
        elif col.get("formula") and not col.get("declenchee"):
            valeur = self._base.executer(col["formula"], self)
        else:
            valeur = self._valeurs.get(nom, _defaut(col))
        if col["type"].startswith("Ref:"):
            valeur = valeur.id if isinstance(valeur, Ligne) else valeur   # formule qui rend un enregistrement
            valeur = self._base.ligne(col["type"][4:], valeur or 0)
        elif col["type"].startswith("DateTime") and isinstance(valeur, (int, float)):
            # Comme Grist : la valeur est locale au fuseau déclaré (« DateTime:Europe/Paris »).
            fuseau = ZoneInfo(col["type"].partition(":")[2]) if ":" in col["type"] else dt.timezone.utc
            valeur = dt.datetime.fromtimestamp(valeur, tz=fuseau)
        self._memo[nom] = valeur
        return valeur

    def __repr__(self):
        return f"<{self._table} {self.id}>"


class Table:
    def __init__(self, base, nom):
        self._base, self._nom = base, nom

    @property
    def all(self):
        return [self._base.ligne(self._nom, i) for i in self._base.ids(self._nom)]

    def lookupRecords(self, **criteres):
        return [l for l in self.all if all(self._egal(getattr(l, k), v) for k, v in criteres.items())]

    def lookupOne(self, **criteres):
        trouvees = self.lookupRecords(**criteres)
        return trouvees[0] if trouvees else self._base.ligne(self._nom, 0)

    @staticmethod
    def _egal(valeur, voulu):
        return (valeur.id == (voulu.id if isinstance(voulu, Ligne) else voulu)) if isinstance(valeur, Ligne) else valeur == voulu


class Base:
    def __init__(self, schema_module, maintenant=dt.datetime(2026, 10, 20, 12, 0, tzinfo=dt.timezone.utc), **tables):
        """`schema_module` : module du projet exposant `TABLES`. `tables` : nom de table -> liste de dicts ;
        l'identifiant par défaut est le rang (à partir de 1)."""
        self.schema = schema_module
        self.maintenant = maintenant
        self._tables = {t["id"]: t for t in schema_module.TABLES}
        self._lignes = {t: {} for t in self._tables}
        for nom, rows in tables.items():
            for rang, valeurs in enumerate(rows, start=1):
                valeurs = dict(valeurs)
                self._lignes[nom][valeurs.pop("id", rang)] = valeurs
        self._cache = {}

    def avec(self, table, id_=None, **valeurs):
        """Base résultante d'une écriture : ligne modifiée (`id_`) ou ajoutée. Retourne (base, ligne) :
        la ligne est le `newRec` d'une règle d'accès."""
        suivante = Base(self.schema, maintenant=self.maintenant)
        suivante._lignes = {t: {i: dict(v) for i, v in lignes.items()} for t, lignes in self._lignes.items()}
        if id_ is None:
            id_ = max(suivante._lignes[table], default=0) + 1
        suivante._lignes[table].setdefault(id_, {}).update(valeurs)
        return suivante, suivante.ligne(table, id_)

    def colonne(self, table, nom):
        if nom == "id":
            return {"id": "id", "type": "Int"}
        return next((c for c in self._tables[table]["columns"] if c["id"] == nom), None)

    def ids(self, table):
        return list(self._lignes[table])

    def ligne(self, table, id_):
        if id_ == 0 or id_ not in self._lignes[table]:
            return Ligne(self, table, 0, {})
        cle = (table, id_)
        if cle not in self._cache:
            self._cache[cle] = Ligne(self, table, id_, self._lignes[table][id_])
        return self._cache[cle]

    def __getitem__(self, table):
        return Table(self, table)

    def executer(self, formule, rec):
        corps = re.sub(r"\$(\w+)", r"rec.\1", formule)
        if "\n" not in corps:
            corps = f"return {corps}"
        def now(tz=None):
            return self.maintenant.astimezone(ZoneInfo(tz)) if tz else self.maintenant

        def dtime(valeur, tz=None):
            return valeur.replace(tzinfo=ZoneInfo(tz)) if tz else valeur

        espace = {"NOW": now, "DTIME": dtime, "TODAY": lambda: self.maintenant.date(),
                  **{t: self[t] for t in self._tables}}
        # Le bac à sable de Grist n'a ni pytz ni dateutil : un import hors liste échoue ici aussi.
        if re.search(r"\b(?:pytz|dateutil)\b", corps):
            raise ImportError("module absent du bac à sable des formules Grist")
        exec("def _f(rec):\n" + textwrap.indent(corps, "  "), espace)  # noqa: S102 — formules du dépôt uniquement
        return espace["_f"](rec)

    def toutes_les_formules(self):
        """Évalue chaque colonne de formule de chaque ligne ; sert de test de fumée."""
        for table, lignes in self._lignes.items():
            for id_ in lignes:
                ligne = self.ligne(table, id_)
                for col in self._tables[table]["columns"]:
                    if col.get("formula") and not col.get("declenchee"):
                        getattr(ligne, col["id"])
