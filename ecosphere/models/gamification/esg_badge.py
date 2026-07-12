# -*- coding: utf-8 -*-
"""
esg.badge — Gamification badge artwork and metadata.

Badges are awarded to employees via esg.reward records when they complete
an esg.challenge. Rarity tiers drive leaderboard visual differentiation.
"""
from odoo import fields, models


class EsgBadge(models.Model):
    _name = 'esg.badge'
    _description = 'ESG Badge'
    _order = 'rarity desc, name'

    name = fields.Char(string='Badge Name', required=True)
    description = fields.Text(string='Description')
    image = fields.Binary(
        string='Badge Image',
        attachment=True,
        help='Badge artwork. Displayed in Employee dashboard Rewards & Badges section.',
    )
    category_id = fields.Many2one(
        comodel_name='esg.category',
        string='ESG Pillar',
        ondelete='set null',
        help='Which pillar this badge is associated with.',
    )
    rarity = fields.Selection(
        selection=[
            ('common', 'Common'),
            ('rare', 'Rare'),
            ('epic', 'Epic'),
            ('legendary', 'Legendary'),
        ],
        string='Rarity',
        required=True,
        default='common',
    )
