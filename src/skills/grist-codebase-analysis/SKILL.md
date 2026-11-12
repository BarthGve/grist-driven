---
name: grist-codebase-analysis
description: Analyser un projet existant (code, schéma Grist, widgets) pour en extraire les conventions avant d'y toucher. Utiliser pendant l'architecture, la recherche et la reprise d'un projet.
---
# Analyser un projet existant

Objectif : comprendre ce qui existe, puis écrire les conventions à suivre sous forme de règles.

## Déroulé

1. **Cartographier** : dossiers, points d'entrée, fichiers de configuration (`.grist-driven.json`, `AGENTS.md`), `schema.py`,
   `acl_rules.py`, `widgets.json`, dossier des widgets selon le profil (`widgets/` ou `widgets_ui/`), tests.
2. **Suivre une fonctionnalité de bout en bout** : une table, ses règles d'accès, son widget, son test. C'est ce parcours qui révèle les
   usages réels bien mieux qu'une documentation.
3. **Relever les régularités** : nommage, découpage du cœur JS, façon de poser une règle en double (formule et cœur), étiquettes de règles,
   gestion des erreurs, forme des tests.
4. **Repérer les points d'accroche** : où une nouvelle table, une nouvelle règle ou un nouveau widget se branche.
5. **Mesurer** ce qui compte pour un document vivant : volumétrie, formules qui relisent des familles de lignes (voir `grist-perf`).
6. **Rendre compte en règles** (« une règle d'accès = une étiquette et un test de refus »), pas en constats (« il y a des règles »).
   Ces règles alimentent `AGENTS.md` et `docs/architecture.md`.

## Principes

- Vérifier avant d'affirmer : ne citer un fichier, une fonction ou une signature qu'après l'avoir ouvert.
- Projet non vide : ce qui existe impose la pile et les patrons. S'y conformer ; ne proposer aucune réécriture.
- Projet vide : proposer deux ou trois options à partir des contraintes du PRD (profil de widgets, volumétrie), consigner le choix dans un ADR,
  ne rien créer avant confirmation.
- Lecture seule : l'analyse ne modifie ni le document Grist ni le dépôt.
