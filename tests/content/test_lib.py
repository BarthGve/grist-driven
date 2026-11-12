"""Scripts du flux (tableau, config, version, wiki, init) et porte de qualité.

Aucun réseau : `gh` est remplacé par tests/fixtures/gh-stub.sh, les dépôts git sont fabriqués
dans des répertoires temporaires.
"""
import json
import os
import re
import subprocess
from pathlib import Path
from types import SimpleNamespace

import pytest

RACINE = Path(__file__).resolve().parents[2]
LIB = RACINE / "src" / "lib"
GATE = RACINE / "src" / "hooks" / "grist-gate.sh"
STUB = RACINE / "tests" / "fixtures" / "gh-stub.sh"
SCRIPTS = [LIB / f"grist-{n}.sh" for n in ("board", "config", "version", "wiki", "init")] + [GATE]

STATUTS = {"backlog": "opt1", "ready": "opt2", "in progress": "opt3", "review": "opt4", "test": "opt5", "shipped": "opt6"}
CONFIG = {
    "owner": "acme", "repo": "app", "project_id": "PVT_test", "project_number": 1,
    "status_field_id": "FIELD_status", "status_option_ids": STATUTS,
}


def sh(cmd, cwd, env, entree=None):
    return subprocess.run([str(c) for c in cmd], cwd=cwd, env=env, input=entree, text=True, capture_output=True)


@pytest.fixture
def projet(tmp_path):
    """Dépôt git avec main + next, faux gh en tête du PATH, état du faux gh vide."""
    racine = tmp_path / "projet"
    racine.mkdir()
    (tmp_path / "bin").mkdir()
    (tmp_path / "bin" / "gh").symlink_to(STUB)
    etat = tmp_path / "etat.json"
    etat.write_text("{}")
    env = {
        **os.environ,
        "PATH": f"{tmp_path / 'bin'}:{os.environ['PATH']}",
        "GRIST_GH_STUB_STATE": str(etat),
        "GIT_AUTHOR_NAME": "t", "GIT_AUTHOR_EMAIL": "t@t.test",
        "GIT_COMMITTER_NAME": "t", "GIT_COMMITTER_EMAIL": "t@t.test",
    }
    env.pop("GRIST_RACINE", None)
    p = SimpleNamespace(racine=racine, env=env, etat=etat, tmp=tmp_path)
    git(p, "init", "-q", "-b", "main")
    (racine / "README.md").write_text("x\n")
    git(p, "add", "README.md")
    git(p, "commit", "-q", "-m", "init")
    git(p, "branch", "next")
    return p


def git(p, *args, cwd=None):
    r = sh(["git", *args], cwd or p.racine, p.env)
    assert r.returncode == 0, r.stderr
    return r.stdout


def issue(cle, statut, n):
    return {
        "title": f"[{cle}] Titre {n}", "number": n, "id": f"I_{n}",
        "projectItems": [{"id": f"PVTI_{n}", "status": {"optionId": STATUTS[statut], "name": statut}}],
    }


def poser_tableau(p, issues, config=CONFIG):
    (p.racine / ".grist").mkdir(exist_ok=True)
    (p.racine / ".grist" / "config.json").write_text(json.dumps(config))
    p.etat.write_text(json.dumps({"issues": issues, "status_option_ids": STATUTS}))


def etat(p):
    return json.loads(p.etat.read_text())


def statut_de(p, numero):
    i = next(i for i in etat(p)["issues"] if i["number"] == numero)
    return i["projectItems"][0]["status"]["name"]


def board(p, *args):
    return sh([LIB / "grist-board.sh", *args], p.racine, p.env)


# ---------------------------------------------------------------- version


