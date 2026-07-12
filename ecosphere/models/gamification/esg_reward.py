# -*- coding: utf-8 -*-
"""
esg.reward — Records a badge award to a specific employee.

Created by Phase 5 gamification engine when an esg.challenge is verified complete.
Provides the "Rewards & Badges" list on the Employee dashboard.
"""
from odoo import fields, models


class EsgReward(models.Model):
    _name = 'esg.reward'
    _description = 'ESG Reward (Badge Award)'
    _order = 'awarded_at desc'

    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Employee',
        required=True,
        ondelete='cascade',
        index=True,
    )
    badge_id = fields.Many2one(
        comodel_name='esg.badge',
        string='Badge',
        required=True,
        ondelete='cascade',
    )
    challenge_id = fields.Many2one(
        comodel_name='esg.challenge',
        string='Source Challenge',
        ondelete='set null',
        help='Which challenge completion triggered this award.',
    )
    awarded_at = fields.Datetime(
        string='Awarded At',
        required=True,
        default=fields.Datetime.now,
    )
    xp_at_award = fields.Integer(
        string='XP Total At Award',
        help='Snapshot of the employee\'s cumulative XP at the moment of award.',
    )
