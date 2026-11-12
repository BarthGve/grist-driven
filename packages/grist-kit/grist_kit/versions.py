"""Journal des versions d'un widget : lecture, table CHANGELOG du document, CHANGELOG.md.

Le journal du code (bloc JSON entre `/* VERSIONS BEGIN */` et `/* VERSIONS END */`) est la source de vérité ;
la table CHANGELOG sert à la page d'historique des utilisateurs. Chaque entrée du journal :
`{version, date, notes: [{texte, widgets}]}`. Indépendant de tout projet : chemins et noms de widgets en paramètres.
"""

import json
from pathlib import Path

DEBUT, FIN = "/* VERSIONS BEGIN */", "/* VERSIONS END */"


def lire_journal(html_ou_js: str) -> list[dict]:
    """Liste des versions du bloc JSON entre les marqueurs."""
    try:
        debut = html_ou_js.index(DEBUT) + len(DEBUT)
        return json.loads(html_ou_js[debut:html_ou_js.index(FIN, debut)])
    except ValueError as e:
        raise ValueError(f"Journal introuvable ou invalide : marqueurs {DEBUT} / {FIN} attendus ({e})") from e


def lignes_changelog(journal: list[dict]) -> list[dict]:
    """Champs de la table CHANGELOG : une note par ligne de texte."""
    return [{"version": v["version"], "date": v["date"], "notes": "\n".join(n["texte"] for n in v["notes"])}
            for v in journal]


def synchroniser(client, lignes: list[dict], dry_run: bool = False) -> list[str]:
    """Crée ou met à jour les lignes de CHANGELOG ; renvoie les versions touchées. Ne supprime jamais."""
    existantes = {r["fields"]["version"]: r for r in client.fetch_table("CHANGELOG")}
    touchees = []
    for champs in lignes:
        actuel = existantes.get(champs["version"])
        if actuel and all(actuel["fields"].get(k) == v for k, v in champs.items()):
            continue
        touchees.append(champs["version"])
        if dry_run:
            continue
        if actuel:
            client.update_record("CHANGELOG", actuel["id"], champs)
        else:
            client.add_record("CHANGELOG", champs)
    return touchees


def changelog_md(journal: list[dict], noms_widgets: dict | None = None) -> str:
    """CHANGELOG.md rendu depuis le journal ; `noms_widgets` : identifiant -> libellé (identifiant par défaut)."""
    noms = noms_widgets or {}
    lignes = ["# Journal des versions", "",
              "Généré depuis le journal des versions du code : ne pas modifier à la main.", ""]
    for v in journal:
        lignes += [f"## [{v['version']}] - {v['date']}", ""]
        for n in v["notes"]:
            widgets = ", ".join(noms.get(w, w) for w in n["widgets"])
            lignes.append(f"- {n['texte']} _({widgets})_")
        lignes.append("")
    return "\n".join(lignes)


def ecrire_changelog(chemin: Path, journal: list[dict], noms_widgets: dict | None = None,
                     check: bool = False) -> bool:
    """Écrit (ou, avec `check`, compare seulement) le fichier. Vrai si le fichier est à jour."""
    chemin = Path(chemin)
    attendu = changelog_md(journal, noms_widgets)
    if chemin.exists() and chemin.read_text(encoding="utf-8") == attendu:
        return True
    if check:
        return False
    chemin.write_text(attendu, encoding="utf-8")
    return True


def notes_du_widget(journal: list[dict], widget: str) -> list[dict]:
    """Notes concernant un widget, de la plus récente à la plus ancienne."""
    return [n for v in journal for n in v["notes"] if widget in n["widgets"]]