def test_bump_patch_minor_major_synchronise_changelog(tmp_path):
    (tmp_path / "VERSION").write_text("0.1.0\n")
    (tmp_path / "CHANGELOG.md").write_text("# Journal\n\n## 0.1.0 - 2026-01-01\n\n- départ\n")
    (tmp_path / "pyproject.toml").write_text('[project]\nname = "x"\nversion = "0.1.0"\n')
    (tmp_path / "package.json").write_text(json.dumps({"name": "x", "version": "0.1.0"}))
    env = {**os.environ}
    for partie, attendu in (("patch", "0.1.1"), ("minor", "0.2.0"), ("major", "1.0.0")):
        r = sh([LIB / "grist-version.sh", "bump", partie], tmp_path, env)
        assert r.returncode == 0, r.stderr
        assert r.stdout.strip() == attendu
        assert (tmp_path / "VERSION").read_text().strip() == attendu
        assert f'version = "{attendu}"' in (tmp_path / "pyproject.toml").read_text()
        assert json.loads((tmp_path / "package.json").read_text())["version"] == attendu
        titres = re.findall(r"^## (\S+) - \d{4}-\d\d-\d\d$", (tmp_path / "CHANGELOG.md").read_text(), re.M)
        assert titres[0] == attendu  # la nouvelle section passe au-dessus des anciennes
    assert titres == ["1.0.0", "0.2.0", "0.1.1", "0.1.0"]
    assert (tmp_path / "CHANGELOG.md").read_text().startswith("# Journal")


def test_bump_refuse_partie_inconnue_ou_version_invalide(tmp_path):
    (tmp_path / "VERSION").write_text("0.1.0\n")
    env = {**os.environ}
    assert sh([LIB / "grist-version.sh", "bump", "gros"], tmp_path, env).returncode != 0
    (tmp_path / "VERSION").write_text("pas-une-version\n")
    r = sh([LIB / "grist-version.sh", "bump", "patch"], tmp_path, env)
    assert r.returncode != 0 and (tmp_path / "VERSION").read_text() == "pas-une-version\n"
    assert sh([LIB / "grist-version.sh", "current"], tmp_path, env).returncode == 0


# ---------------------------------------------------------------- porte


def sur_branche(p, branche, fichier, contenu="x\n"):
    git(p, "checkout", "-q", "-b", branche)
    cible = p.racine / fichier
    cible.parent.mkdir(parents=True, exist_ok=True)
    cible.write_text(contenu)
    git(p, "add", fichier)


def porte(p, *args, entree=None):
    return sh([GATE, *args], p.racine, p.env, entree)


def test_porte_refuse_code_sans_plan_valide(projet):
    sur_branche(projet, "feature/s01-x/t01-y", "src/app.py")
    r = porte(projet, "pre-commit")
    assert r.returncode != 0 and "docs/plans/s01-x.md" in r.stderr
    (projet.racine / "docs" / "plans").mkdir(parents=True)
    plan = projet.racine / "docs" / "plans" / "s01-x.md"
    plan.write_text("validated: no\n")
    assert porte(projet, "pre-commit").returncode != 0
    plan.write_text("# Plan\nvalidated: yes\n")
    assert porte(projet, "pre-commit").returncode == 0  # tableau non initialisé : porte « prêt » levée


def test_porte_exige_ticket_pret_quand_le_tableau_existe(projet):
    sur_branche(projet, "feature/s01-x/t01-y", "src/app.py")
    (projet.racine / "docs" / "plans").mkdir(parents=True)
    (projet.racine / "docs" / "plans" / "s01-x.md").write_text("validated: yes\n")
    poser_tableau(projet, [issue("s01-x/t01-y", "backlog", 2)])
    r = porte(projet, "pre-commit")
    assert r.returncode != 0 and "backlog" in r.stderr
    poser_tableau(projet, [issue("s01-x/t01-y", "ready", 2)])
    assert porte(projet, "pre-commit").returncode == 0
    poser_tableau(projet, [issue("s01-x/t01-y", "review", 2)])
    assert porte(projet, "pre-commit").returncode != 0


def test_porte_accepte_les_commits_de_docs(projet):
    sur_branche(projet, "feature/s01-x/t01-y", "docs/notes.md")
    assert porte(projet, "pre-commit").returncode == 0
    git(projet, "reset", "-q")
    sur_branche_cadrage = projet.racine / "docs" / "notes.md"
    assert sur_branche_cadrage.exists()
    # branche de cadrage : docs seulement, le code est refusé
    git(projet, "checkout", "-q", "-b", "feature/s02-z")
    (projet.racine / "src").mkdir()
    (projet.racine / "src" / "a.py").write_text("x\n")
    git(projet, "add", "src/a.py", "docs/notes.md")
    r = porte(projet, "pre-commit")
    assert r.returncode != 0 and "cadrage" in r.stderr
    git(projet, "reset", "-q", "src/a.py")
    assert porte(projet, "pre-commit").returncode == 0


