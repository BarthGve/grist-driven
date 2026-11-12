"""Applique un schéma déclaratif à un document Grist, de façon idempotente.

`schema_module` expose `TABLES` (liste ordonnée de tables, chacune avec `id`, `label`, `columns`) et
`colonnes_auto_referentes()` (liste de couples `(table, colonne)`). Chaque colonne : `id`, `label`, `type`,
et au choix `formula`, `declenchee`, `choices`, `options`.
"""

import json
import logging

logger = logging.getLogger(__name__)


def _colonne_payload(col):
    """Payload Grist d'une colonne à partir de sa définition."""
    fields = {"label": col["label"], "type": col["type"]}
    if col.get("formula"):
        fields["formula"] = col["formula"]
        # Formule déclenchée : colonne de données calculée à la création de la ligne seulement
        # (recalcWhen 0 sans recalcDeps), jamais réécrite ensuite.
        fields["isFormula"] = not col.get("declenchee", False)
        if col.get("declenchee"):
            fields["recalcWhen"] = 0
    if col.get("choices"):
        fields["widgetOptions"] = json.dumps({"choices": col["choices"]})
    elif col.get("options"):
        fields["widgetOptions"] = json.dumps(col["options"])
    return {"id": col["id"], "fields": fields}


def _payload_ajout(col):
    """Colonne ajoutée à une table existante : sans formule, Grist la crée avec isFormula vrai, et la première
    écriture d'un non-propriétaire serait refusée. On force donc une colonne de données."""
    payload = _colonne_payload(col)
    payload["fields"].setdefault("isFormula", False)
    return payload


def _tables_existantes(client):
    return {t["id"] for t in client._make_request("GET", "/tables").get("tables", [])}


def _colonnes_existantes(client, table_id):
    return {c["id"] for c in client._make_request("GET", f"/tables/{table_id}/columns").get("columns", [])}


def appliquer(client, schema_module, dry_run=False):
    """Crée les tables et colonnes manquantes. Ne supprime ni ne modifie jamais rien d'existant.

    Deux passes. La première crée les tables sans leurs colonnes auto-référentes : Grist résout la cible d'un
    `Ref` à la création de la colonne, et une table ne peut pas se référencer avant d'exister. La seconde ajoute
    ces colonnes. Les références entre tables distinctes sont couvertes par l'ordre de `TABLES`.

    Les colonnes de formule d'une table neuve sont ajoutées une à une, après les colonnes de données : le
    pare-feu de l'API juge la requête entière et refuse parfois (403) une table envoyée d'un bloc avec toutes
    ses formules, alors que chaque formule passe seule.

    Les formules et choix déjà en place ne sont pas réalignés ici (voir `maj_formules`).
    """
    rapport = {"tables_creees": [], "colonnes_ajoutees": [], "inchangees": []}
    auto_referentes = set(schema_module.colonnes_auto_referentes())
    existantes = _tables_existantes(client)
    tables = {t["id"]: t for t in schema_module.TABLES}

    for table in schema_module.TABLES:
        table_id = table["id"]
        colonnes = [c for c in table["columns"] if (table_id, c["id"]) not in auto_referentes]

        if table_id not in existantes:
            rapport["tables_creees"].append(table_id)
            if not dry_run:
                donnees = [c for c in colonnes if not c.get("formula")]
                client._make_request("POST", "/tables", {"tables": [{
                    "id": table_id, "columns": [_colonne_payload(c) for c in donnees]}]})
                for c in colonnes:
                    if c.get("formula"):
                        client._make_request("POST", f"/tables/{table_id}/columns", {"columns": [_colonne_payload(c)]})
                logger.info("Table %s créée", table_id)
            continue

        deja = _colonnes_existantes(client, table_id)
        manquantes = [c for c in colonnes if c["id"] not in deja]
        if not manquantes:
            rapport["inchangees"].append(table_id)
            continue
        for col in manquantes:
            rapport["colonnes_ajoutees"].append(f"{table_id}.{col['id']}")
            if not dry_run:
                client._make_request("POST", f"/tables/{table_id}/columns", {"columns": [_payload_ajout(col)]})
                logger.info("Colonne %s.%s ajoutée", table_id, col["id"])

    for table_id, colonne_id in sorted(auto_referentes):
        if table_id in existantes and colonne_id in _colonnes_existantes(client, table_id):
            continue
        rapport["colonnes_ajoutees"].append(f"{table_id}.{colonne_id}")
        if dry_run:
            continue
        col = next(c for c in tables[table_id]["columns"] if c["id"] == colonne_id)
        client._make_request("POST", f"/tables/{table_id}/columns", {"columns": [_payload_ajout(col)]})
        logger.info("Colonne auto-référente %s.%s ajoutée", table_id, colonne_id)

    return rapport
