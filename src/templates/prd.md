# PRD — <nom du produit>

## Mode
<nouveau projet | reprise>
<!-- nouveau projet : on part d'un besoin ; reprise : un classeur Grist existe déjà et on le fait évoluer. -->

## Point de départ
<nouveau projet : le besoin et son déclencheur. Reprise : le classeur existant (nom, usage actuel, ce qui fonctionne, ce qui coûte du temps ou des erreurs). Aucun identifiant de document ici.>

## Problème
Quel besoin, pour qui, pourquoi maintenant.

## Profils d'utilisateurs
| Profil | Effectif estimé | Ce qu'il fait | Ce qu'il ne doit jamais voir ni modifier |
|---|---|---|---|
| <profil> | <n> | <tâches principales> | <limite de droits> |

Un profil ici deviendra une ligne de la matrice ACL de `docs/architecture.md`.

## Volumétrie
| Donnée | Volume aujourd'hui | Volume à 12 mois | Rythme d'écriture |
|---|---|---|---|
| <table ou flux> | <n lignes> | <n lignes> | <par jour / par import> |

Utilisateurs simultanés attendus : <n>. Une table au-delà de quelques milliers de lignes impose pagination et formules sobres (skill `grist-perf`).

## Périmètre
### Dans le périmètre
| Fonction | Complexité (1-5) | Justification |
|---|---|---|
| <fonction> | <n> | <pourquoi ce score> |

Échelle : 1 saisie ou liste simple · 2 formulaire avec règles de validation · 3 plusieurs états ou calculs croisés · 4 import/export, droits par profil, rapprochement de sources · 5 volumétrie extrême, migration lourde, système externe. Un 5 est candidat à l'exclusion, sauf s'il est la raison d'être du produit.

### Hors périmètre (liste des exclusions)
<ce qu'on écarte volontairement, sans rien omettre : c'est cette liste qui borne le périmètre.>

### Ce qui fait la différence
<ce que le produit apporte de mieux que la situation actuelle (tableur, circuit papier ou outil précédent).>

## Contraintes
Techniques (version de Grist, hôte), de calendrier, réglementaires (données personnelles, accessibilité), dépendances.

## Critères de réussite
<résultats mesurables sur les fonctions du périmètre : temps de saisie, taux d'erreur, délai de traitement.>

## Amendements
<Une entrée par fonction ajoutée après la première version, la plus récente en haut. Le corps du PRD décrit le produit d'aujourd'hui ; cette section dit comment on y est arrivé.>

### <AAAA-MM-JJ> — v<version cible> — <slug>
**Entre dans le périmètre :** <ce que la fonction ajoute, en une ou deux lignes>
**Retiré des exclusions ?** <non | oui — ce qui a changé depuis la décision d'exclure>
**Stories :** <s07-…, s08-…>
