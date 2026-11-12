#!/usr/bin/env bash
# grist-config : lit .grist/config.json et exporte la configuration du tableau.
# À charger avec `source`. Clés exigées : owner, repo, project_id, status_field_id et
# status_option_ids (un identifiant pour chacun des six statuts du tableau).
# Variables posées : GRIST_OWNER, GRIST_REPO, GRIST_PROJECT_ID, GRIST_PROJECT_NUMBER,
# GRIST_STATUS_FIELD_ID, GRIST_STATUS_JSON.

GRIST_STATUTS="backlog|ready|in progress|review|test|shipped"

grist_config_fichier() {
  printf '%s/.grist/config.json' "${GRIST_RACINE:-${1:-.}}"
}

grist_config_charger() {
  local fichier export_sh
  fichier="$(grist_config_fichier "${1:-}")"
  [ -f "$fichier" ] || {
    echo "grist-config : $fichier introuvable (lancer /grist-init)" >&2
    return 1
  }
  export_sh="$(python3 - "$fichier" "$GRIST_STATUTS" <<'PY'
import json, shlex, sys

fichier, statuts = sys.argv[1], sys.argv[2].split("|")
try:
    c = json.load(open(fichier))
except ValueError as e:
    sys.exit(f"grist-config : {fichier} n'est pas un JSON valide ({e})")
options = c.get("status_option_ids")
manque = [k for k in ("owner", "repo", "project_id", "status_field_id") if not c.get(k)]
if not isinstance(options, dict):
    manque.append("status_option_ids")
else:
    manque += [f"status_option_ids.{s}" for s in statuts if not str(options.get(s, "")).strip()]
if manque:
    sys.exit("grist-config : clés absentes ou vides : " + ", ".join(manque))
valeurs = {
    "GRIST_OWNER": c["owner"], "GRIST_REPO": c["repo"], "GRIST_PROJECT_ID": c["project_id"],
    "GRIST_PROJECT_NUMBER": c.get("project_number", ""), "GRIST_STATUS_FIELD_ID": c["status_field_id"],
    "GRIST_STATUS_JSON": json.dumps(options),
}
for nom, v in valeurs.items():
    print(f"export {nom}={shlex.quote(str(v))}")
PY
)" || return 1
  eval "$export_sh"
}

# Identifiant d'option du tableau pour un statut ("in progress" → opt…).
grist_config_option() {
  python3 -c '
import json, os, sys
options = json.loads(os.environ["GRIST_STATUS_JSON"])
if sys.argv[1] not in options:
    sys.exit("grist-config : statut inconnu " + repr(sys.argv[1]))
print(options[sys.argv[1]], end="")
' "$1"
}

grist_config_depot() {
  printf '%s/%s' "${GRIST_OWNER:?}" "${GRIST_REPO:?}"
}