def test_porte_ignore_les_branches_hors_flux(projet):
    sur_branche(projet, "correctif", "src/app.py")
    assert porte(projet, "pre-commit").returncode == 0


def test_pre_push_main_ne_recoit_que_next(projet):
    zero = "0" * 40
    tete = git(projet, "rev-parse", "HEAD").strip()
    r = porte(projet, "pre-push", entree=f"refs/heads/feature/a {tete} refs/heads/main {zero}\n")
    assert r.returncode != 0 and "next" in r.stderr
    # next → main : VERSION et CHANGELOG obligatoires
    (projet.racine / "VERSION").write_text("0.2.0\n")
    git(projet, "add", "VERSION")
    git(projet, "commit", "-q", "-m", "v")
    nouveau = git(projet, "rev-parse", "HEAD").strip()
    r = porte(projet, "pre-push", entree=f"refs/heads/next {nouveau} refs/heads/main {tete}\n")
    assert r.returncode == 0, r.stderr
    r = porte(projet, "pre-push", entree=f"refs/heads/next {tete} refs/heads/main {tete}\n")
    assert r.returncode != 0 and "VERSION" in r.stderr


def test_pre_push_ticket_vers_next_demande_une_revue(projet):
    zero = "0" * 40
    tete = git(projet, "rev-parse", "HEAD").strip()
    entree = f"refs/heads/feature/s01-x/t01-y {tete} refs/heads/next {zero}\n"
    assert porte(projet, "pre-push", entree=entree).returncode != 0
    (projet.racine / "docs" / "reviews" / "s01-x").mkdir(parents=True)
    (projet.racine / "docs" / "product").mkdir(parents=True)
    (projet.racine / "docs" / "product" / "s01-x.md").write_text("doc\n")
    revue = projet.racine / "docs" / "reviews" / "s01-x" / "t01-y.md"
    revue.write_text("Ship allowed: no\nTour 2\nShip allowed: yes\n")
    assert porte(projet, "pre-push", entree=entree).returncode == 0
    revue.write_text("Ship allowed: yes\nTour 2\nShip allowed: no\n")  # seul le dernier verdict compte
    assert porte(projet, "pre-push", entree=entree).returncode != 0


# ---------------------------------------------------------------- tableau


@pytest.mark.parametrize("depart,arrivee", [
    ("ready", "test"), ("backlog", "in progress"), ("in progress", "shipped"),
    ("shipped", "ready"), ("test", "review"), ("review", "ready"),
])
def test_board_transition_interdite_refusee(projet, depart, arrivee):
    poser_tableau(projet, [issue("s01-x/t01-y", depart, 2)])
    r = board(projet, "status-set", "s01-x/t01-y", arrivee)
    assert r.returncode != 0 and "transition" in r.stderr
    assert statut_de(projet, 2) == depart and "edits" not in etat(projet)


def test_board_transitions_autorisees_et_ordre_complet(projet):
    poser_tableau(projet, [issue("s01-x/t01-y", "backlog", 2)])
    for suivant in ("ready", "in progress", "review", "in progress", "review", "test", "shipped"):
        r = board(projet, "status-set", "s01-x/t01-y", suivant)
        assert r.returncode == 0, (suivant, r.stderr)
        assert statut_de(projet, 2) == suivant
    assert etat(projet)["edits"][-1] == {"id": "PVTI_2", "option": "opt6"}
    assert board(projet, "status-get", "s01-x/t01-y").stdout.strip() == "shipped"


def test_board_statut_inconnu_et_parent_jamais_ready(projet):
    poser_tableau(projet, [issue("s01-x", "backlog", 1), issue("s01-x/t01-y", "backlog", 2)])
    assert board(projet, "status-set", "s01-x/t01-y", "fini").returncode != 0
    r = board(projet, "status-set", "s01-x", "ready")
    assert r.returncode != 0 and "parent" in r.stderr.lower()
    assert board(projet, "status-get", "s09-absent").returncode != 0
    assert board(projet, "require-ready", "s01-x").returncode != 0  # réservé aux tickets
    assert board(projet, "require-ready", "s01-x/t01-y").returncode != 0
    assert board(projet, "status-set", "s01-x/t01-y", "ready").returncode == 0
    assert board(projet, "require-ready", "s01-x/t01-y").returncode == 0


