# EcoSphere — 5-Minute Judging Presentation Script
**Odoo Hackathon** — Sustainability & ESG Platform

This script maps to the judging criteria, demonstrating **ERP-native integration, server-side data isolation, anti-gaming gamification, and Grok AI explainability**.

---

## 0. Pre-Demo Setup (1 minute before judges arrive)
1. Log in to the Odoo instance in three different private browser tabs (to quickly switch views):
   - Tab 1: **Employee Dashboard** (login: `esg_emp_test@example.com` / pass: `EcoSphereEmp2024!`)
   - Tab 2: **Manager Dashboard** (login: `esg_mgr_test@example.com` / pass: `EcoSphereMgr2024!`)
   - Tab 3: **Admin Dashboard** (login: `esg_admin_test@example.com` / pass: `EcoSphereAdm2024!`)
2. In the Admin Dashboard Settings, trigger the "Seed Mock Data" button to ensure active historical score metrics and alerts exist.

---

## 1. Introduction: The Mission (30 seconds)
> *"Welcome, judges. Today we are presenting **EcoSphere**, an AI-powered, ERP-native ESG Scoring and Sustainability Intelligence platform for Odoo. Odoo currently lacks composite scoring, AI coaching, risk alerts, and gamification layers. We have built a single, unified scoring and alerting engine, and exposed three role-scoped dashboards on top: Employee, Manager, and Executive Admin."*

---

## 2. Step 1: The Employee Onboarding & Journey (1.5 minutes)
*Show Tab 1: Employee Dashboard (`esg_emp_test`)*

- **Explain the score meter:**
  > *"When Elena Rodriguez logs in, she is greeted by her profile summary and her overall ESG Score of 82.5 (Gold Tier). The E, S, and G sub-scores are visible below."*
- **Demonstrate Grok explainability:**
  > *"Below her score, she sees a plain-language explanation generated dynamically by Grok, explaining why her score is 82.5 and advising her to reduce travel emissions to hit Platinum."*
- **Demonstrate Onboarding & Gamification:**
  > *"Because this is Elena's first run, the system automatically generated her default onboarding goal: 'First Step: Initial ESG Action Plan'. In her list of recommendations, she has a data-grounded action item 'Attend Upcoming CSR Event'. Let's mark it as done."*
- **Complete action item:** Click **Done** on the recommendation.
  > *"Marking it done writes a verified, audit-trackable transaction to the append-only XP Ledger, granting her 100 XP. This log prevents double-claiming, securing the gamification layer against gaming."*
- **Test AI Assistant:** Type *"How can I raise my score?"* in the chat box.
  > *"Elena has a role-scoped AI Assistant. This assistant has access ONLY to her personal metrics context and chat history, ensuring strict data isolation."*

---

## 3. Step 2: Manager Department Analytics (1.5 minutes)
*Show Tab 2: Manager Dashboard (`esg_mgr_test`)*

- **Explain department summary:**
  > *"Now we switch to Elena's manager, David Chen. David's dashboard aggregates data across the IT Operations department. He sees his department score is 82.0, headcount is 4, and his active department directory list."*
- **Demonstrate data minimization:**
  > *"To protect employee privacy, the directory table displays only names and scores. Sensitive fields like age, gender, and salary are omitted entirely at the database query level."*
- **Show Active alerts:**
  > *"David has a critical alert: 'Critical Limit: Electricity Usage'. Odoo's threshold engine triggered this alert offline immediately when electricity consumption crossed limit bounds. Grok then enriched it with a mitigative ai_narrative, advising David to check server room cooling units."*
- **Demonstrate Manager AI Advisor:**
  > *"David's AI Advisor has department-scoped context, answering queries about department emissions and team performance without ever exposing private employee-level data."*

---

## 4. Step 3: Admin Executive Controls (1 minute)
*Show Tab 3: Admin Dashboard (`esg_admin_test`)*

- **Explain Org KPI cards:**
  > *"Finally, we look at the Executive Admin Dashboard. The Admin sees company-wide KPIs: overall ESG score (78.0), carbon emissions, and total compliance rate."*
- **Demonstrate Score Weight Configuration:**
  > *"Here is the core differentiator: the Admin ESG Score Weightage setting. The Admin can slide the Environmental weight to 45% and click 'Save & Recompute'. This writes to the database category table and runs our unified rollup calculations live, updating the score rings on all three dashboards instantly."*

---

## 5. Judge Q&A Handout (Ready for the 2 standard questions)

### Q1: "Doesn't Odoo 19 Enterprise already have an ESG app?"
> *"Odoo 19 Enterprise's ESG app is a compliance tool that calculates Scope 1/2/3 values from accounting. EcoSphere adds the composite scoring layer, Grok explainability, deterministic threshold risk alerts, behavior-driven gamification using append-only ledgers, and three role-scoped dashboards. Best of all: EcoSphere runs on Community edition, filling a massive product gap."*

### Q2: "Doesn't Odoo's Employees / Attendance app already do this?"
> *"Yes, and we do not duplicate them. EcoSphere reads directly from native `hr.employee` and `hr.attendance` tables. Our value-add is the scoring aggregation math, Grok-generated action recommendations, and the comparative department and sector analytics that native Odoo HR apps do not support."*
