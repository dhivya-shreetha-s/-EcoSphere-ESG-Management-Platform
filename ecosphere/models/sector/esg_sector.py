# -*- coding: utf-8 -*-
"""
esg.sector — Standalone sector model.

Sectors group one or more hr.department records into a business unit above
the department level. They drive the sector-level ESG score roll-up in Phase 2
and the Admin's sector performance intelligence view in Phase 4.

Architectural decision (locked in Phase 1 plan):
  Use a standalone model with Many2one on hr.department, NOT a tag/field added
  directly to hr.department. This avoids patching a core model and gives us a
  clean admin UI.
"""
from odoo import api, fields, models


class EsgSector(models.Model):
    _name = 'esg.sector'
    _description = 'ESG Sector'
    _order = 'sequence, name'
    _rec_name = 'name'

    name = fields.Char(
        string='Sector Name',
        required=True,
        translate=True,
        help='Human-readable sector label, e.g. "Information Technology", "Operations".',
    )
    code = fields.Char(
        string='Sector Code',
        size=10,
        help='Short identifier used in reports and API context builders, e.g. "IT", "OPS".',
    )
    description = fields.Text(string='Description', translate=True)
    sequence = fields.Integer(string='Sequence', default=10)
    active = fields.Boolean(string='Active', default=True)

    department_ids = fields.One2many(
        comodel_name='hr.department',
        inverse_name='esg_sector_id',
        string='Departments',
        help='Departments that belong to this sector.',
    )

    # Computed summary — implemented in Phase 2
    department_count = fields.Integer(
        string='# Departments',
        compute='_compute_department_count',
        store=True,
    )

    @api.depends('department_ids')
    def _compute_department_count(self):
        for sector in self:
            sector.department_count = len(sector.department_ids)

    # ------------------------------------------------------------------ #
    # Phase 1 constraint: unique code per sector                          #
    # ------------------------------------------------------------------ #
    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Sector code must be unique.'),
    ]
