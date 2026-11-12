# Revue — Ticket <story>/<ticket>

> Revue à contexte neuf. Chaque point est classé critique, majeur ou mineur.
> Rapport : `docs/reviews/<story>/<ticket>.md`. Un tour est ajouté par `/grist-review`, jamais de tour modifié.
> Seul le verdict du dernier tour compte.

## Tour <n> — <aaaa-mm-jj>

Diff relu : `git diff next...feature/<story>/<ticket>` au commit `<sha court>`

### Conformité au plan
- [ ] Le code fait ce que dit le plan, rien de plus
- [ ] Les interdits de l'exécution sont respectés, chacun vérifié et nommé

### Anti-hallucination
- [ ] Aucune fonction, colonne, route ou import inventé (chacun ouvert et vérifié)
- [ ] Aucune valeur ou logique plausible mais fausse
- [ ] Le code fait ce qu'il annonce

### Grist
- [ ] Structure (schéma, ACL, widgets) écrite par les scripts du kit, jamais par le MCP
- [ ] `--dry-run` lu avant toute application ; aucune écriture réelle imprévue
- [ ] Chaque règle d'ACL a son test, refus compris ; pas de `rec.X.Y` ; cas `newRec` couverts
- [ ] Chaque règle en double a ses deux implémentations et ses deux tests
- [ ] Colonnes de données ajoutées à une table existante : nature déclarée (`isFormula`)

### Sécurité
- [ ] Aucune injection (HTML, formule, commande) à partir d'une saisie non fiable
- [ ] Droits décidés côté ACL, pas seulement masqués dans le widget
- [ ] Aucun secret ni identifiant de document dans le code, les journaux ou les bundles
- [ ] Aucune donnée personnelle dans les journaux

### Factorisation
- [ ] Une règle métier, un endroit (hors les doubles déclarés)
- [ ] Aucune abstraction spéculative

### Performance
- [ ] Un seul chargement des données par widget, pagination au-delà de 50 lignes
- [ ] Pas de formule coûteuse sur grosse table (`lookupRecords` en colonne, `NOW()`) sans mesure
- [ ] Écritures groupées ; bundle `ui-kit` sous la limite après gzip

### Conformité aux règles
- [ ] Conventions du projet respectées (`AGENTS.md`)
- [ ] Aucun ADR accepté contredit (`docs/decisions/`)
- [ ] Design system respecté : composants et jetons de `docs/design-system.md`, écran conforme à `docs/designs/<id>.md`

### Tests
- [ ] Vérifications complètes relancées par le relecteur, vertes (résultat repris ou nouvelle exécution : dire laquelle)
- [ ] Les assertions fixent les critères d'acceptation
- [ ] Morsure prouvée par neutralisation : <ce qui a été neutralisé> → <N> tests rouges, rétabli (`git diff --exit-code` propre)
- [ ] Tests devenus redondants nommés et retirés, ou leur maintien justifié

### Régressions
- [ ] Aucun effet sur les chemins existants

### Constats précédents
<tour 1 : omis. Ensuite : chaque critique ou majeur du tour précédent, réglé ou non, et où>

### Constats
<une ligne par point : gravité — fichier — ce qui ne va pas>

### Non vérifié
<ce que cette revue n'a pas pu contrôler et pourquoi : pas de document Grist réel, pas de navigateur, profil jamais essayé.
Nommer les gestes précis à faire : page à ouvrir, profil à simuler avec `?aclAsUser_=`, bouton à cliquer. Une liste vide revient à dire « tout vu ».>

### Verdict
Gravité max : <critique | majeur | mineur | aucune>
Livraison autorisée : <oui | non>
