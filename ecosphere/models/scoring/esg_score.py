# -*- coding: utf-8 -*-
"""
esg.score — The central output record of the EcoSphere scoring engine.

Contains the real-time weighted scoring engine calculation math and the
hierarchical rollup logic.
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
    # Calculations Engine                                                  #
    # ------------------------------------------------------------------ #
    def action_compute_score(self):
        """
        Executes the scoring calculation for the record.
        1. Gathers active categories and weights.
        2. Loops through active metrics, pulling raw values via EsgDataAggregator.
        3. Normalizes each value to 0-100.
        4. Rolls up category sub-scores.
        5. Computes composite score and suggested bonus.
        6. Writes explainability details to factor_breakdown.
        """
        self.ensure_one()
        categories = self.env['esg.category'].search([])
        metrics = self.env['esg.metric'].search([('active', '=', True)])
        aggregator = self.env['esg.data.aggregator']

        # Determine target record ID based on scope
        target_id = False
        if self.scope == 'employee':
            target_id = self.employee_id.id
        elif self.scope == 'department':
            target_id = self.department_id.id
        elif self.scope == 'sector':
            target_id = self.sector_id.id

        breakdown_metrics = []
        category_scores = {}
        category_total_weights = {}

        # Initialise rollups
        for cat in categories:
            category_scores[cat.code] = 0.0
            category_total_weights[cat.code] = 0.0

        for metric in metrics:
            raw_val = aggregator.get_raw_value(
                metric, self.scope, target_id, self.period_start, self.period_end
            )
            norm_score = self._normalize_value(metric, raw_val)
            
            cat_code = metric.category_id.code
            category_scores[cat_code] += norm_score * metric.weight
            category_total_weights[cat_code] += metric.weight

            breakdown_metrics.append({
                'id': metric.id,
                'name': metric.name,
                'category': cat_code,
                'raw_value': raw_val,
                'unit': metric.unit or '',
                'normalized_score': norm_score,
                'weight_within_category': metric.weight,
            })

        # Calculate category averages
        final_scores = {}
        for cat in categories:
            code = cat.code
            total_weight = category_total_weights[code]
            if total_weight > 0:
                final_scores[code] = category_scores[code] / total_weight
            else:
                final_scores[code] = 100.0  # safe default

        # Calculate overall weighted score
        overall_numerator = 0.0
        overall_denominator = 0.0
        for cat in categories:
            overall_numerator += final_scores[cat.code] * cat.weight
            overall_denominator += cat.weight

        overall_score = 0.0
        if overall_denominator > 0:
            overall_score = overall_numerator / overall_denominator

        # Suggested ESG bonus: up to 10% maximum depending on overall score
        suggested_bonus = overall_score / 10.0

        # Construct final factor breakdown
        breakdown_categories = {}
        for cat in categories:
            breakdown_categories[cat.code] = {
                'name': cat.name,
                'weight': cat.weight,
                'score': round(final_scores[cat.code], 2),
            }

        # Calculate relative overall contribution for each metric
        for item in breakdown_metrics:
            cat_code = item['category']
            cat_weight = breakdown_categories[cat_code]['weight']
            metric_weight = item['weight_within_category']
            total_metric_weight = category_total_weights[cat_code] or 1.0
            
            # contribution = (normalized_score * metric_weight / total_metric_weight) * (cat_weight / 100)
            contribution = (item['normalized_score'] * metric_weight / total_metric_weight) * (cat_weight / 100.0)
            item['contribution_to_overall'] = round(contribution, 2)

        breakdown_data = {
            'categories': breakdown_categories,
            'metrics': breakdown_metrics,
        }

        self.write({
            'score_env': final_scores.get('E', 0.0),
            'score_social': final_scores.get('S', 0.0),
            'score_gov': final_scores.get('G', 0.0),
            'score_overall': overall_score,
            'suggested_esg_bonus_pct': suggested_bonus,
            'factor_breakdown': json.dumps(breakdown_data, indent=2),
            'computed_at': fields.Datetime.now(),
        })

    def _normalize_value(self, metric, raw_value):
        """Normalize raw value to 0-100 scale using bounds and direction."""
        span = metric.max_value - metric.min_value
        if span <= 0:
            return 100.0

        # Clip raw value to bounds
        clipped = max(metric.min_value, min(metric.max_value, raw_value))

        if metric.direction == 'higher_is_better':
            score = ((clipped - metric.min_value) / span) * 100.0
        else:  # lower_is_better
            score = ((metric.max_value - clipped) / span) * 100.0

        return round(score, 2)

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
