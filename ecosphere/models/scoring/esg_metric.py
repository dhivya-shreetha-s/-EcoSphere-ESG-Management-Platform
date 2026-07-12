# -*- coding: utf-8 -*-
"""
esg.metric — Individual measurable factors that feed into E/S/G sub-scores.

Examples:
  - "Attendance Rate"       → Social, source: hr.attendance
  - "Fuel Consumption"      → Environmental, source: fleet.vehicle.log.fuel
  - "Policy Compliance %"   → Governance, source: esg.csr.event (custom)

The `weight` field here is the within-category weight; `esg.category.weight`
is the cross-category weight. Both are used in Phase 2's roll-up formula.

`direction` determines whether higher or lower raw values improve the score:
  - higher_is_better: attendance %, recycling rate
  - lower_is_better:  fuel consumption, paper waste
"""
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class EsgMetric(models.Model):
    _name = 'esg.metric'
    _description = 'ESG Metric'
    _order = 'category_id, sequence, name'

    name = fields.Char(string='Metric Name', required=True, translate=True)
    category_id = fields.Many2one(
        comodel_name='esg.category',
        string='ESG Category',
        required=True,
        ondelete='restrict',
        index=True,
    )
    data_source_id = fields.Many2one(
        comodel_name='esg.data.source',
        string='Data Source',
        ondelete='set null',
        help='Native Odoo model that supplies raw values for this metric.',
    )
    unit = fields.Char(
        string='Unit',
        help='Display unit, e.g. "%", "kWh", "kg CO₂", "hours".',
    )
    weight = fields.Float(
        string='Within-Category Weight (%)',
        default=100.0,
        digits=(6, 2),
        help='Weight of this metric within its ESG category (E, S, or G).',
    )
    direction = fields.Selection(
        selection=[
            ('higher_is_better', 'Higher is Better'),
            ('lower_is_better', 'Lower is Better'),
        ],
        string='Score Direction',
        required=True,
        default='higher_is_better',
    )
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)
    description = fields.Text(
        string='Description',
        translate=True,
        help='Shown in the explainability layer so users understand what this metric measures.',
    )

    # Normalisation bounds — used by Phase 2 to map raw values to 0–100
    min_value = fields.Float(
        string='Min Raw Value',
        default=0.0,
        help='Raw value corresponding to score = 0.',
    )
    max_value = fields.Float(
        string='Max Raw Value',
        default=100.0,
        help='Raw value corresponding to score = 100.',
    )

    # ------------------------------------------------------------------ #
    # Validation                                                           #
    # ------------------------------------------------------------------ #
    @api.constrains('weight')
    def _check_weight(self):
        for rec in self:
            if rec.weight <= 0:
                raise ValidationError(
                    f'Metric weight for "{rec.name}" must be greater than 0.'
                )

    @api.constrains('min_value', 'max_value')
    def _check_bounds(self):
        for rec in self:
            if rec.min_value >= rec.max_value:
                raise ValidationError(
                    f'Min value must be less than max value for metric "{rec.name}".'
                )
