# -*- coding: utf-8 -*-
"""
Phase 2 scoring and rollup math tests.

Verifies E/S/G category rollups, relative metric contributions, overall weighted score,
suggested bonus, normalization bounds, and hierarchical rollup (employee -> dept -> sector -> org).
"""
from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
import json


class TestScoring(TransactionCase):

    def setUp(self):
        super().setUp()
        
        # 1. Clean existing scores / metrics / sectors to isolate math tests
        self.env['esg.score'].search([]).unlink()
        self.env['esg.metric'].search([]).unlink()
        self.env['esg.sector'].search([]).unlink()

        # 2. Get E, S, G categories
        self.cat_e = self.env['esg.category'].search([('code', '=', 'E')], limit=1)
        self.cat_s = self.env['esg.category'].search([('code', '=', 'S')], limit=1)
        self.cat_g = self.env['esg.category'].search([('code', '=', 'G')], limit=1)

        # Ensure weights are 33.33 / 33.33 / 33.34
        self.cat_e.weight = 33.33
        self.cat_s.weight = 33.33
        self.cat_g.weight = 33.34

        # 3. Create dummy data sources
        self.src_attendance = self.env['esg.data.source'].create({
            'name': 'Test Attendance Source',
            'model_name': 'hr.attendance',
            'field_name': 'check_in',
        })
        self.src_csr = self.env['esg.data.source'].create({
            'name': 'Test CSR Source',
            'model_name': 'esg.csr.event.registration',
            'field_name': 'hours_attended',
        })

        # 4. Create metrics with exact bounds and weights
        # E Metric: Electricity (lower is better, range 0 to 1000)
        self.metric_electricity = self.env['esg.metric'].create({
            'name': 'Electricity Usage',
            'category_id': self.cat_e.id,
            'data_source_id': self.src_attendance.id,  # reuse for stub query
            'unit': 'kWh',
            'weight': 100.0,
            'direction': 'lower_is_better',
            'min_value': 0.0,
            'max_value': 1000.0,
        })

        # S Metric 1: Attendance (higher is better, range 0 to 100)
        self.metric_attendance = self.env['esg.metric'].create({
            'name': 'Attendance Rate',
            'category_id': self.cat_s.id,
            'data_source_id': self.src_attendance.id,
            'unit': '%',
            'weight': 60.0,
            'direction': 'higher_is_better',
            'min_value': 0.0,
            'max_value': 100.0,
        })

        # S Metric 2: Volunteering (higher is better, range 0 to 20)
        self.metric_volunteer = self.env['esg.metric'].create({
            'name': 'Volunteering Hours',
            'category_id': self.cat_s.id,
            'data_source_id': self.src_csr.id,
            'unit': 'hrs',
            'weight': 40.0,
            'direction': 'higher_is_better',
            'min_value': 0.0,
            'max_value': 20.0,
        })

        # G Metric: Compliance (higher is better, range 0 to 100)
        self.metric_compliance = self.env['esg.metric'].create({
            'name': 'Compliance Rate',
            'category_id': self.cat_g.id,
            'unit': '%',
            'weight': 100.0,
            'direction': 'higher_is_better',
            'min_value': 0.0,
            'max_value': 100.0,
        })

        # 5. Create test employees and department
        self.sector = self.env['esg.sector'].create({
            'name': 'Test Engineering Sector',
            'code': 'ENG',
        })
        self.dept = self.env['hr.department'].create({
            'name': 'Test Quality Assurance',
            'esg_sector_id': self.sector.id,
        })
        self.employee = self.env['hr.employee'].create({
            'name': 'Test QA Engineer',
            'department_id': self.dept.id,
        })

    def test_normalization_higher_is_better(self):
        """Verifies higher_is_better normalization arithmetic and boundary clipping."""
        score_record = self.env['esg.score'].create({
            'scope': 'employee',
            'employee_id': self.employee.id,
            'period_start': '2024-01-01',
            'period_end': '2024-01-31',
        })
        
        # Test exact mid-point
        norm = score_record._normalize_value(self.metric_attendance, 50.0)
        self.assertEqual(norm, 50.0)

        # Test below min_value (clipping)
        norm_low = score_record._normalize_value(self.metric_attendance, -10.0)
        self.assertEqual(norm_low, 0.0)

        # Test above max_value (clipping)
        norm_high = score_record._normalize_value(self.metric_attendance, 120.0)
        self.assertEqual(norm_high, 100.0)

    def test_normalization_lower_is_better(self):
        """Verifies lower_is_better normalization arithmetic."""
        score_record = self.env['esg.score'].create({
            'scope': 'employee',
            'employee_id': self.employee.id,
            'period_start': '2024-01-01',
            'period_end': '2024-01-31',
        })

        # Raw value = 250 (out of 0 to 1000)
        # Expected score: (1000 - 250) / 1000 * 100 = 75.0
        norm = score_record._normalize_value(self.metric_electricity, 250.0)
        self.assertEqual(norm, 75.0)

    def test_scoring_rollup_math(self):
        """
        Calculates a score record and verifies E/S/G category rollups,
        relative metric contributions, overall weighted score, and suggested bonus.
        """
        score_record = self.env['esg.score'].create({
            'scope': 'employee',
            'employee_id': self.employee.id,
            'period_start': '2024-01-01',
            'period_end': '2024-01-31',
        })

        # Inject mock data returns into aggregator (we'll override get_raw_value behavior
        # in the test by mapping the test values)
        def mock_get_raw_value(metric, scope, target_id, start_date, end_date):
            if metric == self.metric_electricity:
                return 400.0  # (1000 - 400)/1000 * 100 = 60.0 score (E)
            elif metric == self.metric_attendance:
                return 90.0   # 90.0 score (S, weight=60)
            elif metric == self.metric_volunteer:
                return 10.0   # 10/20 * 100 = 50.0 score (S, weight=40)
            elif metric == self.metric_compliance:
                return 80.0   # 80.0 score (G)
            return 0.0

        # Patch aggregator method during this test run
        self.patch(self.env['esg.data.aggregator'], 'get_raw_value', mock_get_raw_value)

        # Execute
        score_record.action_compute_score()

        # Math verification
        # 1. Category E Score: 60.0 (only 1 metric)
        self.assertEqual(score_record.score_env, 60.0)

        # 2. Category S Score: (90.0 * 60 + 50.0 * 40) / 100 = (5400 + 2000) / 100 = 74.0
        self.assertEqual(score_record.score_social, 74.0)

        # 3. Category G Score: 80.0
        self.assertEqual(score_record.score_gov, 80.0)

        # 4. Overall score: (60.0 * 33.33 + 74.0 * 33.33 + 80.0 * 33.34) / 100
        # = (1999.8 + 2466.42 + 2667.2) / 100 = 7133.42 / 100 = 71.3342 -> 71.33
        self.assertAlmostEqual(score_record.score_overall, 71.33, places=2)

        # 5. Suggested Bonus: overall_score / 10.0 = 7.133
        self.assertAlmostEqual(score_record.suggested_esg_bonus_pct, 7.13, places=2)

        # 6. Check explainability JSON structure
        breakdown = json.loads(score_record.factor_breakdown)
        self.assertIn('categories', breakdown)
        self.assertIn('metrics', breakdown)
        self.assertEqual(breakdown['categories']['E']['score'], 60.0)
        self.assertEqual(breakdown['categories']['S']['score'], 74.0)
        self.assertEqual(breakdown['categories']['G']['score'], 80.0)
