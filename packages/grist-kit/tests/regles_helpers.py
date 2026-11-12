"""Règles d'accès fictives pour tester le simulateur d'ACL."""

RESOURCES = [
    {"key": "default", "tableId": "*", "colIds": "*"},
    {"key": "docs", "tableId": "DOCS", "colIds": "*"},
    {"key": "docs_secret", "tableId": "DOCS", "colIds": "secret"},
]
# Volontairement dans le désordre : l'ordre d'évaluation vient de `rulePos`.
RULES = [
    {"resource_key": "docs", "rulePos": 3, "permissionsText": "+R", "aclFormula": ""},
    {"resource_key": "docs", "rulePos": 1, "permissionsText": "+CRUD", "aclFormula": "user.Personne.admin"},
    {"resource_key": "docs", "rulePos": 2, "permissionsText": "+RU", "aclFormula": "rec.auteur.id == user.Personne.id"},
    {"resource_key": "docs_secret", "rulePos": 1, "permissionsText": "+R", "aclFormula": "user.Personne.admin"},
    {"resource_key": "docs_secret", "rulePos": 2, "permissionsText": "-R", "aclFormula": ""},
]
USER_ATTRIBUTES = [
    {"resource_key": "default", "name": "Personne", "tableId": "PERSONNES", "lookupColId": "email_cle", "charId": "Email"},
]
