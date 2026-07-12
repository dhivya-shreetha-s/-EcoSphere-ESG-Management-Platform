# -*- coding: utf-8 -*-
"""
esg.xp.ledger — Immutable transaction log for gamification XP.

DESIGN PRINCIPLE (anti-gaming, audit trail):
  - Total XP is ALWAYS computed as SUM(delta_xp) on this ledger.
  - It is NEVER stored as a cached integer on hr.employee.
  - Reversals are first-class entries (delta_xp < 0, reason='reversal').
  - `verified_by_data` = True means the XP delta was triggered by a confirmed
    real-data change (e.g. metric threshold crossed, event attendance confirmed).
    False means manually granted (admin only) — these are flagged for audit.
  - Records in this table are append-only. No update/delete allowed for non-admin.

Leaderboard query in Phase 5:
  SELECT employee_id, SUM(delta_xp) AS total_xp
  FROM esg_xp_ledger
  GROUP BY employee_id
  ORDER BY total_xp DESC
"""
from odoo import fields, models


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
