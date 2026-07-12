# -*- coding: utf-8 -*-
"""
Phase 5 gamification, ledger writes, and onboarding tests.
"""
from odoo.tests.common import TransactionCase
from datetime import date, timedelta


class TestGamification(TransactionCase):

    def setUp(self):
        super().setUp()
        
        self.env['esg.xp.ledger'].search([]).unlink()
        self.env['esg.goal'].search([]).unlink()

        self.dept = self.env['hr.department'].create({'name': 'Engineering'})
        self.employee = self.env['hr.employee'].create({
            'name': 'Test Gamification User',
            'department_id': self.dept.id,
        })
        
        self.cat_s = self.env['esg.category'].search([('code', '=', 'S')], limit=1)

        # Create dummy metric
        self.metric = self.env['esg.metric'].create({
            'name': 'General metric',
            'category_id': self.cat_s.id,
            'unit': 'units',
            'weight': 50.0,
            'direction': 'higher_is_better',
            'min_value': 0.0,
            'max_value': 100.0,
        })

    def test_onboarding_goal_creates_automatically(self):
        """Verifies onboarding wizard creates a default active goal when checked."""
        goal_model = self.env['esg.goal']
        
        # Initial active goals
        initial_goals = goal_model.search_count([('employee_id', '=', self.employee.id)])
        self.assertEqual(initial_goals, 0)

        # Trigger onboarding
        goal_model.check_or_create_onboarding_goal(self.employee)

        # Assert goal exists and is active
        goals = goal_model.search([('employee_id', '=', self.employee.id)])
        self.assertEqual(len(goals), 1)
        self.assertEqual(goals[0].state, 'active')
        self.assertEqual(goals[0].name, 'First Step: Initial ESG Action Plan')

    def test_xp_ledger_anti_double_award(self):
        """Verifies CSR event attendance registration state changes trigger XP once only."""
        # Create CSR event
        event = self.env['esg.csr.event'].create({
            'name': 'Test Volunteer Event',
            'event_date': date.today(),
            'xp_award': 150,
        })

        reg = self.env['esg.csr.event.registration'].create({
            'event_id': event.id,
            'employee_id': self.employee.id,
            'state': 'registered',
        })

        # Transition to attended (1st time) -> triggers XP
        reg.write({'state': 'attended'})
        
        # Verify ledger entry created
        ledger_entries = self.env['esg.xp.ledger'].search([('employee_id', '=', self.employee.id)])
        self.assertEqual(len(ledger_entries), 1)
        self.assertEqual(ledger_entries[0].delta_xp, 150)
        self.assertEqual(ledger_entries[0].reason, 'event_attended')

        # Try updating state again
        reg.write({'state': 'attended'})
        
        # Verify no double entries
        ledger_entries_after = self.env['esg.xp.ledger'].search([('employee_id', '=', self.employee.id)])
        self.assertEqual(len(ledger_entries_after), 1, "Expected anti-double-award checks to prevent duplicate XP ledger writes.")
