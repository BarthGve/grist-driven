"""Évalue les règles d'accès du projet comme Grist, hors du document.

Pour une colonne, les ressources sont consultées de la plus précise à la plus générale (colonnes citées,
table entière, puis toutes les tables) ; dans une ressource, par `rulePos` croissant. Chaque droit
(C, R, U, D) est tranché par la première règle qui s'applique et le fixe ; sans règle, il est refusé.
`user.<Nom>` est la fiche de la table déclarée dans `USER_ATTRIBUTES` du module de règles dont la colonne
`lookupColId` égale l'adresse de connexion (ligne « fausse » si aucune).

Permissions : `all`, `none`, ou un ou plusieurs groupes signés (`+R`, `-CUD`, `+R-CUD`, `+CR-UD`).

Structure du document : droit `S`, évalué sur la ressource `*SPECIAL` / `SchemaEdit` (`permis(..., "S")`, la table est
ignorée). Écrire la règle avec `permissionsText` `+S` ou `-S`. Sans règle applicable, Grist laisse la structure aux
propriétaires et aux éditeurs (`acces` `owners` ou `editors`) : le simulateur fait de même.
"""

import re

DROITS = "CRUDS"


class Utilisateur:
    def __init__(self, base, regles_module, email, acces="editors"):
        self.Email, self.Access = email, acces
        for attribut in getattr(regles_module, "USER_ATTRIBUTES", []):
            fiche = base[attribut["tableId"]].lookupOne(**{attribut["lookupColId"]: getattr(self, attribut["charId"], email)})
            setattr(self, attribut["name"], fiche)


def _bits(texte):
    if texte in ("all", "none"):
        return {d: texte == "all" for d in DROITS}
    bits = {}
    for signe, lettres in re.findall(r"([+-])([A-Z]*)", texte):
        bits.update({d: signe == "+" for d in lettres if d in DROITS})
    return bits


def _ressources(regles_module, table, colonne):
    liste = regles_module.RESOURCES
    precises = [r for r in liste if r["tableId"] == table and r["colIds"] not in ("*",)
                and (colonne is not None and colonne in r["colIds"].split(","))]
    tables = [r for r in liste if r["tableId"] == table and r["colIds"] == "*"]
    defaut = [r for r in liste if r["tableId"] == "*"]
    return precises + tables + defaut


def permis(base, regles_module, email, table, droit, rec=None, apres=None, colonne=None, acces="editors"):
    """Le droit `droit` (C, R, U, D ou S) est-il accordé à `email` ? `rec` : ligne actuelle ; `apres` : état résultant.

    `S` : modifier la structure (règle spéciale `SchemaEdit`) ; `table` est alors ignorée."""
    if droit == "S":
        table, colonne = "*SPECIAL", "SchemaEdit"
    vide = base.ligne(table, 0)
    contexte = {"user": Utilisateur(base, regles_module, email, acces), "rec": rec if rec is not None else vide,
                "newRec": apres if apres is not None else vide}
    for ressource in _ressources(regles_module, table, colonne):
        regles = sorted((r for r in regles_module.RULES if r["resource_key"] == ressource["key"]), key=lambda r: r["rulePos"])
        for regle in regles:
            bits = _bits(regle["permissionsText"])
            if droit in bits and (not regle["aclFormula"] or eval(regle["aclFormula"], {}, contexte)):  # noqa: S307 — règles du projet
                return bits[droit]
    return droit == "S" and acces in ("owners", "editors")
