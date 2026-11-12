---
description: Cadrer le produit Grist (le quoi et le pourquoi) dans docs/prd.md, en nouveau projet ou en reprise d'un classeur existant. À lancer en premier, une fois par produit ; pas pour une évolution d'un produit livré (/grist-feature) ni pour adopter un dépôt déjà en cours (/grist-continue).
argument-hint: <idée du produit ou nom du classeur existant>
allowed-tools:
  - Read
  - Write
  - Bash
  - AskUserQuestion
---
# grist-prd — Cadrage du produit

Sujet : $ARGUMENTS

Gabarit de sortie : `templates/prd.md`. Rien n'y est rempli sans ta validation.

## Deux modes, et seulement deux
- **nouveau projet** : on part d'un besoin, aucun classeur n'existe encore.
- **reprise** : un classeur Grist tourne déjà et on le fait évoluer. S'il existe un `docs/onboarding.md`, proposer ce mode par défaut.

Première question, toujours : quel mode ? Ne pas la sauter.

## Questions, une à la fois
1. **Point de départ.** Nouveau projet : le besoin et ce qui le déclenche. Reprise : le classeur actuel (usage, ce qui marche, ce qui coûte du temps ou des erreurs). Aucun identifiant de document dans le PRD.
2. **Problème** : quel besoin, pour qui, pourquoi maintenant.
3. **Profils d'utilisateurs** : un tableau, un profil par ligne, avec ce qu'il fait et ce qu'il ne doit jamais voir ni modifier. Ce tableau nourrira la matrice ACL de `/grist-architect` : le détailler maintenant évite de le refaire.
4. **Volumétrie** : nombre de lignes par table principale aujourd'hui et dans deux ans, rythme d'écriture, nombre d'utilisateurs simultanés. Au-delà de quelques dizaines de milliers de lignes, le dire noir sur blanc : les widgets et les formules devront être pensés en conséquence.
5. **Périmètre** : chaque fonction retenue reçoit une complexité de 1 à 5 (échelle du gabarit) ; un 4 ou un 5 doit justifier sa place. Ce qui reste dehors va dans la section « hors périmètre », qui sert de garde-fou contre l'élargissement.
6. **Reprise seulement** : le classeur existant est dans le périmètre par définition ; lire `docs/onboarding.md` s'il existe et ne reposer que les questions sans réponse.
7. **Angle** : ce que le produit fait mieux ou autrement que l'existant.
8. **Contraintes et critères de réussite** : hébergement (instance Grist, DSFR ou ui-kit d'après `.grist-driven.json`), échéances, critères mesurables sur les fonctions du périmètre.

## Sortie
Écrire `docs/prd.md` à partir du gabarit et le commiter sur la branche par défaut (`📝 DOCS: prd`).

Terminer par : « PRD prêt dans docs/prd.md. Suite : /grist-init »
