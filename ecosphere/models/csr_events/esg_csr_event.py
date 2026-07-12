# -*- coding: utf-8 -*-
"""
esg.csr.event — CSR / sustainability events.

Shared model: Employee's "Sustainability Events" list and Manager's
"CSR Event Management" CRUD both read/write this same model. No duplication.

Manager creates and approves events (state: draft → approved).
Employees register (esg.csr.event.registration).
After the event, the Manager marks it completed; XP is granted in Phase 5.
"""
from odoo import api, fields, models
from odoo.exceptions import ValidationError


class EsgCsrEvent(models.Model):
    _name = 'esg.csr.event'
    _description = 'CSR / Sustainability Event'
    _order = 'event_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(string='Event Name', required=True)
    description = fields.Text(string='Description')
    event_date = fields.Date(string='Event Date', required=True, index=True)
    location = fields.Char(string='Location')

    organizer_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Organiser',
        ondelete='set null',
        help='Manager who created this event.',
    )
    department_id = fields.Many2one(
        comodel_name='hr.department',
        string='Department',
        ondelete='set null',
        index=True,
    )
    category_id = fields.Many2one(
        comodel_name='esg.category',
        string='ESG Pillar',
        ondelete='set null',
        help='Which E/S/G pillar this event contributes to.',
    )

    max_participants = fields.Integer(
        string='Max Participants',
        default=50,
    )
    state = fields.Selection(
        selection=[
            ('draft', 'Draft'),
            ('approved', 'Approved'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        index=True,
        tracking=True,
    )

    registration_ids = fields.One2many(
        comodel_name='esg.csr.event.registration',
        inverse_name='event_id',
        string='Registrations',
    )
    registration_count = fields.Integer(
        string='Registrations',
        compute='_compute_registration_count',
        store=True,
    )

    volunteer_hours = fields.Float(
        string='Total Volunteer Hours',
        compute='_compute_volunteer_hours',
        store=True,
        help='Sum of hours_attended for attended registrations.',
    )
    xp_award = fields.Integer(
        string='XP Per Participant',
        default=100,
        help='XP written to esg.xp.ledger per confirmed attendee in Phase 5.',
    )

    @api.depends('registration_ids')
    def _compute_registration_count(self):
        for event in self:
            event.registration_count = len(event.registration_ids)

    @api.depends('registration_ids.hours_attended', 'registration_ids.state')
    def _compute_volunteer_hours(self):
        for event in self:
            event.volunteer_hours = sum(
                r.hours_attended
                for r in event.registration_ids
                if r.state == 'attended'
            )

    # ------------------------------------------------------------------ #
    # Workflow actions                                                     #
    # ------------------------------------------------------------------ #
    def action_approve(self):
        self.write({'state': 'approved'})

    def action_complete(self):
        self.write({'state': 'completed'})

    def action_cancel(self):
        self.write({'state': 'cancelled'})

    # ------------------------------------------------------------------ #
    # Validation                                                           #
    # ------------------------------------------------------------------ #
    @api.constrains('max_participants')
    def _check_max_participants(self):
        for rec in self:
            if rec.max_participants < 1:
                raise ValidationError('Max Participants must be at least 1.')
