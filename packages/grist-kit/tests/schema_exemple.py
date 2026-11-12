"""Schéma fictif de 3 tables, dont une auto-référente : contrat de `schema_module` d'apply_schema."""

NIVEAUX = ["bas", "moyen", "haut"]

TABLES = [
    {"id": "CATEGORIES", "label": "Catégories", "columns": [
        {"id": "nom", "type": "Text", "label": "Nom"},
        {"id": "parent", "type": "Ref:CATEGORIES", "label": "Catégorie parente"},
    ]},
    {"id": "PROJETS", "label": "Projets", "columns": [
        {"id": "titre", "type": "Text", "label": "Titre"},
        {"id": "categorie", "type": "Ref:CATEGORIES", "label": "Catégorie"},
        {"id": "titre_cle", "type": "Text", "label": "Titre normalisé",
         "formula": '($titre or "").strip().lower()'},
    ]},
    {"id": "TACHES", "label": "Tâches", "columns": [
        {"id": "intitule", "type": "Text", "label": "Intitulé"},
        {"id": "projet", "type": "Ref:PROJETS", "label": "Projet"},
        {"id": "priorite", "type": "Choice", "label": "Priorité", "choices": NIVEAUX},
        {"id": "creee_le", "type": "DateTime:Europe/Paris", "label": "Créée le",
         "formula": "NOW()", "declenchee": True},
    ]},
]


def colonnes_auto_referentes():
    """Colonnes `Ref:` vers leur propre table : créées dans une seconde passe."""
    return [("CATEGORIES", "parent")]
