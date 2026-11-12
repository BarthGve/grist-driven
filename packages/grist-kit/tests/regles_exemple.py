"""Règles ACL fictives : contrat de `regles_module` d'apply_acl (RESOURCES, RULES, USER_ATTRIBUTES)."""

RESOURCES = [
    {"key": "default", "tableId": "*", "colIds": "*"},
    {"key": "docs", "tableId": "DOCS", "colIds": "*"},
    {"key": "docs_secret", "tableId": "DOCS", "colIds": "secret"},
]
RULES = [
    {"resource_key": "docs", "rulePos": 1, "permissionsText": "+CRUD", "aclFormula": "user.Personne.admin",
     "memo": "[demo:docs#1] Les administrateurs font tout."},
    {"resource_key": "docs", "rulePos": 2, "permissionsText": "+RU", "aclFormula": "rec.auteur.id == user.Personne.id",
     "memo": "[demo:docs#2] L'auteur lit et modifie."},
    {"resource_key": "docs", "rulePos": 3, "permissionsText": "+R", "aclFormula": "",
     "memo": "[demo:docs#3] Lecture pour tous."},
    {"resource_key": "docs_secret", "rulePos": 1, "permissionsText": "-R", "aclFormula": "not user.Personne.admin",
     "memo": "[demo:docs_secret#1] Colonne secrète : administrateurs seuls."},
]
USER_ATTRIBUTES = [
    {"resource_key": "default", "name": "Personne", "tableId": "PERSONNES", "lookupColId": "email_cle",
     "charId": "Email"},
]
