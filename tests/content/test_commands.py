"""Commandes du pipeline : frontmatter, références croisées, portes lues par les scripts, absence de reste de driven."""
import re
from pathlib import Path

import pytest

RACINE = Path(__file__).resolve().parents[2]
COMMANDES = RACINE / "src" / "commands"
SKILLS = RACINE / "src" / "skills"
AGENTS = RACINE / "src" / "agents"
LIB = RACINE / "src" / "lib"

LOT_A = ["prd", "init", "stories", "stories-review", "architect", "design-system"]
LOT_B = ["research", "design", "plan", "docs"]
LOT_C = ["execute", "review", "ship", "release", "feature", "continue", "status", "help", "orchestrator"]
# Chaque lot ajoute ses noms : un test qui ne regarde que les fichiers présents passerait à vide.
ATTENDUES = LOT_A + LOT_B + LOT_C

# Commandes de la tâche 20 : citées avant d'exister. À vider quand la tâche 20 les écrit.
PREVUES_TACHE_20 = {"grist-schema", "grist-acl", "grist-widget", "grist-deploy", "grist-recette", "grist-optimise"}

RESTES = re.compile(r"\bdm-|\bks-|\.dm/")
SOUS_COMMANDES_TABLEAU = {
    "status-get", "status-set", "status-all", "require-ready", "parent-sync",
    "issue-create-us", "issue-create-ticket", "issue-adopt",
}


def _fichier(nom):
    return COMMANDES / f"grist-{nom}.md"


def _texte(nom):
    if not _fichier(nom).is_file():
        pytest.skip(f"grist-{nom} pas encore écrite (voir test_les_commandes_attendues_existent)")
    return _fichier(nom).read_text(encoding="utf-8")


def _frontmatter(nom):
    texte = _texte(nom)
    assert texte.startswith("---\n"), f"grist-{nom} : frontmatter absent"
    bloc = texte.split("---\n", 2)[1]
    return bloc


def test_les_commandes_attendues_existent():
    assert [n for n in ATTENDUES if not _fichier(n).is_file()] == []


def test_aucune_commande_en_trop():
    presentes = sorted(p.stem for p in COMMANDES.glob("grist-*.md"))
    assert [p for p in presentes if p.removeprefix("grist-") not in ATTENDUES + ["schema", "acl", "widget", "deploy", "recette", "optimise"]] == []


@pytest.mark.parametrize("nom", ATTENDUES)
def test_chaque_commande_a_un_frontmatter_complet(nom):
    if not _fichier(nom).is_file():
        pytest.skip("pas encore écrite (voir test_les_commandes_attendues_existent)")
    bloc = _frontmatter(nom)
    desc = re.search(r"^description:\s*(.+)$", bloc, re.M)
    assert desc and len(desc.group(1)) > 30, f"grist-{nom} : description"
    assert re.search(r"^argument-hint:\s*\S", bloc, re.M), f"grist-{nom} : argument-hint"
    assert re.search(r"^allowed-tools:\s*\n(\s+- \w+\n?)+", bloc, re.M), f"grist-{nom} : allowed-tools"


@pytest.mark.parametrize("nom", ATTENDUES)
def test_nom_de_fichier_egal_au_nom_de_commande(nom):
    if not _fichier(nom).is_file():
        pytest.skip("pas encore écrite")
    titre = re.search(r"^# (grist-[\w-]+)", _texte(nom).split("---\n", 2)[2], re.M)
    assert titre and titre.group(1) == f"grist-{nom}"


@pytest.mark.parametrize("nom", ATTENDUES)
def test_aucune_reference_a_dm(nom):
    if not _fichier(nom).is_file():
        pytest.skip("pas encore écrite")
    assert not RESTES.search(_texte(nom))


@pytest.mark.parametrize("nom", ATTENDUES)
def test_toute_commande_citee_existe(nom):
    if not _fichier(nom).is_file():
        pytest.skip("pas encore écrite")
    # les lots suivants citent des commandes pas encore écrites : l'existence finale est garantie par test_les_commandes_attendues_existent
    existantes = {f"grist-{n}" for n in LOT_A + LOT_B + LOT_C} | PREVUES_TACHE_20
    # (?<![\w./-]) : ni chemin (.grist/lib/grist-board.sh), ni dossier (src/skills/grist-tdd)
    citees = set(re.findall(r"(?<![\w./`-])/(grist-[a-z]+(?:-[a-z]+)*)\b(?![.\w])", _texte(nom)))
    assert citees - existantes == set()


