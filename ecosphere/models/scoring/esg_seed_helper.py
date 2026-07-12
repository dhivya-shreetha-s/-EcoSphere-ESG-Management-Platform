# -*- coding: utf-8 -*-
"""
esg.seed.helper — Transient seed helper for generating test and demo data.

Creates mock employee, department, attendance, fleet, account, and CSR records.
Then runs the scoring engine rollup, writing realistic historical scores.
"""
from odoo import api, fields, models
import random
from datetime import date, timedelta, datetime, time


class EsgSeedHelper(models.TransientModel):
    _name = 'esg.seed.helper'
    _description = 'EcoSphere Demo Data Seed Helper'

    def action_seed_mock_data(self):
        """Creates complete mock data set."""
        # 1. Get or create Data Sources
        source_attendance = self._get_or_create_source('HR Attendance', 'hr.attendance', 'check_in')
        source_csr = self._get_or_create_source('CSR Volunteer Hours', 'esg.csr.event.registration', 'hours_attended')
        source_fleet = self._get_or_create_source('Fleet Fuel Logs', 'fleet.vehicle', 'amount')
        source_accounting = self._get_or_create_source('Accounting Utilities', 'account.move', 'debit')

        # 2. Get categories
        cat_e = self.env['esg.category'].search([('code', '=', 'E')], limit=1)
        cat_s = self.env['esg.category'].search([('code', '=', 'S')], limit=1)
        cat_g = self.env['esg.category'].search([('code', '=', 'G')], limit=1)

        # 3. Get or create Metrics
        metric_attendance = self._get_or_create_metric(
            'Attendance Rate', cat_s.id, source_attendance.id, '%', 50.0, 'higher_is_better', 0.0, 100.0
        )
        metric_csr = self._get_or_create_metric(
            'CSR Volunteering Hours', cat_s.id, source_csr.id, 'hrs', 50.0, 'higher_is_better', 0.0, 20.0
        )
        metric_utility = self._get_or_create_metric(
            'Electricity & Utility Consumption', cat_e.id, source_accounting.id, 'debit sum', 60.0, 'lower_is_better', 0.0, 5000.0
        )
        metric_fuel = self._get_or_create_metric(
            'Fleet Fuel Consumption', cat_e.id, source_fleet.id, 'litres', 40.0, 'lower_is_better', 0.0, 500.0
        )

        # 4. Get or create Sectors and Departments
        sector_it = self.env['esg.sector'].search([('code', '=', 'IT')], limit=1)
        if not sector_it:
            sector_it = self.env['esg.sector'].create({'name': 'Information Technology', 'code': 'IT'})

        dept_it = self.env['hr.department'].search([('name', '=', 'IT Operations')], limit=1)
        if not dept_it:
            dept_it = self.env['hr.department'].create({'name': 'IT Operations', 'esg_sector_id': sector_it.id})

        # 5. Create mock employees if none exist
        employee_ids = []
        emp_names = ['Elena Rodriguez', 'Marcus Thorne', 'Sarah Chen', 'Alex Mercer']
        for name in emp_names:
            emp = self.env['hr.employee'].search([('name', '=', name)], limit=1)
            if not emp:
                user = self.env['res.users'].create({
                    'name': name,
                    'login': f"{name.lower().replace(' ', '_')}@ecosphere.com",
                    'groups_id': [(4, self.env.ref('ecosphere.group_esg_employee').id)],
                })
                emp = self.env['hr.employee'].create({
                    'name': name,
                    'user_id': user.id,
                    'department_id': dept_it.id,
                })
            employee_ids.append(emp)

        # 6. Create mock Attendances for the last 30 days
        start_date = date.today() - timedelta(days=30)
        end_date = date.today()

        if 'hr.attendance' in self.env:
            curr = start_date
            while curr <= end_date:
                if curr.weekday() < 5:  # Mon-Fri
                    for emp in employee_ids:
                        # random check-in rate (approx 90% attendance)
                        if random.random() < 0.90:
                            check_in = datetime.combine(curr, time(9, 0, 0))
                            check_out = datetime.combine(curr, time(17, 0, 0))
                            self.env['hr.attendance'].create({
                                'employee_id': emp.id,
                                'check_in': check_in,
                                'check_out': check_out,
                            })
                curr += timedelta(days=1)

        # 7. Create mock CSR Events and registrations
        event = self.env['esg.csr.event'].create({
            'name': 'Urban Tree Planting Drive',
            'description': 'Help plant 500 saplings for the regional reforestation project.',
            'event_date': date.today() - timedelta(days=10),
            'location': 'Maple Park',
            'category_id': cat_s.id,
            'state': 'completed',
            'xp_award': 100,
        })
        for emp in employee_ids:
            self.env['esg.csr.event.registration'].create({
                'event_id': event.id,
                'employee_id': emp.id,
                'state': 'attended',
                'hours_attended': random.randint(4, 8),
            })

        # 8. Create mock scores
        for emp in employee_ids:
            score = self.env['esg.score'].create({
                'scope': 'employee',
                'employee_id': emp.id,
                'period_start': start_date,
                'period_end': end_date,
            })
            score.action_compute_score()

        # Compute Department Score
        score_dept = self.env['esg.score'].create({
            'scope': 'department',
            'department_id': dept_it.id,
            'period_start': start_date,
            'period_end': end_date,
        })
        score_dept.action_compute_score()

        # Compute Sector Score
        score_sect = self.env['esg.score'].create({
            'scope': 'sector',
            'sector_id': sector_it.id,
            'period_start': start_date,
            'period_end': end_date,
        })
        score_sect.action_compute_score()

        # Compute Org Score
        score_org = self.env['esg.score'].create({
            'scope': 'org',
            'period_start': start_date,
            'period_end': end_date,
        })
        score_org.action_compute_score()

        return True

    def _get_or_create_source(self, name, model, field):
        source = self.env['esg.data.source'].search([('model_name', '=', model)], limit=1)
        if not source:
            source = self.env['esg.data.source'].create({
                'name': name,
                'model_name': model,
                'field_name': field,
            })
        return source

    def _get_or_create_metric(self, name, category_id, data_source_id, unit, weight, direction, min_v, max_v):
        metric = self.env['esg.metric'].search([('name', '=', name)], limit=1)
        if not metric:
            metric = self.env['esg.metric'].create({
                'name': name,
                'category_id': category_id,
                'data_source_id': data_source_id,
                'unit': unit,
                'weight': weight,
                'direction': direction,
                'min_value': min_v,
                'max_value': max_v,
            })
        return metric
