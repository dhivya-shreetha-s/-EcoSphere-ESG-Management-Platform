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
    """,
    'category': 'Human Resources/ESG',
    'author': 'EcoSphere Hackathon Team',
    'website': 'https://github.com/dhivya-shreetha-s/-EcoSphere-ESG-Management-Platform.git',
    'license': 'LGPL-3',
    'depends': [
        'base',
        'mail',
        'hr',
    ],
    'data': [
        'security/esg_security.xml',
        'security/ir.model.access.csv',
        'data/esg_category_data.xml',
        'data/esg_sector_data.xml',
        'data/esg_test_users.xml',
        'views/esg_sector_views.xml',
        'views/esg_score_views.xml',
        'views/esg_alert_views.xml',
        'views/esg_recommendation_views.xml',
        'views/esg_menu.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'ecosphere/static/src/css/ecosphere.css',
            'ecosphere/static/src/js/ecosphere_menu.js',
            'ecosphere/static/src/js/esg_score_ring.js',
            'ecosphere/static/src/js/esg_category_chart.js',
            'ecosphere/static/src/js/esg_alert_card.js',
            'ecosphere/static/src/js/esg_ai_chat_panel.js',
            'ecosphere/static/src/js/esg_employee_dashboard.js',
            'ecosphere/static/src/js/esg_manager_dashboard.js',
            'ecosphere/static/src/js/esg_admin_dashboard.js',
            'ecosphere/static/src/xml/esg_score_ring.xml',
            'ecosphere/static/src/xml/esg_category_chart.xml',
            'ecosphere/static/src/xml/esg_alert_card.xml',
            'ecosphere/static/src/xml/esg_ai_chat_panel.xml',
            'ecosphere/static/src/xml/esg_employee_dashboard.xml',
            'ecosphere/static/src/xml/esg_manager_dashboard.xml',
            'ecosphere/static/src/xml/esg_admin_dashboard.xml',
        ],
    },
    'installable': True,
    'application': True,
    'auto_install': False,
}
