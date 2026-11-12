"""Création de la page Grist d'un widget, consignée dans `widgets.json`.

Idempotent : un widget déjà consigné n'est pas recréé. Les chemins sont passés par
l'appelant (aucun chemin global).
"""

import json
import pathlib

ACCES = ("read table", "full")

BUILDER = {
    "name": "Custom widget builder",
    "url": "https://gristgouv.github.io/gristlabs-widgets/custom-widget-builder/index.html",
    "widgetId": "@berhalak/custom-widget-builder",
    "published": True,
    "accessLevel": "none",
    "renderAfterReady": True,
    "description": "Build custom widgets with HTML and JavaScript, right inside Grist.",
}


def options_section(acces: str) -> str:
    """`options` d'une section « Custom widget builder » vide."""
    vue = {
        "mode": "url", "url": None, "widgetDef": BUILDER, "access": acces,
        "pluginId": "", "sectionId": "", "renderAfterReady": True,
        "widgetId": BUILDER["widgetId"], "columnsMapping": None,
        "widgetOptions": {},
    }
    return json.dumps({"customView": json.dumps(vue, ensure_ascii=False)}, ensure_ascii=False)


def charger_config(chemin) -> dict:
    """Lit `widgets.json` ; une configuration vide si le fichier n'existe pas."""
    chemin = pathlib.Path(chemin)
    if not chemin.exists():
        return {"doc_id": "", "widgets": {}}
    return json.loads(chemin.read_text(encoding="utf-8"))


def ecrire_config(chemin, config: dict) -> None:
    pathlib.Path(chemin).write_text(
        json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def creer(client, config: dict, nom: str, table_id: str, titre: str, acces: str = "full") -> dict:
    """Crée page + section personnalisée ; renvoie l'entrée de widgets.json (à écrire par l'appelant)."""
    if acces not in ACCES:
        raise ValueError(f"Niveau d'accès « {acces} » invalide : {' ou '.join(ACCES)}.")
    if config.get("doc_id") and config["doc_id"] != client.doc_id:
        raise ValueError(
            f"widgets.json est lié au document {config['doc_id']}, pas à {client.doc_id} : création refusée.")
    widgets = config.setdefault("widgets", {})
    if widgets.get(nom, {}).get("section_id"):
        return widgets[nom]

    tables = client._make_request("GET", "/tables/_grist_Tables/records")["records"]
    table_ref = next((t["id"] for t in tables if t["fields"]["tableId"] == table_id), None)
    if table_ref is None:
        raise ValueError(f"Table « {table_id} » introuvable dans le document {client.doc_id}.")

    # viewRef 0 : nouvelle page. Le résultat donne les identifiants créés.
    cree = client._make_request("POST", "/apply", [
        ["CreateViewSection", table_ref, 0, "custom", None, None]])["retValues"][0]
    client._make_request("POST", "/apply", [
        ["UpdateRecord", "_grist_Views", cree["viewRef"], {"name": titre}],
        ["UpdateRecord", "_grist_Views_section", cree["sectionRef"], {"options": options_section(acces)}],
    ])
    entree = {"fichier": f"{nom}.html", "table_ref": table_ref, "table_id": table_id,
              "section_id": cree["sectionRef"], "view_ref": cree["viewRef"], "acces": acces}
    widgets[nom] = entree
    config["doc_id"] = client.doc_id
    return entree
