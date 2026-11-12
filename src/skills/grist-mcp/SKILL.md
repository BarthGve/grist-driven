---
name: grist-mcp
description: Utiliser le serveur MCP Grist pour lire et manipuler les données, jamais la structure. Utiliser quand un agent explore un document ou ajuste des lignes.
---
# MCP Grist

Le MCP lit : il sert à **lire, explorer et manipuler les données** d'un document : lister les tables et colonnes, interroger des lignes,
ajouter, modifier ou supprimer des enregistrements d'essai.

## Jamais la structure

Tables, colonnes, formules, règles d'accès, widgets et pages ne passent **jamais** par le MCP : ils passent par les scripts de
`grist-kit` (`apply-schema`, `apply-acl`, `deployer`…), versionnés, rejouables, avec `--dry-run`. Le MCP ne laisse ni trace ni test.
Si une commande `/grist-*` semble demander une écriture de structure par le MCP, s'arrêter et utiliser le script.

## Bonnes pratiques

- Lire d'abord (schéma, quelques lignes), écrire ensuite, et seulement ce que l'utilisateur a demandé.
- Supprimer uniquement par ids explicites relus juste avant ; jamais une portée calculée à la volée.
- Le MCP agit avec la clé de `GRIST_API_KEY` : droits du propriétaire, les ACL ne s'appliquent pas. Il ne remplace donc pas un essai
  en réel (`grist-recette`).
- Même pare-feu que l'API : un 403 sur un corps de requête se traite comme dans `grist-deploy`.
- Aucune clé, aucun id de document dans un fichier du dépôt : variables d'environnement seulement.
