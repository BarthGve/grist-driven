"""Dépose un widget DSFR (HTML d'un seul fichier) dans sa section Grist « Custom widget builder ».

Le HTML va dans `_html`, le JavaScript dans `_js` (base64, avec un chargeur : le pare-feu refuse les
motifs XSS, même dans une donnée). Le document et les sections viennent de `widgets.json`, que
`pages.creer` renseigne à la création de chaque page. Aucun chemin global : l'appelant passe tout.
"""

import base64
import json
import pathlib
import re

from .client import GristErreur, _message

# Scripts de la page. Celui qui n'a qu'un `src` est ignoré : le builder fournit
# déjà `window.grist`, et un `<script src>` ne s'exécuterait pas.
SCRIPT = re.compile(r"[ \t]*<script\b(?P<attrs>[^>]*)>(?P<code>.*?)</script>\n?", re.S)


def separer_html_et_js(contenu):
    """HTML sans ses scripts, et le JavaScript qu'ils portaient."""
    codes = []

    def retirer(m):
        if "src=" not in m.group("attrs"):
            codes.append(m.group("code").strip("\n"))
        return ""

    return SCRIPT.sub(retirer, contenu), "\n\n".join(codes) + "\n"


def chargeur(js):
    """Le JavaScript encodé, avec le bout de code qui le remet en service."""
    charge = base64.b64encode(js.encode("utf-8")).decode("ascii")
    return (
        "(function(){"
        'var s=document.createElement("script");'
        "s.textContent=decodeURIComponent(escape(atob(%s)));"
        "document.body.appendChild(s);})();" % json.dumps(charge)
    )


def litteral_json_echappe(texte):
    """Chaîne JSON où seuls lettres, chiffres et espace restent littéraux.

    Le pare-feu Imperva devant l'API Grist rejette (403) les motifs XSS du HTML
    (balises, gestionnaires `onclick="…"`). Tout le reste est émis en échappement
    `\\uXXXX`, que Grist décode à l'identique : la valeur stockée est celle du
    fichier source. Hors BMP (emoji) : paire de substitution.
    """
    morceaux = []
    for ch in texte:
        point = ord(ch)
        if (48 <= point <= 57 or 65 <= point <= 90
                or 97 <= point <= 122 or point == 0x20):
            morceaux.append(ch)
        elif point > 0xFFFF:
            point -= 0x10000
            morceaux.append("\\u%04x\\u%04x"
                            % (0xD800 + (point >> 10), 0xDC00 + (point & 0x3FF)))
        else:
            morceaux.append("\\u%04x" % point)
    return '"' + "".join(morceaux) + '"'


def corps_patch(section_id, options, vue, attendu):
    """Corps JSON du PATCH de la section, `_html` et `_js` entièrement échappés.

    Le chargeur du `_js` (`createElement("script")`, `appendChild`…) déclenche
    lui aussi le pare-feu : la base64 seule n'y suffit pas.
    """
    # Valeurs placées en jetons, remplacées après coup par leur forme échappée :
    # json.dumps rééchapperait les antislashs sinon.
    jetons = {"_html": "@@HTML@@", "_js": "@@JS@@"}
    vue = {**vue, "widgetOptions": {**(vue.get("widgetOptions") or {}),
                                    **{k: jetons[k] for k in attendu}}}
    brut = json.dumps(vue, ensure_ascii=False)
    for cle, jeton in jetons.items():
        if cle in attendu:
            brut = brut.replace(f'"{jeton}"', litteral_json_echappe(attendu[cle]))
    options = {**options, "customView": brut}
    return json.dumps({"records": [{"id": section_id, "fields": {
        "options": json.dumps(options, ensure_ascii=False)}}]}, ensure_ascii=False)


def ouvrir_session(client):
    """Session HTTP amorcée : le GET initial récupère les cookies Imperva, exigés
    pour toute écriture (sans eux, l'écriture est avalée ou refusée)."""
    import requests
    session = requests.Session()
    session.headers.update(client.headers)
    session.get(f"{client.base_url}/docs/{client.doc_id}/tables", timeout=30)
    return session


def _verifie(reponse):
    """Lève GristErreur (message lisible) sur une réponse HTTP non 2xx de la session."""
    code = getattr(reponse, "status_code", 200)
    if code >= 300:
        raise GristErreur(_message(code, getattr(reponse, "text", "")))
    return reponse


def section_du_widget(config, nom):
    """Entrée de `widgets.json` du widget, ou refus avec un message clair."""
    w = config.get("widgets", {}).get(nom)
    if not w or not w.get("section_id"):
        raise ValueError(
            f"Widget « {nom} » sans section : lancer d'abord `python -m grist_kit creer-page {nom} <TABLE>` (creer-page).")
    return w


