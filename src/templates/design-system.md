# Design system — <produit>

> Le contenu dépend du choix consigné dans `.grist-driven.json` (`design_system`). `/grist-design-system` ne garde que la variante retenue
> et supprime l'autre, ainsi que ces consignes.

## Variante `dsfr`

Widgets : un fichier HTML autonome par widget, `core.js` inliné entre marqueurs, tests `node:test` du cœur. Aucun Node pour déployer.

### Version
DSFR <version exacte, ex. 1.14.x>. Jamais une plage : la version exacte garde le cache du navigateur utile.

### Jetons
- Couleurs : <jetons `--background-*`, `--text-*`, `--border-*` utilisés>
- Typographie : <échelle utilisée>
- Espacements : <échelle `fr-m*` et `fr-p*`>

### Composants disponibles
| Composant | Classe | Usage |
|---|---|---|
| <Bouton> | `fr-btn` | <…> |
| <Champ> | `fr-input` | <…> |
| <Tableau> | `fr-table` | <…> |

### Règles de feuilles de style et de script
- Ordre de chargement des feuilles : <ordre>
- Interdits : attribut `style=""`, `innerHTML` sur une donnée, `alert()`.
- Accessibilité : <libellés, focus visible, contrastes, annonces pour les états>

## Variante `ui-kit`

Widgets : application React/TypeScript construite par Vite (`vite-plugin-singlefile`), une entrée par widget, sortie `dist/<entrée>.html`.
Composants issus de La Suite ui-kit (`@gouvfr-lasuite/ui-components`).

### Version
Paquet `@gouvfr-lasuite/ui-components` en version exacte : <version>. Node ≥ 20 pour construire.

### Jetons
- Couleurs et typographie : <jetons du thème du kit repris tels quels>
- Espacements et rayons : <échelle>

### Composants disponibles
| Composant | Import | Usage |
|---|---|---|
| <Button> | `@gouvfr-lasuite/ui-components` | <…> |
| <Input> | idem | <…> |
| <DataGrid> | idem | <…> |

### Règles de build et de chargement
- Bundle déposé compressé (gzip + base64), sous la limite de l'API Grist ; taille mesurée après chaque build.
- Chargement différé des écrans lourds ; cache des lectures par `react-query`.
- Interdits : composant maison qui duplique un composant du kit, couleur hors thème.
- Accessibilité : <vérifications attendues du kit, ce qui reste à faire à la main>

## Commun aux deux variantes

### Motifs d'interface
- Formulaires : <…>
- États (vide / chargement / erreur / succès / accès refusé) : <…>
- Retours à l'utilisateur (message en ligne, notification) : <…>

### À faire / à éviter
- ✅ <…>
- ❌ <…>
