"""Configuration d'un projet : lecture de `.grist-driven.json` et import de ses modules de données."""

import importlib
import json
import sys
from dataclasses import dataclass
from pathlib import Path

CONFIG = ".grist-driven.json"
DESIGN_SYSTEMS = ("dsfr", "ui-kit")


@dataclass
class Projet:
    racine: Path
    app: str
    package: str
    design_system: str
    widgets_dir: str
    core: str

    @property
    def schema(self):
        return importlib.import_module(f"{self.package}.schema")

    @property
    def regles(self):
        return importlib.import_module(f"{self.package}.acl_rules")

    @property
    def amorcer(self):
        """Module `<package>.amorcer`, ou None s'il n'existe pas (facultatif)."""
        nom = f"{self.package}.amorcer"
        try:
            return importlib.import_module(nom)
        except ModuleNotFoundError as e:
            if e.name == nom:
                return None
            raise


def charger_projet(racine: Path) -> Projet:
    """Lit `.grist-driven.json` ; `ValueError` lisible si absent, incomplet ou au design system inconnu."""
    racine = Path(racine).resolve()
    fichier = racine / CONFIG
    if not fichier.exists():
        raise ValueError(f"{CONFIG} introuvable dans {racine} : lancer la commande à la racine d'un projet "
                         "installé par `install.sh init`.")
    try:
        cfg = json.loads(fichier.read_text(encoding="utf-8"))
    except ValueError as e:
        raise ValueError(f"{CONFIG} illisible : {e}") from e
    manquantes = [c for c in ("app", "package", "design_system") if not cfg.get(c)]
    if manquantes:
        raise ValueError(f"{CONFIG} incomplet : {', '.join(manquantes)} manquant(s).")
    if cfg["design_system"] not in DESIGN_SYSTEMS:
        raise ValueError(f"Design system « {cfg['design_system']} » inconnu dans {CONFIG} : "
                         f"{' ou '.join(DESIGN_SYSTEMS)}.")
    if str(racine) not in sys.path:
        sys.path.insert(0, str(racine))
    ds = cfg["design_system"]
    return Projet(racine=racine, app=cfg["app"], package=cfg["package"], design_system=ds,
                  widgets_dir=cfg.get("widgets_dir") or ("widgets_ui" if ds == "ui-kit" else "widgets"),
                  core=cfg.get("core") or "widgets/core.js")
