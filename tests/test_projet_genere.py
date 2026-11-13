"""Intégration : `install.sh init` pose le gabarit dans un dossier temporaire, pour chaque profil,
puis le projet généré passe ses propres tests et `apply-schema --dry-run` (client factice) ne lève rien.
Aucun réseau : le kit est installé depuis `packages/grist-kit` (chemin local)."""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent
INSTALL = REPO / "install.sh"


def _installer(projet, design_system):
    env = {**os.environ, "HOME": str(projet), "GRIST_KIT_SPEC": str(REPO / "packages" / "grist-kit"),
           "GRIST_DRIVEN_VENV_ARGS": "--system-site-packages",
           "GRIST_DRIVEN_PIP_ARGS": "--no-index --no-deps --no-build-isolation",
           "GRIST_DRIVEN_TTY": str(projet / "absent")}
    env.pop("GRIST_API_KEY", None)
    r = subprocess.run(["bash", str(INSTALL), "init", "--yes", "--name", "demo-app", "--design-system", design_system,
                        "--mcp", "none", "--no-git-flow", "--no-hooks", "--ci"],
                       cwd=projet, env=env, capture_output=True, text=True, stdin=subprocess.DEVNULL)
    assert r.returncode == 0, r.stdout + r.stderr
    return r


def _py(projet, *args):
    return subprocess.run([str(projet / ".venv" / "bin" / "python"), *args], cwd=projet,
                          capture_output=True, text=True)


@pytest.fixture(params=["dsfr", "ui-kit"])
def projet(request, tmp_path):
    _installer(tmp_path, request.param)
    return tmp_path, request.param


def test_projet_genere_passe_ses_tests(projet):
    chemin, _ = projet
    r = _py(chemin, "-m", "pytest", "-q")
    assert r.returncode == 0, r.stdout + r.stderr


def test_apply_schema_dry_run_avec_client_factice(projet):
    chemin, _ = projet
    code = ("from grist_kit import __main__ as cli; from grist_kit.testing.faux_grist import ClientFactice; "
            "import sys; sys.exit(cli.main(['apply-schema', '--dry-run'], racine='.', client=ClientFactice()))")
    r = _py(chemin, "-c", code)
    assert r.returncode == 0, r.stdout + r.stderr


def test_config_et_env(projet):
    chemin, ds = projet
    cfg = json.loads((chemin / ".grist-driven.json").read_text())
    assert (cfg["package"], cfg["design_system"]) == ("demo_app", ds)
    assert oct((chemin / ".env").stat().st_mode & 0o777) == "0o600"
    assert (chemin / ".github/workflows/ci.yml").exists()


def test_dsfr_inliner_check_et_tests_node(tmp_path):
    _installer(tmp_path, "dsfr")
    r = _py(tmp_path, "-m", "grist_kit", "inliner", "--check")
    assert r.returncode == 0, r.stdout + r.stderr
    if shutil.which("node"):
        n = subprocess.run(["node", "--test", "tests/core.test.js"], cwd=tmp_path, capture_output=True, text=True)
        assert n.returncode == 0, n.stdout + n.stderr


def test_uikit_structure_et_build_double(tmp_path):
    """Pas de npm ni de Vite ici (aucun réseau) : on vérifie la structure, la syntaxe de build.mjs
    et le message de l'inliner ; le build réel est documenté dans packages/grist-kit/ECARTS.md."""
    _installer(tmp_path, "ui-kit")
    pkg = json.loads((tmp_path / "widgets_ui" / "package.json").read_text())
    assert "@gouvfr-lasuite/ui-components" in pkg["dependencies"]
    # version vérifiée au registre npm (la 2.0.0, posée à l'origine, n'existe pas) ; réseau interdit ici.
    assert pkg["dependencies"]["@gouvfr-lasuite/ui-components"] == "1.5.0"
    assert "vite-plugin-singlefile" in pkg["devDependencies"]
    assert "@types/node" in pkg["devDependencies"]  # vite.config.ts importe node:path
    assert "__dirname" not in (tmp_path / "widgets_ui" / "vite.config.ts").read_text()  # module ESM
    assert pkg["scripts"]["build"]
    if shutil.which("node"):
        n = subprocess.run(["node", "--check", "build.mjs"], cwd=tmp_path / "widgets_ui", capture_output=True, text=True)
        assert n.returncode == 0, n.stderr
    r = _py(tmp_path, "-m", "grist_kit", "inliner")
    assert r.returncode == 0 and "ui-kit" in r.stdout
