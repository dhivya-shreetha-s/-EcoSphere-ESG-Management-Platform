# -*- coding: utf-8 -*-
"""
esg.category — The three ESG pillars: Environmental, Social, Governance.

Seeded at install time via data/esg_category_data.xml (E, S, G).
The `weight` field drives the overall-score composite formula in Phase 2.
Weights are stored here (not hardcoded) so the Admin "ESG Score Weightage"
setting in Phase 4 has a live data source to write to and re-trigger recompute.
"""
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class EsgCategory(models.Model):
    _name = 'esg.category'
    _description = 'ESG Category (E / S / G)'
    _order = 'sequence'
    _rec_name = 'name'

    name = fields.Char(
        string='Category Name',
        required=True,
        translate=True,
        help='e.g. "Environmental", "Social", "Governance".',
    )
    code = fields.Selection(
        selection=[
            ('E', 'Environmental'),
            ('S', 'Social'),
            ('G', 'Governance'),
        ],
        string='Code',
        required=True,
    )
    color = fields.Integer(
        string='Color Index',
        default=0,
        help='Odoo kanban color index (0–11).',
    )
    weight = fields.Float(
        string='Weight (%)',
        default=33.33,
        digits=(6, 2),
        help=(
            'Percentage weight in the overall ESG composite score. '
            'The three category weights should sum to 100. '
            'Adjusted by Admin in the ESG Score Weightage settings.'
        ),
    )
    sequence = fields.Integer(string='Sequence', default=10)
    description = fields.Text(string='Description', translate=True)

    metric_ids = fields.One2many(
        comodel_name='esg.metric',
        inverse_name='category_id',
        string='Metrics',
    )

    # ------------------------------------------------------------------ #
    # Validation                                                           #
    # ------------------------------------------------------------------ #
    @api.constrains('weight')
    def _check_weight_positive(self):
        for rec in self:
            if rec.weight <= 0:
                raise ValidationError(
                    f'Weight for category "{rec.name}" must be greater than 0.'
                )

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Each ESG category code (E/S/G) must be unique.'),
    ]
