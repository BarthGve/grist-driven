---
description: Ajouter une évolution à un produit déjà livré — la cadrer, amender le PRD, ajouter des stories au backlog. À lancer après la v1 quand un nouveau besoin arrive ; pas pour le premier PRD (/grist-prd) ni pour un défaut dans une story existante.
argument-hint: <slug ou courte description de l'évolution>
allowed-tools:
  - Read
  - Glob
  - Grep
  - Write
  - Edit
  - Bash
  - AskUserQuestion
  - Agent
---
# grist-feature — Une évolution sur un produit en service

Évolution visée : $ARGUMENTS

Le produit est cadré, construit, livré. Cette commande cadre, amende, découpe et rend la main au flux par story ; elle n'écrit aucun code d'application.

## Prérequis
`docs/prd.md` et `docs/stories.md` doivent exister. Sinon : « Pas de PRD : /grist-prd (ou /grist-continue sur un dépôt existant) », ou « Produit pas encore découpé : /grist-stories ».

## 1. Cadrer (une question à la fois)
Le besoin et son déclencheur ; le périmètre, ce que l'évolution apporte et ce qui reste dehors ; les profils d'utilisateurs concernés et la volumétrie attendue sur les tables touchées. Relire la liste « hors périmètre » du PRD : si l'évolution y figure, exiger ce qui a changé depuis. Une fonction peut sortir de cette liste, pas en silence. Rien n'est rempli sans validation.

## 2. Impact sur l'architecture (une grille, pas une impression)
Parcourir chaque point et noter ceux qui sont touchés :
- une table ou une colonne de plus, ou la migration de données existantes ;
- un profil ou une règle d'accès nouvelle (ligne de la matrice ACL) ;
- un widget de plus, ou un changement de profil de design system ;
- une règle posée en double (formule de colonne et widget) ;
- une dépendance, un service externe ou un second document Grist.

Au moins un oui : passage par `/grist-architect` (nouvel ADR, sections mises à jour) avant `/grist-plan`. Aucun : direct à `/grist-research`. La réponse est consignée dans l'amendement.

## 3. Amender le PRD
Mettre à jour le corps de `docs/prd.md` (le tableau du périmètre gagne la fonction, la liste hors périmètre la perd si elle en sort), puis ajouter en tête de la section `## Amendements` (la créer en fin de fichier si elle manque) :

    ### <AAAA-MM-JJ> — v<version visée> — <slug>
    **Entre dans le périmètre :** …
    **Sorti de la liste hors périmètre ?** non | oui — <justification>
    **Stories :** <identifiants>

## 4. Découper, en AJOUTANT
Appliquer le skill `grist-agentic-stories`. Repérer le plus grand `s<NN>` de `docs/stories.md` et poursuivre la suite : les identifiants nomment des fichiers et des branches vivantes, une collision casse tout le cycle. Ajouter les stories à la fin de `docs/stories.md`, sans jamais écraser le fichier : les stories qui s'y trouvent sont du travail livré.

## 5. Issues parent
Une par nouvelle story, en `backlog` : `bash .grist/lib/grist-board.sh issue-create-us <story> "<titre>" <fichier-corps>` (sans effet si le titre `[<story>]` existe déjà).

## 6. Relecture à contexte neuf
Appeler l'outil Agent avec subagent_type: stories-reviewer, en lui demandant de relire les nouvelles stories contre `docs/prd.md` (amendements compris) et contre les stories déjà livrées : doublon avec du livré, dépendance à du non livré, contradiction avec le comportement en production. Il termine par `Gravité max : …` et `Stories prêtes : oui|non`. Écrire le rapport dans `docs/reviews/features/<slug>.md` ; **ne pas toucher à `docs/reviews/stories.md`**, signal de cadrage du produit entier que `/grist-status` et `/grist-research` lisent. Porte souple, comme la relecture initiale.

## 7. Commit
Sur `next` : `📝 DOCS: évolution <slug>`.

Terminer par : « Évolution cadrée (<identifiants>). Suite : /grist-architect » si l'architecture est touchée, sinon « Suite : /grist-research <story> ».
