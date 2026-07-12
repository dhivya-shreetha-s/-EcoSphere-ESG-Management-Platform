## EcoSphere Pull Request

### Phase / Branch
<!-- e.g. Phase 1 — Foundation, feature/phase1-scaffold -->

### What this PR does
<!-- Concise description of what changed and why -->

### Checklist
- [ ] Module still installs cleanly on a fresh DB (`odoo-bin -i ecosphere --stop-after-init`)
- [ ] Tests pass (`--test-tags ecosphere`)
- [ ] Three test logins (employee / manager / admin) all see correct scoped content
- [ ] RBAC spot-check: employee ORM search cannot return another employee's `esg.score`
- [ ] No hardcoded data, mock JSON, or placeholder numbers on any visible screen
- [ ] No secrets in this diff (search: `grep -r "xai\|grok\|api_key" --include="*.py" .`)
- [ ] `.env` is NOT in this diff
- [ ] Commit messages follow `type(scope): description` convention
- [ ] Phase N walkthrough updated (if this closes a phase)

### Screenshots / recordings (if UI changes)
<!-- Paste screenshots or link to recording -->

### Open questions / blockers
<!-- Anything the reviewer needs to decide or unblock -->
