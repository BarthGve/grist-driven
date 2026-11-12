"""Skills : frontmatter, pièges obligatoires, absence de reste de driven."""
import re
from pathlib import Path

import pytest

SKILLS = Path(__file__).resolve().parents[2] / "src" / "skills"
SAVOIR = ["schema", "acl", "widget", "deploy", "recette", "mcp", "perf"]
METHODE = ["agentic-stories", "codebase-analysis", "quality-bar", "stories-review", "tdd"]
NOMS = [f"grist-{n}" for n in SAVOIR + METHODE]

# Motifs obligatoires par skill (regex, insensible à la casse).
PIEGES = {
    "grist-schema": [r"isFormula", r"colId", r"réutilisé", r"orphelin", r"PATCH"],
    "grist-acl": [r"rec\.", r"newRec", r"état d'avant", r"-R\b", r"\[<app>:<ressource>#<n>\]", r"refus"],
    "grist-widget": [r"deux endroits", r"dsfr", r"ui-kit", r"style=", r"innerHTML", r"alert\(\)", r"1 Mo", r"gzip"],
    "grist-deploy": [r"apply-schema", r"maj-formules", r"apply-acl", r"--dry-run", r"403", r"version"],
    "grist-recette": [r"aclAsUser_", r"profil"],
    "grist-mcp": [r"jamais la structure", r"lit"],
    "grist-perf": [r"avant et après", r"Intl", r"Map", r"lookupRecords", r"NOW", r"/apply", r"LIMITE_API_OCTETS", r"50 lignes", r"250 ms", r"react-query"],
    "grist-quality-bar": [r"Intl", r"Map", r"lookupRecords", r"avant et après", r"/apply", r"LIMITE_API_OCTETS", r"Ship allowed"],
}


def _lire(nom):
    return (SKILLS / nom / "SKILL.md").read_text(encoding="utf-8")


def _frontmatter(texte):
    m = re.match(r"---\n(.*?)\n---\n", texte, re.S)
    assert m, "frontmatter absent"
    return dict(re.findall(r"^(\w+): (.+)$", m.group(1), re.M))


@pytest.mark.parametrize("nom", NOMS)
def test_le_skill_existe(nom):
    assert (SKILLS / nom / "SKILL.md").is_file()


def test_aucun_skill_en_trop():
    assert sorted(p.name for p in SKILLS.iterdir() if p.is_dir()) == sorted(NOMS)


@pytest.mark.parametrize("nom", NOMS)
def test_frontmatter_name_egal_dossier(nom):
    assert _frontmatter(_lire(nom))["name"] == nom


@pytest.mark.parametrize("nom", NOMS)
def test_description_commence_par_un_verbe_et_dit_quand_l_utiliser(nom):
    d = _frontmatter(_lire(nom))["description"]
    assert re.match(r"[A-ZÉ][a-zéèêîô]+(er|ir|re)\b", d), d  # infinitif
    assert re.search(r"\b(quand|lors|avant|après|pendant)\b", d, re.I), d


@pytest.mark.parametrize("nom,motifs", PIEGES.items())
def test_chaque_piege_obligatoire_est_cite(nom, motifs):
    texte = _lire(nom)
    manquants = [m for m in motifs if not re.search(m, texte, re.I)]
    assert not manquants, manquants


def test_acl_cite_aclasuser_et_une_regle_testee_par_cas():
    assert re.search(r"un test par règle", _lire("grist-acl"), re.I)


def test_quality_bar_cite_les_criteres_de_performance():
    assert "grist-perf" in _lire("grist-quality-bar")


def test_mcp_tient_en_une_page():
    assert len(_lire("grist-mcp").splitlines()) <= 60


@pytest.mark.parametrize("nom", NOMS)
def test_aucune_reference_a_dm(nom):
    assert not re.search(r"\b(dm|ks)-|\.dm/", _lire(nom))


@pytest.mark.parametrize("nom", NOMS)
def test_aucune_donnee_reelle(nom):
    # Pas de clé, d'identifiant de document ni de nom de projet réel.
    assert not re.search(r"SCIP|SP2C|sirpa|Pulsar|gouv\.fr|[A-Za-z0-9]{22}", _lire(nom))
