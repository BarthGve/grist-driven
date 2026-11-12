"""Profil `ui-kit` : construit `widgets_ui/` (Vite) et dépose le bundle gzip dans la section du widget.

Un bundle React dépasse la limite de l'API Grist (413 vers 1 Mo) : le JavaScript est compressé
(gzip niveau 9, horodatage fixé, sortie stable) puis encodé en base64 ; le navigateur le décompresse
(`DecompressionStream`). Le reste (garde-fou section/document, corps échappé, relecture) vient de `deployer`.
"""

import base64
import gzip
import json
import pathlib
import re
import shutil
import subprocess

from .client import GristErreur
from .deployer import (_verifie, corps_patch, ouvrir_session, section_du_widget,
                       separer_html_et_js, synchroniser_champs, verifier_section)

# Taille maximale du corps d'un PATCH accepté par l'API Grist.
LIMITE_API_OCTETS = 1_000_000
NODE_MIN = 20


def chargeur_gzip(js):
    """JavaScript compressé (gzip niveau 9, `mtime=0`) puis base64, avec le code qui le remet en service."""
    charge = base64.b64encode(gzip.compress(js.encode("utf-8"), 9, mtime=0)).decode("ascii")
    return ("(async function(){"
            "var b=Uint8Array.from(atob(%s),function(c){return c.charCodeAt(0)});"
            "var t=await new Response(new Blob([b]).stream().pipeThrough(new DecompressionStream(\"gzip\"))).text();"
            "var s=document.createElement(\"script\");s.textContent=t;document.body.appendChild(s);})();" % json.dumps(charge))


def _version_node():
    node = shutil.which("node")
    if not node:
        raise GristErreur(f"Node.js absent : le profil ui-kit exige Node ≥ {NODE_MIN} (https://nodejs.org).")
    sortie = subprocess.run([node, "--version"], capture_output=True, text=True).stdout.strip()
    m = re.match(r"v?(\d+)", sortie)
    if not m or int(m.group(1)) < NODE_MIN:
        raise GristErreur(f"Node.js {sortie or 'inconnu'} trop ancien : le profil ui-kit exige Node ≥ {NODE_MIN}.")
    return node


def construire(widgets_ui, entrees=None):
    """`npm ci` puis `node build.mjs [entrées]` dans `widgets_ui` ; renvoie la taille en Ko de chaque entrée."""
    node = _version_node()
    npm = shutil.which("npm")
    if not npm:
        raise GristErreur("npm absent : il vient avec Node.js (https://nodejs.org).")
    for cmd in ([npm, "ci"], [node, "build.mjs", *(entrees or [])]):
        r = subprocess.run(cmd, cwd=widgets_ui, capture_output=True, text=True)
        if r.returncode:
            raise GristErreur(f"`{pathlib.Path(cmd[0]).name} {' '.join(cmd[1:])}` a échoué "
                              f"(code {r.returncode}) :\n{(r.stdout + r.stderr).strip()[-1500:]}")
    return {m.group(1): int(m.group(2)) for m in re.finditer(r"^(\S+) : (\d+) Ko$", r.stdout, re.M)}


def deployer_uikit(client, config, nom, widgets_ui, check=False, session=None) -> int:
    """Dépose `widgets_ui/dist/<entrée>.html` dans la section de `nom`. 0 = à jour ou déposé ; 1 = écart en `check`.

    L'entrée est `config["widgets"][nom]["entree"]` (défaut : `nom`).
    """
    verifier_section(client, config, nom)
    w = section_du_widget(config, nom)
    page = pathlib.Path(widgets_ui) / "dist" / f"{w.get('entree', nom)}.html"
    if not page.exists():
        raise GristErreur(f"{page} introuvable : construire d'abord le widget (`cd widgets_ui && npm ci && node build.mjs`).")
    html, js = separer_html_et_js(page.read_text(encoding="utf-8"))
    attendu = {"_html": html, "_js": chargeur_gzip(js)}
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

    corps = corps_patch(w["section_id"], options, vue, attendu).encode("utf-8")
    if len(corps) > LIMITE_API_OCTETS:
        raise GristErreur(
            f"413 : le bundle « {nom} » fait {len(corps) // 1024} Ko une fois compressé et échappé, "
            f"au-delà de la limite de l'API Grist (~{LIMITE_API_OCTETS // 1024} Ko). "
            "Réduire le bundle : retirer les dépendances inutiles, importer par composant, "
            "ne pas embarquer polices ni images.")
    session = session or ouvrir_session(client)
    url = f"{client.base_url}/docs/{client.doc_id}/tables/_grist_Views_section/records"
    _verifie(session.patch(url, data=corps, timeout=90))
    relu = next(r for r in _verifie(session.get(url, timeout=60)).json()["records"]
                if r["id"] == w["section_id"])
    stocke = json.loads(json.loads(relu["fields"]["options"])["customView"])["widgetOptions"]
    if stocke.get("_html") != html or stocke.get("_js") != attendu["_js"]:
        raise GristErreur("Écriture non conforme au fichier source : la section ne contient pas ce qui a été envoyé.")
    print(f"déposé : {', '.join(ecarts)} ({len(corps) // 1024} Ko envoyés) — recharger la page Grist")
    return 0
