# -*- coding: utf-8 -*-
"""
esg.challenge — Gamification challenges tied to verified data changes.

Contains the challenge verification scheduler that awards XP and badges.
"""
from odoo import api, fields, models
from odoo.exceptions import ValidationError
from datetime import date, timedelta


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

    # ------------------------------------------------------------------ #
    # Phase 5: Verification scheduling engine                             #
    # ------------------------------------------------------------------ #
    @api.model
    def verify_active_challenges(self):
        """
        Verify completions.
        Queries EsgDataAggregator for active scopes. If actual value satisfies
        threshold, awards XP and Badge to the employee.
        """
        challenges = self.search([('active', '=', True)])
        aggregator = self.env['esg.data.aggregator']

        for chal in challenges:
            if chal.scope == 'employee':
                employees = self.env['hr.employee'].search([])
                for emp in employees:
                    # Check if already rewarded
                    reward_exists = self.env['esg.reward'].search_count([
                        ('employee_id', '=', emp.id),
                        ('challenge_id', '=', chal.id)
                    ])
                    if reward_exists > 0:
                        continue

                    # Retrieve raw value over trailing 30 days
                    start_date = date.today() - timedelta(days=30)
                    end_date = date.today()
                    actual_val = aggregator.get_raw_value(
                        chal.metric_id, 'employee', emp.id, start_date, end_date
                    )

                    # Assess completion condition
                    completed = False
                    if chal.direction == 'higher_is_better' and actual_val >= chal.target_value:
                        completed = True
                    elif chal.direction == 'lower_is_better' and actual_val <= chal.target_value:
                        completed = True

                    if completed:
                        # Write transaction log
                        self.env['esg.xp.ledger'].create({
                            'employee_id': emp.id,
                            'delta_xp': chal.xp_reward,
                            'reason': 'challenge_complete',
                            'reference_model': 'esg.challenge',
                            'reference_id': chal.id,
                            'verified_by_data': True,
                        })

                        # Award badge reward
                        if chal.badge_id:
                            # Sum current XP for snapshot
                            xps = self.env['esg.xp.ledger'].read_group(
                                [('employee_id', '=', emp.id)], ['delta_xp:sum'], []
                            )
                            total_xp = xps[0].get('delta_xp') or 0
                            self.env['esg.reward'].create({
                                'employee_id': emp.id,
                                'badge_id': chal.badge_id.id,
                                'challenge_id': chal.id,
                                'xp_at_award': total_xp,
                            })
