# -*- coding: utf-8 -*-
"""
Phase 1 smoke test — verifies module installs cleanly and seed data exists.

Run with:
  python -m pytest ecosphere/tests/test_install.py -v
  # or via Odoo test runner:
  odoo-bin -i ecosphere --test-enable --stop-after-init -d ecosphere_test
"""
from odoo.tests.common import TransactionCase


class TestInstall(TransactionCase):

    def test_esg_categories_seeded(self):
        """Three ESG categories (E, S, G) must exist after install."""
        categories = self.env['esg.category'].search([])
        codes = set(categories.mapped('code'))
        self.assertEqual(
            codes, {'E', 'S', 'G'},
            'Expected exactly three ESG categories (E, S, G) to be seeded at install.',
        )

    def test_esg_sectors_seeded(self):
        """At least one sector must exist after install."""
        sector_count = self.env['esg.sector'].search_count([])
        self.assertGreater(
            sector_count, 0,
            'Expected at least one ESG sector to be seeded at install.',
        )

    def test_models_accessible(self):
        """All EcoSphere models must be importable and their tables present."""
        model_names = [
            'esg.sector',
            'esg.category',
            'esg.metric',
            'esg.data.source',
            'esg.score',
            'esg.alert',
            'esg.recommendation',
            'esg.csr.event',
            'esg.csr.event.registration',
            'esg.challenge',
            'esg.badge',
            'esg.reward',
            'esg.xp.ledger',
            'esg.goal',
            'esg.ai.log',
        ]
        for model_name in model_names:
            with self.subTest(model=model_name):
                self.assertIn(
                    model_name, self.env,
                    f'Model "{model_name}" not found in registry — possible import or manifest error.',
                )
                # Verify table exists by running a search (raises if table missing)
                self.env[model_name].search([], limit=1)

    def test_hr_department_extension(self):
        """hr.department must have the esg_sector_id field after install."""
        dept_model = self.env['hr.department']
        self.assertIn(
            'esg_sector_id',
            dept_model._fields,
            'hr.department.esg_sector_id field not found — sector extension failed.',
        )

    def test_category_weights_sum_to_100(self):
        """Category weights should sum to approximately 100."""
        categories = self.env['esg.category'].search([])
        total = sum(c.weight for c in categories)
        self.assertAlmostEqual(
            total, 100.0, places=0,
            msg=f'Category weights sum to {total:.2f} — expected ~100.',
        )
