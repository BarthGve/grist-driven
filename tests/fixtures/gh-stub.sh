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


if "issue list" in ligne:
    etat["list_calls"] = etat.get("list_calls", 0) + 1
    champs = ("title", "number", "id", "projectItems")
    fin(0, json.dumps([{k: i.get(k, []) for k in champs} for i in etat.get("issues", [])]))
elif "project item-edit" in ligne:
    cible, option = opt("--id"), opt("--single-select-option-id")
    etat.setdefault("edits", []).append({"id": cible, "option": option})
    noms = {v: k for k, v in etat.get("status_option_ids", {}).items()}
    for issue in etat.get("issues", []):
        for item in issue.get("projectItems", []):
            if item["id"] == cible and option in noms:
                item["status"] = {"optionId": option, "name": noms[option]}
    fin(0, "{}")
elif "issue create" in ligne:
    n = numero_suivant()
    corps = open(opt("-F", "--body-file")).read() if opt("-F", "--body-file") else ""
    etat.setdefault("issues", []).append({
        "title": opt("-t", "--title") or "", "number": n, "id": f"I_{n}", "body": corps, "labels": [],
        "projectItems": [{"id": f"PVTI_{n}", "status": {"optionId": "opt1", "name": "backlog"}}],
    })
    fin(0, f"https://github.com/{opt('-R') or 'acme/app'}/issues/{n}")
elif "project item-add" in ligne:
    etat["item_add_calls"] = etat.get("item_add_calls", 0) + 1
    restant = etat.get("item_add_fail_remaining", 0)
    if restant > 0:
        etat["item_add_fail_remaining"] = restant - 1
        fin(1)
    fin(0, "{}")
elif "api graphql" in ligne:
    fin(1 if etat.get("subissue_fail") else 0, "{}")
elif "issue edit" in ligne:
    num = next((a for a in args if a.isdigit()), None)
    issue = next((i for i in etat.get("issues", []) if str(i["number"]) == num), None)
    if issue is None:
        fin(1)
    if opt("--body-file"):
        issue["body"] = open(opt("--body-file")).read()
    if opt("--title"):
        issue["title"] = opt("--title")
    if opt("--add-label") and opt("--add-label") not in issue["labels"]:
        issue["labels"].append(opt("--add-label"))
    fin(0, "{}")
elif "project create" in ligne:
    fin(0, json.dumps({"id": "PVT_stub", "number": 7}))
elif "project field-create" in ligne:
    noms = (opt("--single-select-options") or "").split(",")
    fin(0, json.dumps({"id": "FIELD_stub", "options": [{"name": n, "id": f"opt-{i}"} for i, n in enumerate(noms)]}))
elif "project field-list" in ligne or "project link" in ligne:
    fin(0, json.dumps({"fields": []}))
elif "label create" in ligne or "repo create" in ligne or ligne.startswith("api -X"):
    fin(0, "{}")
elif "api user" in ligne:
    fin(0, "acme")
elif "auth token" in ligne or "auth setup-git" in ligne:
    fin(0, "jeton-factice")
else:
    sys.stderr.write(f"gh-stub : appel non géré : {ligne}\n")
    fin(98)
PY
)
exec python3 -c "$PROG" "$@"
