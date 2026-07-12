# EcoSphere for Odoo
### AI-powered, ERP-native ESG Scoring & Sustainability Intelligence
**Odoo Hackathon** — Team EcoSphere

---

## Quick Links
- [Architecture Overview](#architecture-overview)
- [Local Setup](#local-setup)
- [Three Test Logins](#three-test-logins-definition-of-done)
- [Running Tests](#running-tests)
- [Installed-App Detection](#installed-app-detection)
- [Branch Strategy](#branch-strategy)
- [Judge FAQ](#judge-faq)

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                       EcoSphere Module                       │
│                                                             │
│   Employee Dashboard  Manager Dashboard  Admin Dashboard    │
│         (Phase 4)          (Phase 4)        (Phase 4)       │
│              │                  │                │          │
│              └──────────────────┼────────────────┘          │
│                                 │                           │
│                    ONE SHARED ENGINE                         │
│   ┌────────────────────────────────────────────────────┐    │
│   │  Scoring Engine  │  Alert Engine  │  AI Service   │    │
│   │   (Phase 2)      │  (Phase 3)     │  (Phase 3)    │    │
│   └────────────────────────────────────────────────────┘    │
│                         │                                   │
│                   Data Models (Phase 1)                      │
│   esg.score │ esg.alert │ esg.recommendation │ esg.goal     │
│   esg.csr.event │ esg.xp.ledger │ esg.ai.log │ ...          │
│                         │                                   │
│              Native Odoo Models (read-only)                  │
│   hr.employee │ hr.department │ hr.attendance │ fleet.* ...  │
└─────────────────────────────────────────────────────────────┘

Role-scoped access enforced at ORM level (record rules in security/esg_security.xml)
```

**Key architectural decision:** Build the engine once; each dashboard is a thin,
role-filtered view. Never build three parallel scoring engines.

---

## Local Setup

### Prerequisites
| Requirement | Version |
|---|---|
| Python | ≥ 3.10 |
| PostgreSQL | ≥ 14 |
| Odoo | 19.x (Community or Enterprise) |
| Git | any recent |

### Step-by-step

```bash
# 1. Clone the repo
git clone https://github.com/your-org/ecosphere.git
cd ecosphere

# 2. Create your .env from the template (NEVER commit .env)
cp .env.example .env
# Edit .env and fill in your GROK_API_KEY

# 3. Create the development database
createdb ecosphere_dev

# 4. Copy and configure Odoo config
cp odoo.conf.example odoo.conf
# Edit odoo.conf: set db_name, db_user, db_password, addons_path

# 5. Install the module on a fresh database
python odoo-bin -c odoo.conf -d ecosphere_dev -i ecosphere --stop-after-init

# 6. Start the dev server
python odoo-bin -c odoo.conf -d ecosphere_dev

# 7. Open http://localhost:8069 and log in with an admin account
#    Then verify the three test logins (see below)
```

> **Windows note:** Use `python` instead of `python3`. On WSL, standard Linux paths apply.

---

## Three Test Logins — Definition of Done

After install, these accounts exist. Use them in **every phase's** DoD verification:

| Role | Login | Password |
|---|---|---|
| Employee | `esg_emp_test@example.com` | `EcoSphereEmp2024!` |
| Manager | `esg_mgr_test@example.com` | `EcoSphereMgr2024!` |
| Admin | `esg_admin_test@example.com` | `EcoSphereAdm2024!` |

⚠️ **Change these passwords before any staging/public deployment.**

### RBAC spot-check (run this manually after every phase):
```python
# In Odoo shell (python odoo-bin shell -c odoo.conf -d ecosphere_dev):
# Log in as the employee user and try to read another employee's score:
emp_user = env['res.users'].search([('login', '=', 'esg_emp_test@example.com')])
scores = env['esg.score'].with_user(emp_user).search([])
print("Scores visible to employee:", scores)
# Expected: only their own score (or empty if none created yet)
```

---

## Running Tests

```bash
# Via Odoo test runner (recommended):
python odoo-bin -c odoo.conf -d ecosphere_test \
  --test-enable --test-tags ecosphere \
  --stop-after-init

# Tests run:
#   tests/test_install.py — smoke: seed data, model tables, hr.department extension
#   tests/test_security.py — RBAC: cross-employee ORM isolation
```

---

## Installed-App Detection

EcoSphere auto-detects which optional native Odoo apps are installed via
`esg.data.source.installed` (computed field) and logs results at startup.

To check manually in the Odoo shell:
```python
env['ir.module.module'].search([
    ('name', 'in', [
        'hr_attendance', 'hr_holidays', 'hr_payroll',
        'fleet', 'account', 'stock', 'project'
    ]),
    ('state', '=', 'installed')
]).mapped('name')
```

The Phase 2 scoring engine reads `esg.data.source.installed` to decide whether
to run live queries or compute lightweight proxies for environmental metrics.

---

## Branch Strategy

```
main           ← protected; merge via PR only; production-ready at all times
develop        ← integration branch; all phase branches merge here first

feature/phase1-scaffold          (this branch)
feature/phase2-scoring
feature/phase3-ai
feature/phase4-shared-components ← MUST land before the three dashboard branches
feature/phase4-emp-dash
feature/phase4-mgr-dash
feature/phase4-admin-dash
feature/phase5-gamification
feature/phase6-hardening
```

### Commit convention
```
type(scope): description

Types: feat, fix, refactor, test, docs, chore
Scopes: scoring, alerts, gamification, csr, ai, security, ui, deps

Examples:
  feat(scoring): add esg_score model with scope fields
  fix(security): tighten employee record rule domain
  test(rbac): add cross-employee ORM isolation test
  docs(readme): add installed-app detection instructions
```

Aim for at least **one commit per hour per active contributor**.

---

## Judge FAQ

### "Doesn't Odoo 19 Enterprise already have an ESG app?"

> *Odoo 19 Enterprise's ESG app handles GHG-protocol Scope 1/2/3 reporting and
> CSRD compliance dashboards — it's a compliance tool. EcoSphere adds the composite
> scoring engine, AI-driven action items specific to each user's actual data gaps,
> proactive risk alerts with Grok narrative, behaviour-driven gamification with an
> anti-gaming audit trail, and three role-scoped dashboards that turn compliance numbers
> into personal behaviour change. It also runs on Community edition, where Odoo's
> native ESG app doesn't exist at all.*

### "Doesn't Odoo's Employees/Attendance app already do this?"

> *Yes — and we don't rebuild it. EcoSphere reads from `hr.employee`, `hr.attendance`,
> and `hr.leave` directly. Our value-add is the ESG scoring layer on top of those
> native records: explainable composite scores, AI-generated improvement actions,
> gamification, and the comparative department/sector intelligence that Odoo's native
> HR apps don't provide.*

---

## Environment Variables

See `.env.example`. Required variables:

| Variable | Description |
|---|---|
| `GROK_API_KEY` | Your xAI API key — **never commit this** |
| `GROK_MODEL` | Grok model name (default: `grok-4.5`) |
| `GROK_BASE_URL` | xAI API base URL (default: `https://api.x.ai/v1`) |

The Python AI service reads these via `os.environ.get()`. The key never appears
in source code, logs, or Odoo config files.
