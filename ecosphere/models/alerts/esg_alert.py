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

    # ------------------------------------------------------------------ #
    # Phase 3: Alert Triggering & AI enrichment                           #
    # ------------------------------------------------------------------ #
    @api.model
    def check_score_thresholds(self, score):
        """
        Deterministic trigger checklist. Called after a score is computed.
        If a metric has crossed a critical threshold, creates an alert record
        and schedules AI narrative context.
        """
        breakdown = score.get_factor_breakdown()
        if not breakdown or 'metrics' not in breakdown:
            return

        for m in breakdown['metrics']:
            norm = m['normalized_score']
            metric = self.env['esg.metric'].browse(m['id'])
            
            # If normalized score is critical (< 50)
            if norm < 50.0:
                # Determine scoping details
                target_role = 'employee'
                scope = 'self'
                if score.scope == 'department':
                    target_role = 'manager'
                    scope = 'department'
                elif score.scope in ('sector', 'org'):
                    target_role = 'admin'
                    scope = 'org'

                # Create Alert deterministically (offline compatible!)
                alert = self.create({
                    'name': f"Critical Limit: {metric.name}",
                    'message': f"Metric '{metric.name}' score dropped to {norm:.1f}/100. Action required.",
                    'severity': 'critical' if norm < 30.0 else 'warning',
                    'target_role': target_role,
                    'scope': scope,
                    'employee_id': score.employee_id.id if score.scope == 'employee' else False,
                    'department_id': score.department_id.id if score.scope == 'department' else False,
                    'metric_id': metric.id,
                    'threshold_value': 50.0,
                    'actual_value': m['raw_value'],
                })

                # Try to enrich with AI narrative
                alert.action_enrich_alert_with_ai()

    def action_enrich_alert_with_ai(self):
        """Request Grok to write a 1-sentence mitigative context."""
        for rec in self:
            narrative = self.env['esg.ai.service'].get_alert_narrative(rec)
            if narrative:
                rec.write({'ai_narrative': narrative})
