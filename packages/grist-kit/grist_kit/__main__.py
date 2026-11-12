"""`python -m grist_kit <commande>` : applique schéma, ACL, widgets et versions d'un projet Grist.

Toutes les commandes sont idempotentes et acceptent `--dry-run` (rien n'est écrit) et `--doc <id>`
(défaut : `GRIST_DOC_ID`). Le projet est lu dans le dossier courant (`.grist-driven.json`).
"""

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

from . import apply_acl, apply_schema, build_uikit, deployer, inliner, maj_formules, pages, versions
from .client import GristClient, GristErreur
from .projet import charger_projet


def _afficher(titre, rapport):
    print(f"{titre} :")
    for cle, val in rapport.items():
        print(f"  {cle} : {len(val) if isinstance(val, (list, tuple, set, dict)) else val}")


def _schema(p, c, a):
    _afficher("schéma", apply_schema.appliquer(c, p.schema, dry_run=a.dry_run))
    return 0


def _formules(p, c, a):
    _afficher("formules", maj_formules.appliquer(c, p.schema, dry_run=a.dry_run))
    return 0


def _acl(p, c, a):
    _afficher("ACL", apply_acl.appliquer(c, p.regles, dry_run=a.dry_run, prune=a.prune))
    return 0


def _amorcer(p, c, a):
    mod = p.amorcer
    if mod is None:
        print(f"Aucun amorçage dans le paquet « {p.package} » : rien à faire.")
        return 0
    mod.executer(c, a.dry_run)
    return 0


def _config(p):
    return pages.charger_config(p.racine / "widgets.json")


def _creer_page(p, c, a):
    if a.dry_run:
        print(f"[dry-run] page « {a.titre} » pour le widget « {a.widget} » (table {a.table}, accès {a.acces}).")
        return 0
    config = _config(p)
    pages.creer(c, config, a.widget, a.table, a.titre, a.acces)
    pages.ecrire_config(p.racine / "widgets.json", config)
    print(f"page « {a.titre} » prête pour le widget « {a.widget} ».")
    return 0


def _deployer(p, c, a):
    config, dossier = _config(p), p.racine / p.widgets_dir
    verifier = a.check or a.dry_run          # --dry-run compare sans rien écrire
    if p.design_system == "ui-kit":
        if not verifier:
            entree = config.get("widgets", {}).get(a.widget, {}).get("entree", a.widget)
            for nom, ko in build_uikit.construire(dossier, [entree]).items():
                print(f"  {nom} : {ko} Ko")
        code = build_uikit.deployer_uikit(c, config, a.widget, dossier, check=verifier)
    else:
        code = deployer.deployer(c, config, a.widget, dossier, check=verifier)
    return code if a.check or not a.dry_run else 0


def _pages_html(p):
    return sorted((p.racine / p.widgets_dir).glob("*.html"))


def _inliner(p, c, a):
    if p.design_system == "ui-kit":
        print("Profil ui-kit : le core est compilé par le build, rien à recopier.")
        return 0
    verifier = a.check or a.dry_run
    ok = inliner.inliner_tout(p.racine / p.core, _pages_html(p), check=verifier)
    return 0 if ok or not a.check and a.dry_run else 1


def _versions(p, c, a):
    sources = [p.racine / p.core, *_pages_html(p)]
    texte = next((s.read_text(encoding="utf-8") for s in sources
                  if s.exists() and versions.DEBUT in s.read_text(encoding="utf-8")), None)
    if texte is None:
        raise ValueError(f"Aucun journal des versions ({versions.DEBUT} … {versions.FIN}) dans "
                         f"{p.core} ni dans les pages de {p.widgets_dir}.")
    journal = versions.lire_journal(texte)
    touchees = versions.synchroniser(c, versions.lignes_changelog(journal), dry_run=a.dry_run)
    print(f"table CHANGELOG : {len(touchees)} version(s) à jour ou touchée(s) : {', '.join(touchees) or 'aucune'}.")
    a_jour = versions.ecrire_changelog(p.racine / "CHANGELOG.md", journal, check=a.dry_run)
    if a.dry_run and not a_jour:
        print("[dry-run] CHANGELOG.md serait réécrit.")
    return 0


# nom -> (fonction, besoin d'un client Grist)
COMMANDES = {"apply-schema": (_schema, True), "maj-formules": (_formules, True), "apply-acl": (_acl, True),
             "amorcer": (_amorcer, True), "creer-page": (_creer_page, True), "deployer": (_deployer, True),
             "inliner": (_inliner, False), "versions": (_versions, True)}


def _parser():
    commun = argparse.ArgumentParser(add_help=False)
    commun.add_argument("--dry-run", action="store_true", help="n'écrit rien")
    commun.add_argument("--doc", help="identifiant du document (défaut : GRIST_DOC_ID)")
    parser = argparse.ArgumentParser(prog="python -m grist_kit", description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="commande", required=True)
    for nom, aide in (("apply-schema", "crée les tables et colonnes manquantes"),
                      ("maj-formules", "réaligne formules et choix sur le schéma"),
                      ("apply-acl", "installe les règles d'accès"), ("amorcer", "charge les données de départ"),
                      ("creer-page", "crée la page d'un widget"), ("deployer", "dépose un widget dans Grist"),
                      ("inliner", "recopie le core dans les pages"), ("versions", "synchronise le journal des versions")):
        p = sub.add_parser(nom, parents=[commun], help=aide)
        if nom == "apply-acl":
            p.add_argument("--prune", action="store_true", help="retire les règles étiquetées devenues obsolètes")
        if nom == "creer-page":
            p.add_argument("widget")
            p.add_argument("table")
            p.add_argument("--titre", required=True)
            p.add_argument("--acces", choices=pages.ACCES, default="full")
        if nom == "deployer":
            p.add_argument("widget")
        if nom in ("deployer", "inliner"):
            p.add_argument("--check", action="store_true", help="compare sans écrire ; code 1 s'il y a un écart")
    return parser


def _client(args, racine):
    load_dotenv(racine / ".env")
    doc = args.doc or os.getenv("GRIST_DOC_ID")
    if not doc:
        raise ValueError("Document non précisé : renseigner GRIST_DOC_ID (dans .env) ou passer --doc <id>.")
    return GristClient(doc_id=doc)


def main(argv=None, racine=None, client=None) -> int:
    """Point d'entrée ; `racine` et `client` sont injectables (tests). Renvoie le code de sortie."""
    args = _parser().parse_args(argv)
    racine = Path(racine or Path.cwd())
    fonction, besoin_client = COMMANDES[args.commande]
    try:
        projet = charger_projet(racine)
        if besoin_client:
            client = client or _client(args, projet.racine)
            if args.doc:
                client.doc_id = args.doc
        return fonction(projet, client, args)
    except (GristErreur, ValueError, FileNotFoundError, ImportError) as e:
        print(f"Erreur : {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
