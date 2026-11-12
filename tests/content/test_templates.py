"""Agents et gabarits de documents : structure, absence de reste de driven, références."""
import re
from pathlib import Path

RACINE = Path(__file__).resolve().parents[2]
AGENTS = RACINE / "src" / "agents"
GABARITS = RACINE / "src" / "templates"
NOMS_AGENTS = ["implementer", "reviewer", "stories-reviewer", "worktree-manager"]
NOMS_GABARITS = [
    "prd", "architecture", "stories", "plan", "research", "adr", "review-checklist",
    "stories-review-checklist", "product-doc", "design-brief", "design-system",
]
RESTES = re.compile(r"\bdm-|\bks-|\.dm/")


def _fichiers():
    return [AGENTS / f"{n}.md" for n in NOMS_AGENTS] + [GABARITS / f"{n}.md" for n in NOMS_GABARITS]


def _frontmatter(chemin: Path) -> dict[str, str]:
    texte = chemin.read_text(encoding="utf-8")
    assert texte.startswith("---\n"), f"{chemin.name} : frontmatter absent"
    bloc = texte.split("---\n", 2)[1]
    return dict(re.findall(r"^(\w+):\s*(.+)$", bloc, re.M))


def test_tous_les_fichiers_existent():
    assert [f.name for f in _fichiers() if not f.is_file()] == []


def test_architecture_a_les_cinq_sections_grist():
    texte = (GABARITS / "architecture.md").read_text(encoding="utf-8")
    titres = re.findall(r"^## (.+)$", texte, re.M)
    for motif in ("Modèle de données", "Matrice ACL", "Inventaire des widgets", "Règles en double", "Plan de déploiement"):
        assert any(t.startswith(motif) for t in titres), motif
    assert "profil × table × droit" in texte


def test_prd_a_profils_et_volumetrie():
    texte = (GABARITS / "prd.md").read_text(encoding="utf-8")
    assert re.search(r"^## Profils d'utilisateurs", texte, re.M)
    assert re.search(r"^## Volumétrie", texte, re.M)
    assert "nouveau projet" in texte and "reprise" in texte
    assert not re.search(r"cloner|clone", texte, re.I)


def test_design_system_a_deux_variantes():
    texte = (GABARITS / "design-system.md").read_text(encoding="utf-8")
    assert "## Variante `dsfr`" in texte and "## Variante `ui-kit`" in texte
    assert ".grist-driven.json" in texte and "@gouvfr-lasuite/ui-components" in texte


def test_agents_ont_un_frontmatter():
    for nom in NOMS_AGENTS:
        fm = _frontmatter(AGENTS / f"{nom}.md")
        assert fm.get("name") == nom, nom
        assert len(fm.get("description", "")) > 20, nom


def test_aucune_reference_a_dm():
    for f in _fichiers():
        assert not RESTES.search(f.read_text(encoding="utf-8")), f.name


def test_les_gabarits_cites_par_les_commandes_existent():
    # Les commandes (tâche 19) peuvent ne pas être encore là : le test porte alors sur les agents.
    sources = list((RACINE / "src" / "commands").glob("*.md")) + list(AGENTS.glob("*.md"))
    for f in sources:
        for nom in re.findall(r"templates/([\w-]+)\.md", f.read_text(encoding="utf-8")):
            assert (GABARITS / f"{nom}.md").is_file(), f"{f.name} cite templates/{nom}.md"


def test_les_skills_et_agents_cites_existent_ou_sont_prevus():
    # Les skills sont de la tâche 21 : on vérifie seulement qu'ils portent le préfixe grist-.
    for nom in NOMS_AGENTS:
        for s in re.findall(r"^\s+- ([\w-]+)$", (AGENTS / f"{nom}.md").read_text(encoding="utf-8"), re.M):
            assert s.startswith("grist-"), (nom, s)
