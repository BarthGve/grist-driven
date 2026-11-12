"""Applique le cloisonnement par ACL d'un document Grist, de façon idempotente.

Chaque règle est identifiée par l'étiquette `[<app>:<ressource>#<n>]` placée en tête de son `memo` :
formule, permission ou texte modifié -> mise à jour en place (jamais de doublon) ; règle retirée du code ->
signalée, supprimée seulement avec `prune`.

`regles_module` expose `RESOURCES`, `RULES` et `USER_ATTRIBUTES`.

Piège d'API : POST /apply attend le tableau d'actions à la RACINE du corps.
"""

import json
import logging
import re

logger = logging.getLogger(__name__)

# Préfixe d'application libre ; chaque document n'en porte qu'un.
ETIQUETTE = re.compile(r"^\[[a-z0-9_]+:([a-z_]+)#(\d+)\]")


def _etiquette(memo):
    m = ETIQUETTE.match(memo or "")
    return (m.group(1), int(m.group(2))) if m else None


def valider(souhaitees):
    """Refuse, avant tout appel réseau, une règle sans étiquette, deux règles de même étiquette, ou une
    étiquette dont la partie ressource diffère de `resource_key`."""
    vues = set()
    for s in souhaitees:
        cle = _etiquette(s.get("memo"))
        if cle is None:
            raise ValueError(
                f"Règle sans étiquette `[<app>:<ressource>#<n>]` en tête du memo : {s.get('memo')!r}")
        if "resource_key" in s and cle[0] != s["resource_key"]:
            raise ValueError(
                f"Étiquette incohérente avec resource_key : [{cle[0]}#{cle[1]}] pour la ressource "
                f"{s['resource_key']!r} ({s['memo']!r})")
        if cle in vues:
            raise ValueError(f"Étiquette en double : [{cle[0]}#{cle[1]}] ({s['memo']!r})")
        vues.add(cle)


def planifier(souhaitees, existantes, id_par_cle=None):
    """Compare règles souhaitées et existantes ; ne fait aucun appel réseau.

    `souhaitees` : règles de `regles_module.RULES`. `existantes` : dicts à plat
    {id, resource, aclFormula, permissionsText, memo, rulePos}. `id_par_cle` (optionnel) : id de ressource par
    `resource_key` ; si fourni, une règle posée sur une autre ressource est replacée (clé absente ou None : ignorée).
    """
    plan = {"ajouts": [], "mises_a_jour": [], "obsoletes": []}
    par_etiquette = {}
    for r in existantes:
        cle = _etiquette(r.get("memo"))
        if cle:
            par_etiquette[cle] = r

    voulues = set()
    for s in souhaitees:
        cle = _etiquette(s["memo"])
        voulues.add(cle)
        courante = par_etiquette.get(cle)
        if courante is None:
            plan["ajouts"].append(s)
            continue
        # Le memo aussi : une règle insérée décale les suivantes, leur texte doit suivre.
        for champ in ("aclFormula", "permissionsText", "memo"):
            if courante.get(champ, "") != s[champ]:
                plan["mises_a_jour"].append((courante["id"], {champ: s[champ]}))
        voulue = (id_par_cle or {}).get(s.get("resource_key"))
        if voulue is not None and courante.get("resource") != voulue:
            plan["mises_a_jour"].append((courante["id"], {"resource": voulue}))

    # Ordre relatif au sein de chaque ressource : Grist fractionne les rulePos, seul l'ordre compte ;
    # on le force s'il ne suit pas l'ordre souhaité.
    groupes = {}
    for s in souhaitees:
        cle = _etiquette(s["memo"])
        if cle in par_etiquette:
            groupes.setdefault(cle[0], []).append((s["rulePos"], par_etiquette[cle]))
    for regles in groupes.values():
        attendu = [r["id"] for _, r in sorted(regles, key=lambda t: t[0])]
        reel = [r["id"] for r in sorted((r for _, r in regles), key=lambda r: r["rulePos"])]
        if attendu != reel:
            for pos, r in regles:
                plan["mises_a_jour"].append((r["id"], {"rulePos": pos}))

    plan["obsoletes"] = [r["id"] for cle, r in par_etiquette.items() if cle not in voulues]
    return plan


