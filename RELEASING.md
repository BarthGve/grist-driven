# Publier grist-driven

Pré-1.0 : le **mineur** peut changer l'interface d'installation (drapeaux, chemins posés), le **patch** jamais.
La version vit dans `VERSION` ; `packages/grist-kit/pyproject.toml` doit porter la même.

## 1. Vérifier

```bash
python -m pytest packages/grist-kit tests -q
bash tests/installer/run.sh
bash tests/e2e/test_init_complet.sh
python scripts/provenance.py src <dépôt amont> /tmp/provenance.md   # similarité maximale < 0,5
git status --short                                                  # propre
```

Relire aussi le dépôt : aucun reste de driven (`dm-`, `ks-`, `.dm/`), aucun nom de client, aucun identifiant de
document ni clé (dépôt public).

## 2. Bumper (sauf pour la 0.1.0, déjà à la bonne version)

```bash
bash src/lib/grist-version.sh bump minor    # ou major / patch ; aligne pyproject.toml
```

## 3. Remplir le changelog

Écrire la section de la version dans `CHANGELOG.md` : ce que lit l'utilisateur, pas les messages de commit.
Le hook de poussée vers `main` refuse une version absente du changelog.

## 4. Taguer et publier

Dépôt, organisation et tag sont ceux de `GRIST_KIT_SPEC_DEFAUT` (`src/lib/scaffold.sh`) : les ajuster avant le tag
si le dépôt public porte un autre nom.

```bash
ver=$(cat VERSION)
git commit -am "🔖 RELEASE: ${ver}"          # si bump ou changelog modifiés
git tag "v${ver}"
git push origin main --tags
gh release create "v${ver}" --title "v${ver}" --notes-file <(sed -n "/^## ${ver}/,/^## /p" CHANGELOG.md | sed '$d')
```

La publication reste manuelle : aucun déploiement automatique.
