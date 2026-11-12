---
name: grist-agentic-stories
description: Découper un PRD ou un besoin en stories qu'un agent peut exécuter seul. Utiliser pendant le cadrage, avant /grist-stories-review ; pas pour les tickets d'une story.
---
# Découper en stories

Une story est une tranche livrable de bout en bout, assez précise pour qu'un agent la réalise sans deviner.

## Format d'une story

- **Id** `s<numéro>-<slug>` (`s03-declarer-une-absence`), repris tel quel dans les fichiers du pipeline et la branche.
- **Récit** : « En tant que <profil>, je veux <action> pour <bénéfice> ». Le profil vient de la matrice des profils du PRD.
- **Critères d'acceptation** : chacun devient un test. Écrire le résultat observable (« une demande valide est enregistrée et
  confirmée ; une demande invalide n'écrit rien »), jamais « ça marche ».
- **Notes pour l'agent** : tables et colonnes touchées, règles d'accès en jeu, widgets concernés, volumétrie, pièges connus.
  C'est le contexte qu'un humain devinerait et qu'un agent doit lire.
- **Dépendances** : les ids des stories qui doivent être livrées avant.
- **Complexité** de 1 à 5.

## Règles de découpe

1. Une story apporte une valeur à un profil. « Créer la table » n'est pas une story : la table naît dans la story qui en a besoin.
2. Dans un projet Grist, une story traverse en général quatre couches (schéma, règle d'accès, widget, recette). Si elle n'en touche qu'une,
   chercher quelle valeur utilisateur elle porte réellement.
3. Une règle d'accès est un critère, pas une story. Chaque profil du PRD qui touche la donnée a au moins un critère de refus.
4. Taille : tenir dans un cycle recherche → plan → exécution → revue → livraison. Un plan de plus de dix tâches annonce une story trop grosse.
5. Complexité 4 : nommer le risque dans les notes. Complexité 5 : découper avant d'aller plus loin.
6. Ordre exécutable de haut en bas : aucune story ne suppose un travail placé après elle.
7. Ce que le PRD déclare hors périmètre ne revient jamais en story.

## Exemple

Mauvais : « s01 — Mettre en place la base ». Aucune valeur, rien à tester, impossible à livrer seul.
Bon : « s01-deposer-une-demande — En tant qu'agent, je veux déposer une demande pour qu'un responsable la traite. »
Critères : une demande valide est enregistrée et confirmée ; une demande invalide affiche les erreurs et n'écrit rien ;
un agent d'une autre unité ne la voit pas.
