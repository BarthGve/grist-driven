# Questionnaire d'installation (spec §6.2). Une réponse vient dans l'ordre :
# drapeau, saisie sur le terminal, valeur par défaut (--yes). Sauf le design
# system : jamais de défaut. Les prompts vont sur stderr, les saisies sont lues
# sur le descripteur 3 (le terminal, même en `curl … | bash`).
# Code de sortie 2 : réponse manquante ou invalide.

TTY_PATH=${GRIST_DRIVEN_TTY:-/dev/tty}

ouvrir_terminal() {
  if [ -r "$TTY_PATH" ] && ( : <"$TTY_PATH" ) 2>/dev/null; then exec 3<"$TTY_PATH"; return 0; fi
  return 1
}

_lire() { IFS= read -r REPONSE <&3 || die 2 "fin de saisie sur le terminal"; }

# demander VAR "question" "défaut" : ne fait rien si VAR est déjà renseigné.
demander() {
  [ -z "${!1}" ] || return 0
  if [ "$YES" = true ]; then printf -v "$1" %s "$3"; return 0; fi
  printf '%s [%s] : ' "$2" "$3" >&2; _lire
  printf -v "$1" %s "${REPONSE:-$3}"
}

# demander_bool VAR "question" true|false
demander_bool() {
  [ -z "${!1}" ] || return 0
  if [ "$YES" = true ]; then printf -v "$1" %s "$3"; return 0; fi
  local d=O/n; [ "$3" = true ] || d=o/N
  while :; do
    printf '%s [%s] : ' "$2" "$d" >&2; _lire
    case $(printf %s "$REPONSE" | tr 'A-Z' 'a-z') in
      o|oui|y|yes) printf -v "$1" %s true; return 0;;
      n|non|no) printf -v "$1" %s false; return 0;;
      "") printf -v "$1" %s "$3"; return 0;;
    esac
  done
}

_dans() { local v=$1; shift; local x; for x in "$@"; do [ "$x" = "$v" ] && return 0; done; return 1; }

# Identifiants de documents : lettres, chiffres, - et _ ; preprod, production et recette distincts.
_verifier_documents() {
  local v n
  for n in DOC_ID DOC_ID_PREPROD DOC_ID_PRODUCTION; do
    v=${!n}
    case $v in *[!A-Za-z0-9_-]*) die 2 "identifiant de document invalide pour $n (lettres, chiffres, - et _ seulement)";; esac
  done
  if [ -n "$DOC_ID_PREPROD" ] && [ "$DOC_ID_PREPROD" = "$DOC_ID_PRODUCTION" ]; then
    die 2 "la preprod et la production doivent avoir chacune leur propre document"
  fi
  if [ -n "$DOC_ID" ] && { [ "$DOC_ID" = "$DOC_ID_PREPROD" ] || [ "$DOC_ID" = "$DOC_ID_PRODUCTION" ]; }; then
    die 2 "le document de recette (--doc-id) doit différer de la preprod et de la production"
  fi
}

poser_questions() {
  if [ "$YES" != true ]; then
    ouvrir_terminal || die 2 "pas de terminal pour poser les questions : relancer avec --yes et --design-system dsfr|ui-kit"
  fi
  [ "$YES" = true ] && [ -z "$DESIGN_SYSTEM" ] && die 2 "design system obligatoire : --design-system dsfr|ui-kit"

  demander NAME "1. Nom de l'application" "$(basename "$PWD")"
  demander ORG "2. Organisation Grist" docs
  demander API_HOST "   Adresse de l'API Grist" "https://grist.numerique.gouv.fr/o/$ORG/api"
  if [ -z "$DESIGN_SYSTEM" ]; then   # pas de défaut : on redemande
    while :; do
      printf '3. Design system des widgets (dsfr / ui-kit) : ' >&2; _lire
      _dans "$REPONSE" dsfr ui-kit && { DESIGN_SYSTEM=$REPONSE; break; }
    done
  fi
  demander MCP "4. MCP Grist (existing / install / coder / none)" install
  demander MCP_SCOPE "   Portée du MCP (project / user)" project
  if [ -z "${GRIST_API_KEY:-}" ] && [ "$YES" != true ]; then
    printf '5. Clé d API Grist (saisie masquée, vide = plus tard) : ' >&2
    IFS= read -rs GRIST_API_KEY <&3 || GRIST_API_KEY=""; echo >&2
  fi
  demander DOC_ID_PREPROD "6. Identifiant du document Grist de preprod, déployé depuis next (vide = plus tard)" ""
  demander DOC_ID_PRODUCTION "7. Identifiant du document Grist de production, déployé depuis main (vide = plus tard)" ""
  demander_bool GIT_FLOW "8. Flux git main/next et tableau GitHub" true
  demander_bool HOOKS "9. Hooks git" true
  demander_bool CI "   Workflow CI" true

  _dans "$DESIGN_SYSTEM" dsfr ui-kit || die 2 "design system invalide « $DESIGN_SYSTEM » : dsfr ou ui-kit"
  _dans "$MCP" existing install coder none || die 2 "--mcp invalide « $MCP » : existing, install, coder ou none"
  _dans "$MCP_SCOPE" project user || die 2 "--mcp-scope invalide « $MCP_SCOPE » : project ou user"
  [ -n "$NAME" ] || die 2 "nom de l'application vide"
  _verifier_documents
}
