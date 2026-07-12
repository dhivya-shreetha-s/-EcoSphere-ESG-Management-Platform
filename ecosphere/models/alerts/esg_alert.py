# -*- coding: utf-8 -*-
"""
esg.alert — Single model powering ALL three Alert Centers.

The `target_role` + `scope` combination determines visibility:
  - target_role='employee', scope='self'       → shown on Employee dashboard
  - target_role='manager',  scope='department' → shown on Manager dashboard
  - target_role='admin',    scope='org'        → shown on Admin dashboard

Record rules in security/esg_security.xml enforce this at the ORM level —
an Employee cannot read a manager-scoped alert even via direct shell query.

Alert lifecycle:
  1. Phase 2 deterministic threshold engine writes the alert (no AI dependency).
  2. Phase 3 Grok enrichment adds `ai_narrative` as an optional supplement.
  3. The alert trigger (state→active) NEVER depends on the Grok call succeeding.
"""
from odoo import api, fields, models


class EsgAlert(models.Model):
    _name = 'esg.alert'
    _description = 'ESG Risk Alert'
    _order = 'create_date desc, severity'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Alert Title', required=True)
    message = fields.Text(
        string='Alert Message',
        required=True,
        help='Deterministic, human-readable description. Always populated.',
    )
    ai_narrative = fields.Text(
        string='AI Narrative',
        help=(
            'Grok-enriched context and urgency framing (Phase 3). '
            'Empty = UI falls back to `message`. Never blocks alert display.'
        ),
    )
    severity = fields.Selection(
        selection=[
            ('info', 'Info'),
            ('warning', 'Warning'),
            ('critical', 'Critical'),
        ],
        string='Severity',
        required=True,
        default='warning',
        index=True,
    )

    # ------------------------------------------------------------------ #
    # Visibility scoping — drives record rules                            #
    # ------------------------------------------------------------------ #
    target_role = fields.Selection(
        selection=[
            ('employee', 'Employee'),
            ('manager', 'Manager'),
            ('admin', 'Admin'),
        ],
        string='Target Role',
        required=True,
        index=True,
        help='Which role dashboard this alert surfaces on.',
    )
    scope = fields.Selection(
        selection=[
            ('self', 'Individual'),
            ('department', 'Department'),
            ('org', 'Organisation'),
        ],
        string='Scope',
        required=True,
        default='department',
    )
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Employee',
        ondelete='cascade',
        index=True,
        help='Set when scope=self.',
    )
    department_id = fields.Many2one(
        comodel_name='hr.department',
        string='Department',
        ondelete='cascade',
        index=True,
        help='Set when scope=department.',
    )

    # ------------------------------------------------------------------ #
    # Trigger metadata — for explainability and audit                     #
    # ------------------------------------------------------------------ #
    metric_id = fields.Many2one(
        comodel_name='esg.metric',
        string='Triggered By Metric',
        ondelete='set null',
        help='Which ESG metric crossed the threshold.',
    )
    threshold_value = fields.Float(
        string='Threshold',
        digits=(10, 4),
        help='The configured threshold value that, when crossed, triggers the alert.',
    )
    actual_value = fields.Float(
        string='Actual Value',
        digits=(10, 4),
        help='The recorded metric value at time of trigger.',
    )

    # ------------------------------------------------------------------ #
    # Lifecycle                                                            #
    # ------------------------------------------------------------------ #
    state = fields.Selection(
        selection=[
            ('active', 'Active'),
            ('acknowledged', 'Acknowledged'),
            ('resolved', 'Resolved'),
        ],
        string='State',
        default='active',
        index=True,
        tracking=True,
    )
    is_resolved = fields.Boolean(
        string='Resolved',
        compute='_compute_is_resolved',
        store=True,
    )
    resolved_at = fields.Datetime(string='Resolved At')

    @api.depends('state')
    def _compute_is_resolved(self):
        for rec in self:
            rec.is_resolved = rec.state == 'resolved'

    def action_acknowledge(self):
        self.write({'state': 'acknowledged'})

    def action_resolve(self):
        self.write({
            'state': 'resolved',
            'resolved_at': fields.Datetime.now(),
        })