def ressource_a_renommer(cle, table_id, existantes, ressources):
    """Id de la ressource qui porte déjà les règles de `cle` sur `table_id`, sinon None.

    Quand les colonnes d'une ressource changent, on met à jour son colIds : en créer une autre laisserait
    les règles sur l'ancienne, aux colonnes périmées, et Grist refuserait tout nouveau jeu de règles.
    """
    for r in existantes:
        etiquette = _etiquette(r.get("memo"))
        res = ressources.get(r.get("resource"))
        if etiquette and etiquette[0] == cle and res and res.get("tableId") == table_id:
            return r["resource"]
    return None


def _lire(client, table):
    reponse = client._make_request("GET", f"/tables/{table}/records")
    return [{"id": r["id"], **r["fields"]} for r in reponse.get("records", [])]


def appliquer(client, regles_module, dry_run=False, prune=False):
    """Installe ressources, attributs utilisateur et règles. Retourne le plan.

    `regles_module` est obligatoire. Les règles sont validées avant tout appel réseau.
    """
    valider(regles_module.RULES)
    lues = _lire(client, "_grist_ACLResources")
    ressources = {(r["tableId"], r["colIds"]): r["id"] for r in lues}
    par_id = {r["id"]: r for r in lues}
    regles_lues = _lire(client, "_grist_ACLRules")
    id_par_cle = {}
    for res in regles_module.RESOURCES:
        cle = (res["tableId"], res["colIds"])
        ancienne = None if cle in ressources else ressource_a_renommer(
            res["key"], res["tableId"], regles_lues, par_id)
        if ancienne is not None and not dry_run:
            client._make_request("POST", "/apply", [[
                "UpdateRecord", "_grist_ACLResources", ancienne, {"colIds": res["colIds"]}]])
            ressources[cle] = ancienne
        elif cle not in ressources and not dry_run:
            reponse = client._make_request("POST", "/apply", [[
                "AddRecord", "_grist_ACLResources", -1,
                {"tableId": res["tableId"], "colIds": res["colIds"]}]])
            ressources[cle] = reponse["retValues"][0]
        id_par_cle[res["key"]] = ressources.get(cle)

    existantes = _lire(client, "_grist_ACLRules")
    maj_attributs = []
    for attr in regles_module.USER_ATTRIBUTES:
        payload = {k: attr[k] for k in ("name", "tableId", "lookupColId", "charId")}
        courante = next((r for r in existantes if r.get("userAttributes")
                         and json.loads(r["userAttributes"]).get("name") == attr["name"]), None)
        if courante is None:
            if not dry_run:
                client._make_request("POST", "/apply", [[
                    "AddRecord", "_grist_ACLRules", -1,
                    {"resource": id_par_cle[attr["resource_key"]],
                     "userAttributes": json.dumps(payload), "rulePos": 0}]])
            continue
        champs = {}
        if json.loads(courante["userAttributes"]) != payload:
            champs["userAttributes"] = json.dumps(payload)
        voulue = id_par_cle.get(attr["resource_key"])
        if voulue is not None and courante.get("resource") != voulue:
            champs["resource"] = voulue
        if champs:
            maj_attributs.append((courante["id"], champs))

    plan = planifier(regles_module.RULES, existantes, id_par_cle)
    plan["mises_a_jour"] += maj_attributs
    if dry_run:
        return plan
    actions = []
    # Les règles obsolètes partent d'abord : une mise à jour peut faire remonter le repli devant l'une
    # d'elles, état que Grist refuse.
    if prune:
        actions += [["RemoveRecord", "_grist_ACLRules", id_] for id_ in plan["obsoletes"]]
    for s in plan["ajouts"]:
        actions.append(["AddRecord", "_grist_ACLRules", -1, {
            "resource": id_par_cle[s["resource_key"]],
            "aclFormula": s["aclFormula"], "permissionsText": s["permissionsText"],
            "rulePos": s["rulePos"], "memo": s["memo"]}])
    for id_, champs in plan["mises_a_jour"]:
        actions.append(["UpdateRecord", "_grist_ACLRules", id_, champs])
    if actions:
        client._make_request("POST", "/apply", actions)
    return plan