def test_board_parent_derive_des_tickets_et_lit_les_tickets_une_fois(projet):
    poser_tableau(projet, [
        issue("s01-x", "backlog", 1), issue("s01-x/t01-a", "review", 2),
        issue("s01-x/t02-b", "backlog", 3), issue("s02-y", "backlog", 4),
    ])
    r = board(projet, "parent-sync", "s01-x")
    assert r.returncode == 0 and r.stdout.strip() == "in progress"
    assert statut_de(projet, 1) == "in progress" and etat(projet)["list_calls"] == 1
    assert board(projet, "parent-sync", "s02-y").stdout.strip() == "backlog"
    assert "edits" not in etat(projet) or len(etat(projet)["edits"]) == 1  # s02-y inchangé : aucune écriture
    sorties = dict(l.split("\t") for l in board(projet, "status-all").stdout.splitlines())
    assert sorties["s01-x/t01-a"] == "review" and sorties["s01-x"] == "in progress"


@pytest.mark.parametrize("enfants,attendu", [
    (["shipped", "shipped"], "shipped"), (["test", "shipped"], "test"),
    (["test", "backlog"], "in progress"), (["ready", "backlog"], "backlog"),
])
def test_board_derivation_du_parent(projet, enfants, attendu):
    poser_tableau(projet, [issue("s01-x", "backlog", 1)] + [issue(f"s01-x/t0{i}-a", s, i + 2) for i, s in enumerate(enfants)])
    assert board(projet, "parent-sync", "s01-x").stdout.strip() == attendu


def test_board_creation_us_et_ticket_avec_repli_parent(projet):
    poser_tableau(projet, [])
    corps = projet.tmp / "corps.md"
    corps.write_text("Corps.\n")
    assert board(projet, "issue-create-us", "s01-x", "Ma story", corps).stdout.strip() == "1"
    etat_avant = etat(projet)
    assert etat_avant["issues"][0]["title"] == "[s01-x] Ma story"
    s = json.loads(projet.etat.read_text())
    s["subissue_fail"] = True
    s["item_add_fail_remaining"] = 1  # un échec d'ajout au tableau : une seule nouvelle tentative
    projet.etat.write_text(json.dumps(s))
    r = board(projet, "issue-create-ticket", "s01-x", "t01-y", "Mon ticket", corps)
    assert r.returncode == 0 and r.stdout.strip() == "2", r.stderr
    e = etat(projet)
    ticket = e["issues"][1]
    assert ticket["title"] == "[s01-x/t01-y] Mon ticket" and "ticket" in ticket["labels"]
    assert "Parent: #1" in ticket["body"] and e["item_add_calls"] == 3  # us + échec + nouvelle tentative


def test_board_adopte_une_issue_ecrite_a_la_main(projet):
    poser_tableau(projet, [{"title": "À la main", "number": 5, "id": "I_5", "projectItems": []}])
    r = board(projet, "issue-adopt", "s03-z", "5", "Titre propre")
    assert r.returncode == 0, r.stderr
    assert etat(projet)["issues"][0]["title"] == "[s03-z] Titre propre"


# ---------------------------------------------------------------- config


def test_config_incomplete_refusee(projet):
    sans_review = {k: v for k, v in STATUTS.items() if k != "review"}
    poser_tableau(projet, [issue("s01-x/t01-y", "ready", 2)], {**CONFIG, "status_option_ids": sans_review})
    r = board(projet, "status-get", "s01-x/t01-y")
    assert r.returncode != 0 and "review" in r.stderr
    r = sh([LIB / "grist-init.sh", "assert-status-ids", json.dumps(sans_review)], projet.racine, projet.env)
    assert r.returncode != 0 and "review" in r.stderr
    r = sh([LIB / "grist-init.sh", "assert-status-ids", json.dumps(STATUTS)], projet.racine, projet.env)
    assert r.returncode == 0


def test_config_absente_message_clair(projet):
    r = board(projet, "status-get", "s01-x")
    assert r.returncode != 0 and ".grist/config.json" in r.stderr


# ---------------------------------------------------------------- wiki


