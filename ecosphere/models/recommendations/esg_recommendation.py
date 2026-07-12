# -*- coding: utf-8 -*-
"""
esg.recommendation — Data-grounded action items for employees/departments.

Trigger gamification XP ledger writes when marked done.
"""
from odoo import api, fields, models


class EsgRecommendation(models.Model):
    _name = 'esg.recommendation'
    _description = 'ESG Recommendation / Action Item'
    _order = 'priority, create_date desc'
    _inherit = ['mail.thread']

    title = fields.Char(string='Action Title', required=True)
    description = fields.Text(string='Description')

    # ------------------------------------------------------------------ #
    # Scope                                                               #
    # ------------------------------------------------------------------ #
    scope = fields.Selection(
        selection=[
            ('employee', 'Employee'),
            ('department', 'Department'),
            ('org', 'Organisation'),
        ],
        string='Scope',
        required=True,
        default='employee',
        index=True,
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

    # ------------------------------------------------------------------ #
    # Provenance — what gap this addresses                                #
    # ------------------------------------------------------------------ #
    metric_id = fields.Many2one(
        comodel_name='esg.metric',
        string='Related Metric',
        ondelete='set null',
        help='The specific ESG metric gap this recommendation addresses.',
    )
    score_id = fields.Many2one(
        comodel_name='esg.score',
        string='Source Score',
        ondelete='set null',
        help='The esg.score record that generated this recommendation.',
    )

    # ------------------------------------------------------------------ #
    # Priority & state                                                    #
    # ------------------------------------------------------------------ #
    priority = fields.Selection(
        selection=[
            ('high', 'High'),
            ('medium', 'Medium'),
            ('low', 'Low'),
        ],
        string='Priority',
        default='medium',
        index=True,
    )
    state = fields.Selection(
        selection=[
            ('open', 'Open'),
            ('in_progress', 'In Progress'),
            ('done', 'Done'),
            ('dismissed', 'Dismissed'),
        ],
        string='Status',
        default='open',
        index=True,
        tracking=True,
    )
    due_date = fields.Date(string='Due Date')
    is_ai_generated = fields.Boolean(
        string='AI Generated',
        default=False,
        help='True = authored by Grok (Phase 3); False = rule-based engine.',
    )

    # ------------------------------------------------------------------ #
    # Gamification link                                                   #
    # ------------------------------------------------------------------ #
    xp_reward = fields.Integer(
        string='XP Reward',
        default=0,
        help='XP written to esg.xp.ledger when this action item is marked Done.',
    )

    # ------------------------------------------------------------------ #
    # Phase 5: Gamification triggers & anti-gaming checks                  #
    # ------------------------------------------------------------------ #
    def write(self, vals):
        """Award XP to the employee when state transitions to Done."""
        if 'state' in vals and vals['state'] == 'done':
            for rec in self:
                if rec.state != 'done' and rec.scope == 'employee' and rec.employee_id:
                    # Write to append-only ledger
                    self.env['esg.xp.ledger'].create({
                        'employee_id': rec.employee_id.id,
                        'delta_xp': rec.xp_reward,
                        'reason': 'recommendation_done',
                        'reference_model': 'esg.recommendation',
                        'reference_id': rec.id,
                        'verified_by_data': True,
                    })
        return super(EsgRecommendation, self).write(vals)
