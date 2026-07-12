# -*- coding: utf-8 -*-
"""
esg.csr.event.registration — Employee registration for a CSR event.

Handles append-only gamification ledger writes (anti-gaming design) when state
transitions to 'attended'.
"""
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class EsgCsrEventRegistration(models.Model):
    _name = 'esg.csr.event.registration'
    _description = 'CSR Event Registration'
    _order = 'event_id, state'

    event_id = fields.Many2one(
        comodel_name='esg.csr.event',
        string='Event',
        required=True,
        ondelete='cascade',
        index=True,
    )
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Employee',
        required=True,
        ondelete='cascade',
        index=True,
    )
    state = fields.Selection(
        selection=[
            ('registered', 'Registered'),
            ('attended', 'Attended'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='registered',
        index=True,
    )
    hours_attended = fields.Float(
        string='Hours Attended',
        default=0.0,
        help='Confirmed volunteer hours (set when state → attended).',
    )
    feedback = fields.Text(
        string='Feedback',
        help='P2 field — not shown in Phase 1/2 UI.',
    )
    xp_granted = fields.Boolean(
        string='XP Granted',
        default=False,
        help='Set to True by Phase 5 gamification engine after XP ledger write.',
    )

    # ------------------------------------------------------------------ #
    # Unique constraint: one registration per employee per event          #
    # ------------------------------------------------------------------ #
    _sql_constraints = [
        (
            'employee_event_unique',
            'UNIQUE(event_id, employee_id)',
            'An employee can only register once per event.',
        ),
    ]

    @api.constrains('hours_attended')
    def _check_hours(self):
        for rec in self:
            if rec.hours_attended < 0:
                raise ValidationError('Hours attended cannot be negative.')

    # ------------------------------------------------------------------ #
    # Phase 5: Gamification triggers & anti-double-award checks          #
    # ------------------------------------------------------------------ #
    def write(self, vals):
        """Trigger XP transaction log write when registration is marked Attended."""
        if 'state' in vals and vals['state'] == 'attended':
            for reg in self:
                if reg.state != 'attended' and not reg.xp_granted:
                    # Write to append-only ledger
                    self.env['esg.xp.ledger'].create({
                        'employee_id': reg.employee_id.id,
                        'delta_xp': reg.event_id.xp_award,
                        'reason': 'event_attended',
                        'reference_model': 'esg.csr.event.registration',
                        'reference_id': reg.id,
                        'verified_by_data': True,
                    })
                    # Set flag locally in vals
                    vals['xp_granted'] = True
        return super(EsgCsrEventRegistration, self).write(vals)
