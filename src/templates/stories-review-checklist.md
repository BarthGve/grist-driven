# Revue des stories — <nom du produit>

> Relecture à contexte neuf de `docs/stories.md` contre `docs/prd.md`. Chaque point est classé critique, majeur ou mineur.

## Couverture
| Fonction du PRD | Story qui la livre | OK ? |
|---|---|---|
| <fonction> | <id> | ✅ / ❌ |

| Profil du PRD | Story qui le sert | OK ? |
|---|---|---|
| <profil> | <id> | ✅ / ❌ |

- [ ] Chaque fonction du périmètre est livrée par au moins une story
- [ ] Chaque profil d'utilisateurs est servi par au moins une story

## Périmètre
- [ ] Aucune story ne réintroduit un élément de la liste des exclusions
- [ ] Aucune story ne dépasse le périmètre

## Qualité des stories
- [ ] Chaque story est une tranche livrable de bout en bout, pas une couche technique
- [ ] Chaque critère d'acceptation peut devenir un test
- [ ] Une story qui touche aux droits a un critère par profil concerné
- [ ] Notes pour l'agent présentes et utiles
- [ ] Complexité notée ; aucun 5 non découpé ; chaque 4 nomme son risque

## La liste dans son ensemble
- [ ] Ordre exécutable : pas de cycle, pas de renvoi vers l'avenir
- [ ] Identifiants bien formés (`s<numéro>-<slug>`), uniques et stables
- [ ] Ni doublon ni recouvrement

## Constats
<une ligne par point : gravité — id de la story (ou « couverture ») — ce qui ne va pas>

## Verdict
Gravité max : <critique | majeur | mineur | aucune>
Stories prêtes : <oui | non>
