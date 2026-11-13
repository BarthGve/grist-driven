"""Règles d'accès de {{app}} : données pures lues par `python -m grist_kit apply-acl`.

Chaque règle porte une étiquette `[{{package}}:<ressource>#<n>]` dans son mémo (c'est ce qui la rend
idempotente). Les propriétaires font tout ; les autres lisent.
"""

RESOURCES = [
    {"key": "default", "tableId": "*", "colIds": "*"},
    {"key": "exemples", "tableId": "EXEMPLES", "colIds": "*"},
]
RULES = [
    {"resource_key": "exemples", "rulePos": 1, "permissionsText": "+CRUD", "aclFormula": 'user.Access == "owners"',
     "memo": "[{{package}}:exemples#1] Les propriétaires font tout."},
    {"resource_key": "exemples", "rulePos": 2, "permissionsText": "+R", "aclFormula": "",
     "memo": "[{{package}}:exemples#2] Lecture pour tous."},
]
USER_ATTRIBUTES = []