def test_wiki_publie_les_docs_produit_dans_un_depot_local(projet):
    poser_tableau(projet, [])
    (projet.racine / "docs" / "product").mkdir(parents=True)
    (projet.racine / "docs" / "product" / "s01-x.md").write_text("# Story X\n")
    wiki = projet.tmp / "wiki.git"
    git(projet, "init", "-q", "--bare", "-b", "master", str(wiki))
    env = {**projet.env, "GRIST_WIKI_URL": str(wiki)}
    r = sh([LIB / "grist-wiki.sh", "publish", projet.racine, "0.3.0", "s01-x"], projet.racine, env)
    assert r.returncode == 0, r.stderr
    copie = projet.tmp / "copie"
    git(projet, "clone", "-q", str(wiki), str(copie), cwd=projet.tmp)
    assert (copie / "s01-x.md").read_text() == "# Story X\n"
    accueil = (copie / "Home.md").read_text()
    assert "0.3.0" in accueil and "[s01-x](s01-x)" in accueil
    # une story déjà publiée reste listée quand une autre arrive
    (projet.racine / "docs" / "product" / "s02-y.md").write_text("# Story Y\n")
    assert sh([LIB / "grist-wiki.sh", "publish", projet.racine, "0.4.0", "s02-y"], projet.racine, env).returncode == 0
    git(projet, "pull", "-q", cwd=copie)
    accueil = (copie / "Home.md").read_text()
    assert "[s01-x](s01-x)" in accueil and "[s02-y](s02-y)" in accueil and "0.4.0" in accueil


def test_wiki_refuse_sans_doc_produit(projet):
    poser_tableau(projet, [])
    env = {**projet.env, "GRIST_WIKI_URL": str(projet.tmp / "inexistant.git")}
    r = sh([LIB / "grist-wiki.sh", "publish", projet.racine, "0.3.0", "s09-absent"], projet.racine, env)
    assert r.returncode != 0 and "docs/product/s09-absent.md" in r.stderr


# ---------------------------------------------------------------- init


def test_init_sans_distant_cree_flux_version_et_config(tmp_path, projet):
    neuf = tmp_path / "neuf"
    neuf.mkdir()
    r = sh([LIB / "grist-init.sh", "run", "--no-remote", "--owner", "acme", "--repo", "app", "--yes"], neuf, projet.env)
    assert r.returncode == 0, r.stderr
    assert (neuf / "VERSION").read_text().strip() == "0.1.0"
    assert "## 0.1.0" in (neuf / "CHANGELOG.md").read_text()
    branches = git(projet, "branch", "--format=%(refname:short)", cwd=neuf).split()
    assert {"main", "next"} <= set(branches)
    cfg = json.loads((neuf / ".grist" / "config.json").read_text())
    assert cfg["owner"] == "acme" and cfg["repo"] == "app" and cfg["project_number"] == 7
    assert set(cfg["status_option_ids"]) == set(STATUTS)
    appels = [" ".join(a) for a in etat(projet)["appels"]]
    assert not any("repo create" in a or a.startswith("api -X") for a in appels)
    # relancé : la config existante n'est pas réécrite et aucun projet n'est recréé
    avant = (neuf / ".grist" / "config.json").read_text()
    r = sh([LIB / "grist-init.sh", "run", "--no-remote", "--owner", "acme", "--repo", "app", "--yes"], neuf, projet.env)
    assert r.returncode == 0 and (neuf / ".grist" / "config.json").read_text() == avant
    assert sum("project create" in " ".join(a) for a in etat(projet)["appels"]) == 1


def test_init_refuse_sans_confirmation_hors_terminal(tmp_path, projet):
    neuf = tmp_path / "neuf"
    neuf.mkdir()
    r = sh([LIB / "grist-init.sh", "run", "--no-remote", "--owner", "acme", "--repo", "app"], neuf, projet.env, entree="")
    assert r.returncode != 0 and not (neuf / ".grist" / "config.json").exists()


# ---------------------------------------------------------------- hygiène


def test_aucun_reste_de_dm_dans_lib():
    motif = re.compile(r"\bdm-|\bks-|\.dm/|\bDM_|\bnode\b|\bnpm\b|\bcodex\b|\bgrok\b", re.I)
    for f in SCRIPTS + [STUB]:
        assert f.exists(), f
        for n, ligne in enumerate(f.read_text().splitlines(), 1):
            assert not motif.search(ligne), f"{f.relative_to(RACINE)}:{n}: {ligne}"


@pytest.mark.parametrize("script", SCRIPTS, ids=lambda s: s.name)
def test_scripts_syntaxe_valide_et_executables(script):
    assert subprocess.run(["bash", "-n", str(script)], capture_output=True).returncode == 0
    assert os.access(script, os.X_OK)
