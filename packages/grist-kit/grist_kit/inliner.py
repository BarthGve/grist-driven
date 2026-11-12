"""Recopie un fichier JS (le « core ») dans les pages HTML qui l'embarquent.

Les widgets Grist sont des fichiers HTML autonomes : Grist ne charge qu'eux, le
JavaScript doit donc y vivre en clair. La logique pure reste dans un fichier
`core.js` testable à part ; `inliner` la dépose dans chaque page entre les marqueurs :

    /* === CORE BEGIN === */
    …
    /* === CORE END === */

À relancer après toute modification du core, sans quoi les widgets partent en
divergence silencieuse. Le core et les pages sont des paramètres.
"""

import re
import sys
from pathlib import Path

MARQUEURS = re.compile(
    r"(/\* === CORE BEGIN === \*/\n).*?(\n/\* === CORE END === \*/)", re.S
)


def inliner(page: Path, core: str, check: bool) -> bool:
    """Écrit ou compare le core inliné. Retourne True si la page est à jour."""
    page = Path(page)
    html = page.read_text(encoding="utf-8")
    trouve = MARQUEURS.search(html)
    if trouve is None:
        print(f"  {page.name} : marqueurs CORE absents", file=sys.stderr)
        return False
    if trouve.group(0)[len(trouve.group(1)) : -len(trouve.group(2))] == core:
        return True
    if check:
        print(f"  {page.name} : core à resynchroniser")
        return False
    # lambda : le core peut contenir des antislashs que re.sub interpréterait.
    page.write_text(
        MARQUEURS.sub(lambda m: m.group(1) + core + m.group(2), html),
        encoding="utf-8",
    )
    print(f"  {page.name} : core recopié ({len(core)} caractères)")
    return True


def inliner_tout(core_path: Path, pages: list[Path], check: bool) -> bool:
    """Recopie (ou compare) le core de `core_path` dans chaque page. True si tout est à jour."""
    core = Path(core_path).read_text(encoding="utf-8").strip()
    a_jour = True
    for page in pages:
        a_jour = inliner(page, core, check) and a_jour
    return a_jour
