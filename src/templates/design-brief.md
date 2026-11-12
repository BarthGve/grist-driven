# Brief de design — Story <id>

> Document autonome à transmettre à un outil de design externe : story, écrans, contraintes, livrable attendu.
> Dans Claude Code, préférer le canevas natif de `/grist-design`, sans aller-retour.

## Story
<rappel et critères d'acceptation>

## Profils
<qui utilisera ces écrans, avec ses droits : ce que chaque profil voit et ne voit pas>

## Écrans à produire
### <nom de l'écran>
- But : <…>
- Structure : <zones, hiérarchie>
- Contenu : <champs, libellés, données affichées, volume typique de lignes>
- Actions : <boutons, interactions>
- États : vide / chargement / erreur / succès / accès refusé : <ce que montre chacun>

## Contraintes du design system (non négociables)
- Famille : <`dsfr` ou `ui-kit`, d'après `docs/design-system.md`>
- Jetons : <couleurs, typographie, espacements, repris du document>
- Composants à réutiliser : <composant : usage>
- À faire / à éviter : <repris du document>

Aucun composant, jeton ni couleur en dehors de cette liste. L'écran vit dans un widget Grist : largeur variable, pas de navigation propre.

## Hors périmètre
<ce qu'il ne faut pas dessiner>

## Livrable attendu
Une maquette HTML statique par écran (basse fidélité acceptée), avec les seuls jetons ci-dessus. Rapporter l'export : il sera rangé dans `docs/designs/<id>.html`.
