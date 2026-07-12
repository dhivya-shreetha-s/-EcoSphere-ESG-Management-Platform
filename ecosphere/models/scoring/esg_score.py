# -*- coding: utf-8 -*-
"""
esg.score — The central output record of the EcoSphere scoring engine.

One record per (subject × period). Subject is identified by exactly one of:
  - employee_id  (scope = 'employee')
  - department_id (scope = 'department')
  - sector_id    (scope = 'sector')
  - (none)       (scope = 'org')

The scoring engine in Phase 2 populates:
  - score_env, score_social, score_gov  (0–100 each)
  - score_overall                        (weighted composite, 0–100)
  - score_label                          (Bronze/Silver/Gold/Platinum tier)
  - factor_breakdown                     (JSON — which metrics contributed what)
  - suggested_esg_bonus_pct             (computed suggestion; NEVER a payroll write)

The Grok AI layer in Phase 3 populates:
  - explanation                          (plain-language narrative; fallback = empty)

IMPORTANT: `factor_breakdown` is stored as JSON text in Phase 1 for simplicity.
If Phase 2 determines a normalised One2many child model is needed for richer
querying, flag it before Phase 2 execution starts (see plan note on this field).
"""
import json
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class EsgScore(models.Model):
    _name = 'esg.score'
    _description = 'ESG Score'
    _order = 'period_start desc, scope, score_overall desc'

    # ------------------------------------------------------------------ #
    # Scope — exactly one of these is set depending on scope value        #
    # ------------------------------------------------------------------ #
    scope = fields.Selection(
        selection=[
            ('employee', 'Employee'),
            ('department', 'Department'),
            ('sector', 'Sector'),
            ('org', 'Organisation'),
        ],
        string='Scope',
        required=True,
        index=True,
        default='employee',
    )
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Employee',
        ondelete='cascade',
        index=True,
    )
    department_id = fields.Many2one(
        comodel_name='hr.department',
        string='Department',
        ondelete='cascade',
        index=True,
    )
    sector_id = fields.Many2one(
        comodel_name='esg.sector',
        string='Sector',
        ondelete='cascade',
        index=True,
    )

    # ------------------------------------------------------------------ #
    # Scoring period                                                       #
    # ------------------------------------------------------------------ #
    period_start = fields.Date(string='Period Start', required=True, index=True)
    period_end = fields.Date(string='Period End', required=True)

    # ------------------------------------------------------------------ #
    # Scores (0–100)                                                       #
    # ------------------------------------------------------------------ #
    score_env = fields.Float(
        string='Environmental Score',
        digits=(6, 2),
        default=0.0,
        help='Environmental sub-score (0–100). Computed by Phase 2 engine.',
    )
    score_social = fields.Float(
        string='Social Score',
        digits=(6, 2),
        default=0.0,
        help='Social sub-score (0–100). Computed by Phase 2 engine.',
    )
    score_gov = fields.Float(
        string='Governance Score',
        digits=(6, 2),
        default=0.0,
        help='Governance sub-score (0–100). Computed by Phase 2 engine.',
    )
    score_overall = fields.Float(
        string='Overall ESG Score',
        digits=(6, 2),
        default=0.0,
        index=True,
        help='Weighted composite of E/S/G sub-scores (0–100).',
    )
    score_label = fields.Selection(
        selection=[
            ('bronze', 'Bronze'),
            ('silver', 'Silver'),
            ('gold', 'Gold'),
            ('platinum', 'Platinum'),
        ],
        string='ESG Tier',
        compute='_compute_score_label',
        store=True,
        help='Tier computed from overall score: Bronze <50, Silver <70, Gold <90, Platinum ≥90.',
    )

    @api.depends('score_overall')
    def _compute_score_label(self):
        for rec in self:
            if rec.score_overall >= 90:
                rec.score_label = 'platinum'
            elif rec.score_overall >= 70:
                rec.score_label = 'gold'
            elif rec.score_overall >= 50:
                rec.score_label = 'silver'
            else:
                rec.score_label = 'bronze'

    # ------------------------------------------------------------------ #
    # Explainability layer                                                 #
    # ------------------------------------------------------------------ #
    factor_breakdown = fields.Text(
        string='Factor Breakdown (JSON)',
        help=(
            'JSON object: {metric_id: {name, category, weight, raw_value, '
            'normalised, contribution}}. Written by Phase 2 scoring engine.'
        ),
    )

    def get_factor_breakdown(self):
        """Return factor_breakdown parsed to dict; empty dict if not set."""
        self.ensure_one()
        if not self.factor_breakdown:
            return {}
        try:
            return json.loads(self.factor_breakdown)
        except (json.JSONDecodeError, TypeError):
            return {}

    # ------------------------------------------------------------------ #
    # Salary suggestion — always a suggestion, never a payroll write      #
    # See plan OQ-2. Label is enforced in Phase 4 UI.                     #
    # ------------------------------------------------------------------ #
    suggested_esg_bonus_pct = fields.Float(
        string='Suggested ESG Bonus (%)',
        digits=(5, 2),
        default=0.0,
        help=(
            'A transparent, formula-derived suggestion only. '
            'NOT a payroll transaction. Phase 2 computes this from score_overall.'
        ),
    )

    # ------------------------------------------------------------------ #
    # AI narrative (Phase 3)                                              #
    # ------------------------------------------------------------------ #
    explanation = fields.Text(
        string='AI Explanation',
        help=(
            'Grok-generated plain-language narrative. '
            'Empty = fallback text shown in UI; never blocks rendering.'
        ),
    )

    computed_at = fields.Datetime(
        string='Computed At',
        help='Timestamp of last scoring engine run for this record.',
    )

    # ------------------------------------------------------------------ #
    # Validation                                                           #
    # ------------------------------------------------------------------ #
    @api.constrains('period_start', 'period_end')
    def _check_period(self):
        for rec in self:
            if rec.period_start and rec.period_end:
                if rec.period_start > rec.period_end:
                    raise ValidationError('Period Start must be before Period End.')

    @api.constrains('scope', 'employee_id', 'department_id', 'sector_id')
    def _check_scope_consistency(self):
        for rec in self:
            if rec.scope == 'employee' and not rec.employee_id:
                raise ValidationError('Employee scope requires an Employee.')
            if rec.scope == 'department' and not rec.department_id:
                raise ValidationError('Department scope requires a Department.')
            if rec.scope == 'sector' and not rec.sector_id:
                raise ValidationError('Sector scope requires a Sector.')
