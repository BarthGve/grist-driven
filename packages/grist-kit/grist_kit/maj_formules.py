"""Aligne sur le schéma les formules et listes de choix des colonnes DÉJÀ présentes dans le document.

`apply_schema` n'ajoute que ce qui manque : il ne met jamais à jour une formule ni des choix existants.
Ce module le fait (PATCH avec l'identifiant explicite de la colonne : jamais de renommage), sans écrire de
données. Les tables et colonnes absentes sont signalées : c'est le travail d'`apply_schema`.

`schema_module` expose `TABLES`, comme pour `apply_schema`.
"""

import json

from grist_kit.client import GristErreur


def _options(texte):
    """widgetOptions décodées ({} si vide), ou None si le JSON est illisible."""
    try:
        return json.loads(texte) if texte else {}
    except ValueError:
        return None


def appliquer(client, schema_module, dry_run=False):
    """Rapport {mises_a_jour, divergentes, inchangees, absentes, illisibles}.

    Lève `GristErreur`, sans rien écrire, tant qu'une table ou une colonne citée par le schéma manque dans
    le document (en simulation, elle est seulement listée dans `absentes`).
    Les colonnes de données dont le schéma attend une formule sont listées `divergentes`, jamais écrasées.
    Les choix ne font qu'ajouter les valeurs du schéma manquantes : ordre et choix ajoutés à la main conservés.
    """
    rapport = {"mises_a_jour": [], "divergentes": [], "inchangees": [], "absentes": [], "illisibles": []}
    patchs = []
    tables = {t["id"] for t in client._make_request("GET", "/tables").get("tables", [])}
    for table in schema_module.TABLES:
        if table["id"] not in tables:
            rapport["absentes"].append(table["id"])
            continue
        existantes = {c["id"]: c.get("fields", {}) for c in
                      client._make_request("GET", f"/tables/{table['id']}/columns").get("columns", [])}
        for col in table["columns"]:
            nom = f"{table['id']}.{col['id']}"
            suivie = bool(col.get("formula")) or col.get("type") == "Choice"
            if col["id"] not in existantes:
                if suivie:
                    rapport["absentes"].append(nom)
                continue
            if not suivie:
                continue
            champs, doc = {}, existantes[col["id"]]
            if col.get("formula"):
                calculee = not col.get("declenchee", False)
                if bool(doc.get("isFormula")) != calculee:
                    # Patcher la seule formule changerait le comportement de la colonne : à traiter à la main.
                    rapport["divergentes"].append(
                        f"{nom} : " + ("colonne de données dans le document, formule dans le schéma" if calculee
                                       else "formule calculée dans le document, formule déclenchée dans le schéma"))
                    continue
                if (doc.get("formula") or "").strip() != col["formula"].strip():
                    champs["formula"] = col["formula"]
            if col.get("type") == "Choice":
                options = _options(doc.get("widgetOptions"))
                if options is None:
                    rapport["illisibles"].append(nom)
                else:
                    deja = options.get("choices") or []
                    manquants = [c for c in col.get("choices", []) if c not in deja]
                    if manquants:
                        champs["widgetOptions"] = json.dumps({**options, "choices": deja + manquants})
            if champs:
                patchs.append((table["id"], col["id"], champs))
                rapport["mises_a_jour"].append(nom)
            else:
                rapport["inchangees"].append(nom)
    if rapport["absentes"] and not dry_run:
        raise GristErreur(f"Rien n'a été écrit : absentes du document ({', '.join(rapport['absentes'])}). "
                          "Lancer d'abord apply_schema.")
    if not dry_run:
        for table_id, col_id, champs in patchs:
            client._make_request("PATCH", f"/tables/{table_id}/columns",
                                 {"columns": [{"id": col_id, "fields": champs}]})
    return rapport
