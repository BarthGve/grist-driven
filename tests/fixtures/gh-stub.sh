#!/bin/sh
# Faux `gh` pour les tests : aucun réseau. L'état (tickets, appels, pannes simulées)
# vit dans le fichier JSON désigné par GRIST_GH_STUB_STATE.
[ -f "${GRIST_GH_STUB_STATE:-}" ] || { echo "gh-stub : GRIST_GH_STUB_STATE absent" >&2; exit 99; }
# Le script Python passe par -c : l'entrée standard reste libre pour `--input -`.
PROG=$(cat <<'PY'
import json, os, sys

chemin = os.environ["GRIST_GH_STUB_STATE"]
etat = json.load(open(chemin))
args = sys.argv[1:]
ligne = " ".join(args)
etat.setdefault("appels", []).append(args)


def opt(*noms):
    for n in noms:
        if n in args and args.index(n) + 1 < len(args):
            return args[args.index(n) + 1]
    return None


def fin(code=0, sortie=""):
    json.dump(etat, open(chemin, "w"), indent=2)
    if sortie:
        print(sortie)
    sys.exit(code)


def numero_suivant():
    return max([i["number"] for i in etat.get("issues", [])] + [0]) + 1


def champs_f():
    """Paires -f/-F clé=valeur ; « @fichier » est lu comme gh le fait."""
    out = {}
    for i, a in enumerate(args):
        if a in ("-f", "-F") and i + 1 < len(args) and "=" in args[i + 1]:
            k, v = args[i + 1].split("=", 1)
            out[k] = open(v[1:]).read() if v.startswith("@") else v
    return out


def corps_stdin():
    return json.load(sys.stdin) if "--input" in args else {}


def issue_par_numero(n):
    return next((i for i in etat.get("issues", []) if str(i["number"]) == str(n)), None)


route = next((a for a in args[1:] if "/" in a and not a.startswith("-")), "") if args[:1] == ["api"] else ""
route = route.split("?")[0]
methode = opt("-X") or "GET"

if args[:2] == ["api", "user"]:
    fin(0, "acme")
elif args[:1] == ["api"] and len(args) >= 2 and args[1].startswith("users/") and "/" not in args[1][6:]:
    fin(0, json.dumps({"login": args[1][6:], "type": "User"}))
elif route.endswith("/projectsV2/1/fields") or route.endswith("/projectsV2/7/fields"):
    fin(0, json.dumps([
        {"id": 1, "name": "Title", "data_type": "title"},
        {"id": 2, "name": "Status", "data_type": "single_select", "node_id": "FIELD_status0",
         "options": [{"id": "d1", "name": {"raw": "Todo"}}, {"id": "d2", "name": {"raw": "In Progress"}},
                     {"id": "d3", "name": {"raw": "Done"}}]}]))
elif route.endswith("/issues") and methode == "GET":
    etat["list_calls"] = etat.get("list_calls", 0) + 1
    fin(0, json.dumps([{"title": i.get("title", ""), "number": i["number"], "id": i["id"]}
                       for i in etat.get("issues", [])]
                      + etat.get("pulls_dans_issues", [])))
elif "/items" in route and methode == "GET":
    noms = {v: k for k, v in etat.get("status_option_ids", {}).items()}
    liste = []
    for i in etat.get("issues", []):
        for item in i.get("projectItems", []):
            st = item.get("status") or {}
            valeur = {"id": st.get("optionId"), "name": {"raw": st.get("name", "")}} if st.get("name") else None
            liste.append({"id": item["id"], "content_type": "Issue", "content": {"number": i["number"], "id": i["id"]},
                          "fields": [{"id": 2, "name": "Status", "data_type": "single_select", "value": valeur}]})
    fin(0, json.dumps(liste))
elif "/items/" in route and methode == "PATCH":
    cible = route.rsplit("/", 1)[1]
    option = corps_stdin()["fields"][0]["value"]
    etat.setdefault("edits", []).append({"id": cible, "option": option})
    noms = {v: k for k, v in etat.get("status_option_ids", {}).items()}
    for issue in etat.get("issues", []):
        for item in issue.get("projectItems", []):
            if item["id"] == cible and option in noms:
                item["status"] = {"optionId": option, "name": noms[option]}
    fin(0, "{}")
elif route.endswith("/items") and methode == "POST":
    corps = corps_stdin()
    etat["item_add_calls"] = etat.get("item_add_calls", 0) + 1
    restant = etat.get("item_add_fail_remaining", 0)
    if restant > 0:
        etat["item_add_fail_remaining"] = restant - 1
        fin(1)
    cible = issue_par_numero(corps.get("number"))
    if cible is not None and not cible.get("projectItems"):
        cible["projectItems"] = [{"id": f"PVTI_{cible['number']}", "status": {"optionId": "opt1", "name": "backlog"}}]
    fin(0, "{}")
elif route.endswith("/issues") and methode == "POST":
    n = numero_suivant()
    c = champs_f()
    etat.setdefault("issues", []).append({
        "title": c.get("title", ""), "number": n, "id": f"I_{n}", "body": c.get("body", ""), "labels": [],
        # le faux projet « auto-ajoute » : sans cela l'issue ne serait pas sur le tableau avant item-add
        "projectItems": [],
    })
    fin(0, json.dumps({"html_url": f"https://github.com/acme/app/issues/{n}", "number": n}))
elif "/issues/" in route and route.endswith("/sub_issues") and methode == "POST":
    fin(1 if etat.get("subissue_fail") else 0, "{}")
elif "/issues/" in route and route.endswith("/labels") and methode == "POST":
    issue = issue_par_numero(route.split("/issues/")[1].split("/")[0])
    etiquette = champs_f().get("labels[]")
    if issue is None:
        fin(1)
    if etiquette and etiquette not in issue["labels"]:
        issue["labels"].append(etiquette)
    fin(0, "{}")
elif "/issues/" in route and methode == "PATCH":
    issue = issue_par_numero(route.rsplit("/", 1)[1])
    if issue is None:
        fin(1)
    c = champs_f()
    if "body" in c:
        issue["body"] = c["body"]
    if "title" in c:
        issue["title"] = c["title"]
    fin(0, "{}")
elif route.endswith("/labels") and methode == "POST":
    fin(0, "{}")
elif "api graphql" in ligne and "updateProjectV2Field" in ligne:
    import re
    noms = re.findall(r'name:"([^"]+)"', ligne)
    reponse = {"data": {"updateProjectV2Field": {"projectV2Field": {
        "id": "FIELD_status0", "options": [{"id": f"opt-{i}", "name": n} for i, n in enumerate(noms)]}}}}
    fin(0, json.dumps(reponse))
elif "project create" in ligne:
    fin(0, json.dumps({"id": "PVT_stub", "number": 7}))
elif "project link" in ligne:
    fin(0, "{}")
elif ligne.startswith("api -X"):
    fin(0, "{}")
elif "auth token" in ligne or "auth setup-git" in ligne:
    fin(0, "jeton-factice")
else:
    sys.stderr.write(f"gh-stub : appel non géré : {ligne}\n")
    fin(98)
PY
)
exec python3 -c "$PROG" "$@"