@pytest.mark.parametrize("nom", ATTENDUES)
def test_tout_skill_et_agent_cite_existe(nom):
    if not _fichier(nom).is_file():
        pytest.skip("pas encore écrite")
    texte = _texte(nom)
    skills = set(re.findall(r"skills? `(grist-[\w-]+)`", texte))
    assert {s for s in skills if not (SKILLS / s / "SKILL.md").is_file()} == set()
    agents = set(re.findall(r"subagent_type: ([\w-]+)", texte)) | set(re.findall(r"sous-agent `([\w-]+)`", texte))
    assert {a for a in agents if not (AGENTS / f"{a}.md").is_file()} == set()


@pytest.mark.parametrize("nom", ATTENDUES)
def test_scripts_et_sous_commandes_du_tableau_existent(nom):
    if not _fichier(nom).is_file():
        pytest.skip("pas encore écrite")
    texte = _texte(nom)
    for script in re.findall(r"\.grist/lib/([\w.-]+\.sh)", texte):
        assert (LIB / script).is_file(), script
    for sous in re.findall(r"grist-board\.sh (?!\")([a-z-]+)", texte):
        assert sous in SOUS_COMMANDES_TABLEAU, sous


def test_prd_n_a_pas_de_mode_cloner_un_saas():
    texte = _texte("prd")
    assert not re.search(r"cloner|clone|SaaS", texte, re.I)
    assert "nouveau projet" in texte and "reprise" in texte
    assert re.search(r"profils? d'utilisateurs", texte, re.I) and re.search(r"volum[ée]trie", texte, re.I)


def test_architect_produit_les_cinq_sections():
    texte = _texte("architect")
    for titre in ("Modèle de données", "Matrice ACL", "Inventaire des widgets", "Règles en double", "Plan de déploiement"):
        assert titre in texte, titre
    assert "docs/architecture.md" in texte and "profil × table × droit" in texte


def test_init_ne_recree_pas_le_projet():
    texte = _texte("init")
    assert "install.sh" in texte and "grist-init.sh" in texte
    assert "VERSION" in texte and "wiki" in texte.lower() and "tableau" in texte.lower()


def test_stories_review_delegue_et_ecrit_le_verdict_lu_par_la_suite():
    texte = _texte("stories-review")
    assert "subagent_type: stories-reviewer" in texte
    assert "Stories prêtes : oui" in texte and "Gravité max :" in texte
    assert "Agent" in _frontmatter("stories-review")


def test_design_system_garde_une_seule_variante():
    texte = _texte("design-system")
    assert ".grist-driven.json" in texte and "design_system" in texte
    assert "dsfr" in texte and "ui-kit" in texte


def test_les_commandes_qui_delegent_ont_l_outil_agent():
    for nom in ("stories-review", "research", "execute", "review", "orchestrator", "feature"):
        if _fichier(nom).is_file():
            assert re.search(r"^\s+- Agent$", _frontmatter(nom), re.M), nom


def test_execute_n_a_ni_write_ni_edit():
    if _fichier("execute").is_file():
        assert not re.search(r"^\s+- (Write|Edit)$", _frontmatter("execute"), re.M)


def test_plan_ecrit_la_ligne_lue_par_la_porte():
    texte = _texte("plan")
    assert "validated: yes" in texte and "validated: no" in texte
    assert "issue-create-ticket" in texte and "size" in texte and "estimate" in texte


def test_review_et_ship_lisent_le_meme_verdict():
    for nom in ("review", "ship"):
        assert "Ship allowed:" in _texte(nom), nom
    assert "Max severity:" in _texte("review")


def test_ship_vise_next_jamais_main_et_exige_le_document_produit():
    texte = _texte("ship")
    assert "--base next" in texte and "docs/product/" in texte
    assert "--squash" in texte and "MERGED" in texte


def test_release_bump_avant_la_pr_et_renvoie_au_deploiement():
    texte = _texte("release")
    assert "grist-version.sh bump" in texte and "grist-wiki.sh publish" in texte
    assert "/grist-deploy" in texte
    assert not re.search(r"apply-schema|apply-acl|deployer\b", texte)


def test_feature_et_continue_partagent_l_ancre_du_mapping():
    ancre = "## Correspondance des issues ouvertes"
    assert ancre in _texte("continue") and ancre in _texte("stories")


def test_status_et_help_listent_toutes_les_commandes_du_flux():
    texte = _texte("help") + _texte("status")
    for nom in ATTENDUES:
        if nom not in ("help", "status") and _fichier(nom).is_file():
            assert f"/grist-{nom}" in _texte("help"), nom
    assert "status-all" in _texte("status")