def synchroniser_champs(client, table_ref, section_id):
    """Déclare dans la section les colonnes de la table qui y manquent.

    Grist n'envoie au widget que les colonnes déclarées comme champs de sa
    section : une colonne ajoutée après coup à la table reste invisible pour
    lui, sans erreur ni trace.
    """
    colonnes = {
        r["id"]: r["fields"]["colId"]
        for r in client._make_request("GET", "/tables/_grist_Tables_column/records")["records"]
        if r["fields"]["parentId"] == table_ref and r["fields"]["colId"] != "manualSort"
    }
    champs = [
        f for f in client._make_request("GET", "/tables/_grist_Views_section_field/records")["records"]
        if f["fields"]["parentId"] == section_id
    ]
    presentes = {f["fields"]["colRef"] for f in champs}
    manquantes = [ref for ref in colonnes if ref not in presentes]
    if not manquantes:
        return []
    position = max((f["fields"]["parentPos"] for f in champs), default=0)
    actions = [["AddRecord", "_grist_Views_section_field", None,
                {"parentId": section_id, "colRef": ref, "parentPos": position + rang}]
               for rang, ref in enumerate(manquantes, start=1)]
    client._make_request("POST", "/apply", actions)
    return [colonnes[ref] for ref in manquantes]


def verifier_section(client, config, nom) -> None:
    """Refuse de toucher à une section qui n'est pas celle du widget dans ce document.

    Les ids de `widgets.json` valent pour le document où la page a été créée : sur un autre document,
    ils désigneraient une section sans rapport.
    """
    if config.get("doc_id") and config["doc_id"] != client.doc_id:
        raise ValueError(
            f"widgets.json est lié au document {config['doc_id']}, pas à {client.doc_id} : "
            "dépôt refusé (créer la page sur ce document avec creer-page).")
    w = section_du_widget(config, nom)
    sid = w["section_id"]
    section = next((r for r in client._make_request("GET", "/tables/_grist_Views_section/records")["records"]
                    if r["id"] == sid), None)
    table = None
    if section and section["fields"].get("tableRef") == w["table_ref"]:
        table = next((r for r in client._make_request("GET", "/tables/_grist_Tables/records")["records"]
                      if r["id"] == w["table_ref"]), None)
    if not (section and table and table["fields"].get("tableId") == w["table_id"]
            and "customView" in (section["fields"].get("options") or "")):
        raise ValueError(
            f"La section {sid} de widgets.json n'existe pas dans ce document, n'est pas liée à la table "
            f"« {w['table_id']} » ou n'est pas un widget personnalisé (widget « {nom} ») : "
            "créer la page sur ce document (creer-page).")


def deployer(client, config, nom, racine, check=False, session=None) -> int:
    """Dépose le widget `nom` dans sa section. 0 = à jour ou déposé ; 1 = écart en mode `check`."""
    verifier_section(client, config, nom)
    w = section_du_widget(config, nom)
    html, js = separer_html_et_js((pathlib.Path(racine) / w["fichier"]).read_text(encoding="utf-8"))
    attendu = {"_html": html, "_js": chargeur(js)}
    if not check:
        ajoutees = synchroniser_champs(client, w["table_ref"], w["section_id"])
        if ajoutees:
            print(f"colonnes déclarées à la section : {', '.join(ajoutees)}")
    lignes = client._make_request("GET", "/tables/_grist_Views_section/records")["records"]
    options = json.loads(next(r for r in lignes if r["id"] == w["section_id"])["fields"]["options"])
    vue = json.loads(options["customView"])
    actuel = vue.get("widgetOptions") or {}

    ecarts = [c for c in ("_html", "_js") if actuel.get(c) != attendu[c]]
    if not ecarts:
        print("widget à jour")
        return 0
    if check:
        print(f"à mettre à jour : {', '.join(ecarts)}")
        return 1

    session = session or ouvrir_session(client)
    url = f"{client.base_url}/docs/{client.doc_id}/tables/_grist_Views_section/records"
    corps = corps_patch(w["section_id"], options, vue, attendu)
    _verifie(session.patch(url, data=corps.encode("utf-8"), timeout=90))
    relu = next(r for r in _verifie(session.get(url, timeout=60)).json()["records"]
                if r["id"] == w["section_id"])
    stocke = json.loads(json.loads(relu["fields"]["options"])["customView"])["widgetOptions"]
    if stocke.get("_html") != html or stocke.get("_js") != attendu["_js"]:
        raise GristErreur("Écriture non conforme au fichier source : la section ne contient pas ce qui a été envoyé.")
    print(f"déposé : {', '.join(ecarts)} ({len(html)} et {len(js)} caractères) — recharger la page Grist")
    return 0
