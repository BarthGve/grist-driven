# Architecture — <nom du produit>

> Cinq sections propres à Grist, puis l'ossature commune. Chaque règle de droits ou de calcul décrite ici a son test dans le projet.

## Pile et structure
<Hôte Grist, version, profil de widgets (`dsfr` ou `ui-kit` d'après `.grist-driven.json`), dossiers clés du dépôt et leur rôle, conventions de nommage.>

## Modèle de données
Source de vérité : `schema.py`.

| Table | Rôle | Colonnes de données | Colonnes calculées (formule) | Références |
|---|---|---|---|---|
| <Table> | <rôle> | <col : type> | <col : idée de la formule> | <vers quelle table> |

Pour chaque table : clé naturelle éventuelle, volume attendu (reprendre le PRD), colonnes qui ne doivent jamais devenir des formules.

## Matrice ACL (profil × table × droit)
Source de vérité : `acl_rules.py`. Droits : **L** lecture · **C** création · **M** modification · **S** suppression ; `-` = aucun. Une cellule peut porter une condition.

| Table | <profil 1> | <profil 2> | <profil 3> |
|---|---|---|---|
| <Table> | L C M | L | - |

- Colonnes à accès restreint : <table.colonne → profils autorisés>.
- Cas refusés à tester pour chaque profil : <liste>.
- Étiquette des règles : `[<app>:<ressource>#<n>]`.

## Inventaire des widgets
Source de vérité : `widgets.json`.

| Widget | Page Grist | Tables lues | Tables écrites | Profils concernés | Entrée |
|---|---|---|---|---|---|
| <widget> | <page> | <tables> | <tables> | <profils> | <fichier HTML `dsfr` ou entrée React `ui-kit`> |

## Règles en double (formule Grist + JS)
Une règle appliquée à deux endroits (la formule qui la calcule dans Grist, le code du widget qui la montre ou la vérifie) est listée ici avec ses deux implémentations et ses deux tests.

| Règle | Formule Grist (table.colonne) | Code JS (fichier, fonction) | Test des deux côtés |
|---|---|---|---|
| <règle métier> | <emplacement> | <emplacement> | <tests> |

## Plan de déploiement
Ordre : `apply-schema` → `maj-formules` → `apply-acl` → `amorcer` → `creer-page` → `deployer`, puis contrôle final (`--check`).

- Document cible et hôte : <référencés par variable d'environnement, jamais en clair>.
- Données d'amorçage : <référentiels à poser>.
- Version et journal des changements : <règle de bump>.
- Recette en réel : un essai par profil de la matrice (`?aclAsUser_=<adresse>`).
- Retour arrière : <procédure>.

## Points d'intégration
<authentification, courriels, imports, services externes.>

## Ergonomie
<parcours et écrans clés, détaillés par `/grist-design` quand c'est utile.>
