import json

from grist_kit import versions
from grist_kit.testing.faux_grist import ClientFactice

JOURNAL = [
    {"version": "1.1.0", "date": "2026-02-01",
     "notes": [{"texte": "Ajoute un filtre", "widgets": ["liste"]},
               {"texte": "Corrige l'export", "widgets": ["liste", "fiche"]}]},
    {"version": "1.0.0", "date": "2026-01-01", "notes": [{"texte": "Première version", "widgets": ["fiche"]}]},
]
NOMS = {"liste": "Liste", "fiche": "Fiche"}


def page(journal=JOURNAL):
    return f"<script>\n/* VERSIONS BEGIN */\n{json.dumps(journal)}\n/* VERSIONS END */\n</script>"


def test_journal_lu_entre_marqueurs():
    assert versions.lire_journal(page()) == JOURNAL


def test_marqueurs_absents_message_clair():
    try:
        versions.lire_journal("<html></html>")
    except ValueError as e:
        assert "VERSIONS BEGIN" in str(e)
    else:
        raise AssertionError("ValueError attendue")


def test_lignes_changelog_une_note_par_ligne():
    lignes = versions.lignes_changelog(JOURNAL)
    assert lignes[0] == {"version": "1.1.0", "date": "2026-02-01", "notes": "Ajoute un filtre\nCorrige l'export"}


def test_synchroniser_cree_puis_est_idempotent():
    client = ClientFactice()
    lignes = versions.lignes_changelog(JOURNAL)
    assert versions.synchroniser(client, lignes) == ["1.1.0", "1.0.0"]
    assert len(client.lignes("CHANGELOG")) == 2
    client.appels.clear()
    assert versions.synchroniser(client, lignes) == []
    assert client.ecritures() == []


def test_synchroniser_met_a_jour_une_note_modifiee():
    client = ClientFactice()
    versions.synchroniser(client, versions.lignes_changelog(JOURNAL))
    modifie = [dict(JOURNAL[0], notes=[{"texte": "Autre texte", "widgets": []}]), JOURNAL[1]]
    assert versions.synchroniser(client, versions.lignes_changelog(modifie)) == ["1.1.0"]
    assert len(client.lignes("CHANGELOG")) == 2
    assert {r["fields"]["notes"] for r in client.lignes("CHANGELOG")} >= {"Autre texte"}


def test_jamais_de_suppression():
    client = ClientFactice()
    versions.synchroniser(client, versions.lignes_changelog(JOURNAL))
    versions.synchroniser(client, versions.lignes_changelog(JOURNAL[:1]))
    assert len(client.lignes("CHANGELOG")) == 2
    assert not any(a[0] == "DELETE" or "RemoveRecord" in str(a[2]) for a in client.appels)


def test_dry_run_n_ecrit_rien():
    client = ClientFactice()
    assert versions.synchroniser(client, versions.lignes_changelog(JOURNAL), dry_run=True) == ["1.1.0", "1.0.0"]
    assert client.ecritures() == []


def test_changelog_md_stable():
    assert versions.changelog_md(JOURNAL, NOMS) == versions.changelog_md(JOURNAL, NOMS)
    md = versions.changelog_md(JOURNAL, NOMS)
    assert "## [1.1.0] - 2026-02-01" in md
    assert "- Corrige l'export _(Liste, Fiche)_" in md
    assert md.index("1.1.0") < md.index("1.0.0")


def test_changelog_md_sans_noms_utilise_les_identifiants():
    assert "_(liste)_" in versions.changelog_md(JOURNAL)


def test_notes_filtrees_par_widget():
    notes = versions.notes_du_widget(JOURNAL, "fiche")
    assert [n["texte"] for n in notes] == ["Corrige l'export", "Première version"]
    assert versions.notes_du_widget(JOURNAL, "inconnu") == []


def test_ecrire_changelog_check(tmp_path):
    chemin = tmp_path / "CHANGELOG.md"
    assert versions.ecrire_changelog(chemin, JOURNAL, NOMS, check=True) is False
    assert not chemin.exists()
    assert versions.ecrire_changelog(chemin, JOURNAL, NOMS) is True
    assert versions.ecrire_changelog(chemin, JOURNAL, NOMS, check=True) is True
