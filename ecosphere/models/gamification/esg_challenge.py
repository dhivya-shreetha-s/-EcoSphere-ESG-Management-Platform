# -*- coding: utf-8 -*-
"""
esg.challenge — Gamification challenges tied to verified data changes.

ANTI-GAMING DESIGN:
  - `metric_id` points to the specific ESG metric that must change in real data.
  - `direction` mirrors the metric's direction: completing a challenge requires
    a genuine data improvement, not just self-reporting.
  - Challenges are verified by the Phase 5 engine by re-querying the live
    esg.metric value; the system never accepts user-provided completion evidence.
  - Disabling data collection (e.g., deleting attendance records) cannot
    improve a score — the metric would simply show no data, not a higher value.
"""
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class EsgChallenge(models.Model):
    _name = 'esg.challenge'
    _description = 'ESG Gamification Challenge'
    _order = 'sequence, name'

    name = fields.Char(string='Challenge Name', required=True)
    description = fields.Text(string='Description')
    sequence = fields.Integer(string='Sequence', default=10)

    metric_id = fields.Many2one(
        comodel_name='esg.metric',
        string='Target Metric',
        required=True,
        ondelete='restrict',
        help='The real ESG metric this challenge requires to change.',
    )
    target_value = fields.Float(
        string='Target Value',
        required=True,
        help='Metric value threshold required to complete this challenge.',
    )
    direction = fields.Selection(
        selection=[
            ('higher_is_better', 'Reach or exceed target'),
            ('lower_is_better', 'Reach or go below target'),
        ],
        string='Completion Condition',
        required=True,
        default='higher_is_better',
    )
    xp_reward = fields.Integer(
        string='XP Reward',
        required=True,
        default=50,
        help='XP written to esg.xp.ledger on verified completion.',
    )
    badge_id = fields.Many2one(
        comodel_name='esg.badge',
        string='Award Badge',
        ondelete='set null',
        help='Badge awarded via esg.reward on completion.',
    )
    scope = fields.Selection(
        selection=[
            ('employee', 'Individual Employee'),
            ('department', 'Department'),
        ],
        string='Scope',
        required=True,
        default='employee',
    )
    active = fields.Boolean(string='Active', default=True)

    @api.constrains('xp_reward')
    def _check_xp(self):
        for rec in self:
            if rec.xp_reward <= 0:
                raise ValidationError('XP Reward must be greater than 0.')
