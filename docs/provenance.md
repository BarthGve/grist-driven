# Audit de provenance

Généré par `scripts/provenance.py` : chaque fichier de driven est comparé à chaque fichier du dernier
commit de Mike Codeur (killer-saas), après normalisation des préfixes `ks-`/`dm-`/`grist-`.
Seuil : 0.5. Le document ne cite que des chemins, jamais de contenu hérité.

## Résumé

- `reecrire` : 32
- `libre` : 24
- total : 56

## Fichiers

| Fichier driven | Rapport | Plus proche équivalent amont | Verdict |
|---|---|---|---|
| `templates/stories-review-checklist.md` | 0.97 | `src/templates/stories-review-checklist.md` | reecrire |
| `templates/research.md` | 0.97 | `src/templates/research.md` | reecrire |
| `skills/agentic-stories/SKILL.md` | 0.97 | `src/skills/agentic-stories/SKILL.md` | reecrire |
| `commands/dm-design-system.md` | 0.96 | `src/commands/ks-design-system.md` | reecrire |
| `hooks/pre-commit` | 0.95 | `src/hooks/pre-commit` | reecrire |
| `commands/dm-research.md` | 0.95 | `src/commands/ks-research.md` | reecrire |
| `templates/stories.md` | 0.95 | `src/templates/stories.md` | reecrire |
| `templates/adr.md` | 0.93 | `src/templates/adr.md` | reecrire |
| `templates/design-system.md` | 0.91 | `src/templates/design-system.md` | reecrire |
| `templates/architecture.md` | 0.91 | `src/templates/architecture.md` | reecrire |
| `skills/tdd-skill/SKILL.md` | 0.91 | `src/skills/tdd-skill/SKILL.md` | reecrire |
| `templates/design-screen.md` | 0.90 | `src/templates/design-screen.md` | reecrire |
| `templates/design-brief.md` | 0.89 | `src/templates/design-brief.md` | reecrire |
| `commands/dm-stories-review.md` | 0.88 | `src/commands/ks-stories-review.md` | reecrire |
| `skills/codebase-analysis/SKILL.md` | 0.81 | `src/skills/codebase-analysis/SKILL.md` | reecrire |
| `skills/stories-review/SKILL.md` | 0.78 | `src/skills/stories-review/SKILL.md` | reecrire |
| `commands/dm-design.md` | 0.74 | `src/commands/ks-design.md` | reecrire |
| `commands/dm-ship.md` | 0.74 | `src/commands/ks-ship.md` | reecrire |
| `templates/review-checklist.md` | 0.73 | `src/templates/review-checklist.md` | reecrire |
| `agents/worktree-manager.md` | 0.72 | `src/agents/worktree-manager.md` | reecrire |
| `agents/implementer.md` | 0.69 | `src/agents/implementer.md` | reecrire |
| `commands/dm-plan.md` | 0.69 | `src/commands/ks-plan.md` | reecrire |
| `templates/prd.md` | 0.67 | `src/templates/prd.md` | reecrire |
| `agents/stories-reviewer.md` | 0.63 | `src/agents/stories-reviewer.md` | reecrire |
| `hooks/pre-push` | 0.63 | `src/hooks/pre-push` | reecrire |
| `agents/reviewer.md` | 0.63 | `src/agents/reviewer.md` | reecrire |
| `commands/dm-stories.md` | 0.61 | `src/commands/ks-stories.md` | reecrire |
| `commands/dm-prd.md` | 0.61 | `src/commands/ks-prd.md` | reecrire |
| `commands/dm-architect.md` | 0.56 | `src/commands/ks-architect.md` | reecrire |
| `commands/dm-review.md` | 0.52 | `src/commands/ks-review.md` | reecrire |
| `skills/quality-bar/SKILL.md` | 0.52 | `src/skills/review-antihallu/SKILL.md` | reecrire |
| `commands/dm-execute.md` | 0.50 | `src/commands/ks-execute.md` | reecrire |
| `templates/plan.md` | 0.49 | `src/templates/plan.md` | libre |
| `hooks/dm-gate.sh` | 0.47 | `src/hooks/ks-gate.sh` | libre |
| `templates/design-path-brief.md` | 0.37 | `src/commands/ks-design.md` | libre |
| `commands/dm-help.md` | 0.34 | `src/commands/ks-help.md` | libre |
| `commands/dm-status.md` | 0.32 | `src/commands/ks-status.md` | libre |
| `commands/dm-orchestrator.md` | 0.26 | `src/commands/ks-orchestrator.md` | libre |
| `AGENTS.md` | 0.21 | `src/AGENTS.md` | libre |
| `commands/dm-docs.md` | 0.20 | `src/commands/ks-plan.md` | libre |
| `lib/dm-quota.sh` | 0.16 | `src/hooks/pre-push` | libre |
| `commands/dm-feature.md` | 0.15 | `src/commands/ks-stories-review.md` | libre |
| `lib/dm-port.sh` | 0.14 | `src/hooks/pre-commit` | libre |
| `commands/dm-init.md` | 0.12 | `src/commands/ks-stories-review.md` | libre |
| `commands/dm-continue.md` | 0.11 | `src/commands/ks-prd.md` | libre |
| `lib/dm-wiki.sh` | 0.11 | `src/hooks/ks-gate.sh` | libre |
| `commands/dm-release.md` | 0.10 | `src/commands/ks-ship.md` | libre |
| `lib/dm-config.sh` | 0.10 | `src/hooks/ks-gate.sh` | libre |
| `lib/dm-version.sh` | 0.09 | `src/hooks/ks-gate.sh` | libre |
| `profiles.txt` | 0.09 | `src/hooks/pre-push` | libre |
| `templates/design-path-canvas.md` | 0.09 | `src/commands/ks-design.md` | libre |
| `templates/product-doc.md` | 0.09 | `src/templates/design-brief.md` | libre |
| `permissions.txt` | 0.09 | `src/hooks/pre-push` | libre |
| `lib/dm-witness.sh` | 0.07 | `install.sh` | libre |
| `lib/dm-init.sh` | 0.07 | `src/hooks/ks-gate.sh` | libre |
| `lib/dm-board.sh` | 0.07 | `src/hooks/ks-gate.sh` | libre |
