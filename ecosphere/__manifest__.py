# -*- coding: utf-8 -*-
{
    'name': 'EcoSphere — ESG Scoring & Sustainability Intelligence',
    'version': '19.0.1.0.0',
    'summary': (
        'AI-powered, ERP-native ESG scoring, risk alerts, gamification, '
        'and three role-scoped sustainability dashboards on one shared engine.'
    ),
    'description': """
EcoSphere for Odoo — Odoo Hackathon
=====================================
Three role-scoped dashboards (Employee / Manager / Admin) backed by one shared
scoring, alerting, and AI engine. Every ESG score is explainable down to the
factor level, enriched by Grok-generated action items and coaching, and reinforced
through verified gamification.

Differentiators over Odoo 19 Enterprise's native ESG app
---------------------------------------------------------
- Composite scoring with live explainability (factor weights + raw inputs)
- Grok-powered action items specific to each user's/dept's actual data gaps
- Deterministic threshold alerts enriched with AI-generated narrative context
- Cross-department & sector performance intelligence
- Verified, anti-gaming gamification (XP ledger tied to real data changes)
- Personalized sustainability journey with Grok goal coaching
- Runs on Community edition — no Enterprise license required

Architecture note
-----------------
Build the engine once; each dashboard is a thin, role-filtered view on top.
    """,
    'category': 'Human Resources/ESG',
    'author': 'EcoSphere Hackathon Team',
    'website': 'https://github.com/your-org/ecosphere',
    'license': 'LGPL-3',

    # ------------------------------------------------------------------ #
    # Hard dependencies (must be installed).  Optional native models are  #
    # detected at runtime via _check_installed_apps() in models/utils.py. #
    # ------------------------------------------------------------------ #
    'depends': [
        'base',
        'mail',       # for chatter on models + activity mixin
        'hr',         # hr.employee, hr.department — always present in Community
    ],

    # ------------------------------------------------------------------ #
    # Data load order matters: security first, then seed data, then views #
    # ------------------------------------------------------------------ #
    'data': [
        # 1. Security (groups + record rules)
        'security/esg_security.xml',
        'security/ir.model.access.csv',

        # 2. Seed / reference data
        'data/esg_category_data.xml',
        'data/esg_sector_data.xml',
        'data/esg_test_users.xml',

        # 3. Views & menus
        'views/esg_sector_views.xml',
        'views/esg_score_views.xml',
        'views/esg_alert_views.xml',
        'views/esg_recommendation_views.xml',
        'views/esg_menu.xml',          # menu last — references actions in views above
    ],

    'assets': {
        'web.assets_backend': [
            'ecosphere/static/src/css/ecosphere.css',
            'ecosphere/static/src/js/ecosphere_menu.js',
        ],
    },

    'images': ['static/description/banner.png'],
    'installable': True,
    'application': True,
    'auto_install': False,
}
