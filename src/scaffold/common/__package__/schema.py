"""Schéma de {{app}} : données pures lues par `python -m grist_kit apply-schema`."""

STATUTS = ["à faire", "en cours", "terminé"]

TABLES = [
    {"id": "EXEMPLES", "label": "Exemples", "columns": [
        {"id": "titre", "type": "Text", "label": "Titre"},
        {"id": "statut", "type": "Choice", "label": "Statut", "choices": STATUTS},
        {"id": "titre_cle", "type": "Text", "label": "Titre normalisé",
         "formula": '($titre or "").strip().lower()'},
    ]},
]


def colonnes_auto_referentes():
    """Colonnes `Ref:` vers leur propre table (créées en seconde passe). Aucune ici."""
    return []
