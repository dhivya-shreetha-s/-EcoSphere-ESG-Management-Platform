# -*- coding: utf-8 -*-
"""
Extension of hr.department to add the esg_sector_id Many2one.

We _inherit rather than _name = 'hr.department' so that we extend, not replace.
This is the minimal, non-disruptive way to attach EcoSphere data to departments.
"""
from odoo import fields, models


class HrDepartmentESGExt(models.Model):
    _inherit = 'hr.department'

    esg_sector_id = fields.Many2one(
        comodel_name='esg.sector',
        string='ESG Sector',
        ondelete='set null',
        index=True,
        help=(
            'Sector this department belongs to. '
            'Used for sector-level ESG score roll-up.'
        ),
    )
