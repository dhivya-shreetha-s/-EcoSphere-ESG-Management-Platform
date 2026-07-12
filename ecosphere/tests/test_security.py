# -*- coding: utf-8 -*-
"""
Phase 1 RBAC security tests.

These tests verify the server-side record rules enforce proper data isolation.
They prove an Employee ORM call is INCAPABLE of reading another employee's
esg.score — regardless of UI state.

Run alongside test_install.py with the same test runner command.
"""
from odoo.tests.common import TransactionCase
from odoo.exceptions import AccessError


class TestRBAC(TransactionCase):

    def setUp(self):
        super().setUp()
        # Create two hr.employee records for testing cross-employee access
        self.dept = self.env['hr.department'].create({'name': 'Test Dept A'})
        self.dept_b = self.env['hr.department'].create({'name': 'Test Dept B'})

        # Employee A — in dept A
        self.user_emp_a = self.env['res.users'].create({
            'name': 'Test Employee A',
            'login': 'test_emp_a_rbac@test.com',
            'groups_id': [(4, self.env.ref('ecosphere.group_esg_employee').id)],
        })
        self.hr_emp_a = self.env['hr.employee'].create({
            'name': 'Test Employee A',
            'user_id': self.user_emp_a.id,
            'department_id': self.dept.id,
        })

        # Employee B — in dept A (same dept, different person)
        self.user_emp_b = self.env['res.users'].create({
            'name': 'Test Employee B',
            'login': 'test_emp_b_rbac@test.com',
            'groups_id': [(4, self.env.ref('ecosphere.group_esg_employee').id)],
        })
        self.hr_emp_b = self.env['hr.employee'].create({
            'name': 'Test Employee B',
            'user_id': self.user_emp_b.id,
            'department_id': self.dept.id,
        })

        # Create a score for Employee B
        cat = self.env['esg.category'].search([('code', '=', 'E')], limit=1)
        self.score_b = self.env['esg.score'].create({
            'scope': 'employee',
            'employee_id': self.hr_emp_b.id,
            'period_start': '2024-01-01',
            'period_end': '2024-01-31',
            'score_env': 75.0,
            'score_social': 80.0,
            'score_gov': 70.0,
            'score_overall': 75.0,
        })

    def test_employee_cannot_read_other_employee_score(self):
        """
        CRITICAL RBAC CHECK (Phase 1 DoD):
        Employee A must not be able to read Employee B's esg.score record.
        This must hold at the ORM level, not just the UI level.
        """
        scores_seen_by_a = self.env['esg.score'].with_user(
            self.user_emp_a
        ).search([])
        score_ids_seen = scores_seen_by_a.ids
        self.assertNotIn(
            self.score_b.id,
            score_ids_seen,
            'SECURITY BREACH: Employee A can read Employee B\'s esg.score via ORM search! '
            'Check the esg_score_employee_rule record rule in esg_security.xml.',
        )

    def test_employee_sees_own_score(self):
        """Employee A should be able to read their own score if one exists."""
        score_a = self.env['esg.score'].create({
            'scope': 'employee',
            'employee_id': self.hr_emp_a.id,
            'period_start': '2024-01-01',
            'period_end': '2024-01-31',
            'score_env': 60.0,
            'score_social': 65.0,
            'score_gov': 70.0,
            'score_overall': 65.0,
        })
        scores_seen = self.env['esg.score'].with_user(
            self.user_emp_a
        ).search([])
        self.assertIn(
            score_a.id,
            scores_seen.ids,
            'Employee A cannot see their own esg.score — record rule too restrictive.',
        )

    def test_employee_alert_isolation(self):
        """Employee A must not see Employee B's personal alerts."""
        alert_b = self.env['esg.alert'].create({
            'name': 'Alert for B',
            'message': 'Test alert',
            'severity': 'warning',
            'target_role': 'employee',
            'scope': 'self',
            'employee_id': self.hr_emp_b.id,
        })
        alerts_seen = self.env['esg.alert'].with_user(
            self.user_emp_a
        ).search([])
        self.assertNotIn(
            alert_b.id,
            alerts_seen.ids,
            'SECURITY BREACH: Employee A can see Employee B\'s alert via ORM search!',
        )

    def test_employee_xp_ledger_isolation(self):
        """Employee A must not see Employee B's XP ledger entries."""
        ledger_b = self.env['esg.xp.ledger'].create({
            'employee_id': self.hr_emp_b.id,
            'delta_xp': 50,
            'reason': 'event_attended',
            'verified_by_data': True,
        })
        ledger_seen = self.env['esg.xp.ledger'].with_user(
            self.user_emp_a
        ).search([])
        self.assertNotIn(
            ledger_b.id,
            ledger_seen.ids,
            'SECURITY BREACH: Employee A can read Employee B\'s XP ledger!',
        )
