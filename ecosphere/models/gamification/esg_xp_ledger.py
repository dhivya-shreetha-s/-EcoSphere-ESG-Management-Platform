# -*- coding: utf-8 -*-
"""
esg.xp.ledger — Immutable transaction log for gamification XP.

Contains the live leaderboard aggregator logic.
"""
from odoo import api, fields, models


class EsgXpLedger(models.Model):
    _name = 'esg.xp.ledger'
    _description = 'ESG XP Ledger (Transaction Log)'
    _order = 'created_at desc'

    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Employee',
        required=True,
        ondelete='cascade',
        index=True,
    )
    delta_xp = fields.Integer(
        string='XP Delta',
        required=True,
        help='Positive = XP earned. Negative = XP reversal.',
    )
    reason = fields.Selection(
        selection=[
            ('challenge_complete', 'Challenge Completed'),
            ('event_attended', 'CSR Event Attended'),
            ('score_milestone', 'Score Milestone Reached'),
            ('recommendation_done', 'Action Item Completed'),
            ('reversal', 'Reversal / Correction'),
            ('admin_grant', 'Admin Manual Grant'),
        ],
        string='Reason',
        required=True,
        index=True,
    )
    reference_model = fields.Char(
        string='Reference Model',
        help='e.g. "esg.challenge", "esg.csr.event.registration".',
    )
    reference_id = fields.Integer(
        string='Reference ID',
        help='ID of the record in reference_model that triggered this entry.',
    )
    verified_by_data = fields.Boolean(
        string='Verified by Real Data',
        default=False,
        help=(
            'True = XP was triggered by a confirmed real-data change. '
            'False = manually granted; flagged for audit.'
        ),
    )
    notes = fields.Text(
        string='Audit Notes',
        help='Anti-gaming audit trail. Required when verified_by_data=False.',
    )
    created_at = fields.Datetime(
        string='Created At',
        required=True,
        default=fields.Datetime.now,
        index=True,
    )

    # ------------------------------------------------------------------ #
    # Phase 5: Leaderboard live aggregation                               #
    # ------------------------------------------------------------------ #
    @api.model
    def get_leaderboard(self, scope, target_id=False, limit=10):
        """
        Aggregate ledger delta_xp sums grouped by employee.
        
        :param scope: Selection ('employee', 'department', 'sector', 'org')
        :param target_id: ID of the corresponding target record
        :param limit: Integer
        :return: List of dicts: [{'rank': 1, 'employee_name': '...', 'xp': 250}]
        """
        domain = []
        if scope == 'department' and target_id:
            domain.append(('employee_id.department_id', '=', target_id))
        elif scope == 'sector' and target_id:
            domain.append(('employee_id.department_id.esg_sector_id', '=', target_id))

        # Query read_group
        groups = self.read_group(
            domain=domain,
            fields=['employee_id', 'delta_xp:sum'],
            groupby=['employee_id'],
            orderby='delta_xp desc',
            limit=limit
        )

        leaderboard = []
        for i, group in enumerate(groups, start=1):
            emp = group['employee_id']
            if emp:
                leaderboard.append({
                    'rank': i,
                    'employee_id': emp[0],
                    'employee_name': emp[1],
                    'xp': group['delta_xp'],
                })

        return leaderboard
