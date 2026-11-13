from grist_kit import apply_schema
from grist_kit.testing.faux_grist import ClientFactice

from {{package}} import schema


def test_schema_dry_run_ne_leve_rien():
    apply_schema.appliquer(ClientFactice(), schema, dry_run=True)


def test_chaque_table_a_des_colonnes():
    assert schema.TABLES and all(t["columns"] for t in schema.TABLES)
