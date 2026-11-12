"""Schéma fictif pour tester les formules en mémoire (aucune donnée réelle)."""

TABLES = [
    {"id": "UNITES", "label": "Unités", "columns": [
        {"id": "code", "type": "Text", "label": "Code"},
        {"id": "parent", "type": "Ref:UNITES", "label": "Rattachée à"},
        {"id": "nb_sous", "type": "Int", "label": "Sous-unités", "formula": "len(UNITES.lookupRecords(parent=$id))"},
        {"id": "code_cle", "type": "Text", "label": "Clé", "formula": "$code.strip().upper()"},
    ]},
    {"id": "PERSONNES", "label": "Personnes", "columns": [
        {"id": "email_cle", "type": "Text", "label": "Courriel"},
        {"id": "unite", "type": "Ref:UNITES", "label": "Unité"},
        {"id": "admin", "type": "Bool", "label": "Admin"},
        {"id": "type_unite", "type": "Text", "label": "Code de l'unité", "formula": "$unite.code"},
    ]},
    {"id": "DOCS", "label": "Documents", "columns": [
        {"id": "titre", "type": "Text", "label": "Titre"},
        {"id": "secret", "type": "Text", "label": "Secret"},
        {"id": "auteur", "type": "Ref:PERSONNES", "label": "Auteur"},
        {"id": "annee_courante", "type": "Int", "label": "Année", "formula": "NOW().year"},
        {"id": "note", "type": "Numeric", "label": "Note"},
        {"id": "etat", "type": "Choice", "label": "État"},
        {"id": "echeance", "type": "Date", "label": "Échéance"},
        {"id": "horodatage", "type": "DateTime:Europe/Paris", "label": "Horodatage"},
        {"id": "figee", "type": "Text", "label": "Figée", "formula": "NOW()", "declenchee": True},
    ]},
]
