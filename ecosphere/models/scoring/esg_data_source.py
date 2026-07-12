# -*- coding: utf-8 -*-
"""
esg.data.source — Maps each ESG metric to its native Odoo model/field.

The `installed` field is computed at record load time by checking whether
the target model exists in the Odoo model registry. This is the runtime
discovery mechanism committed to in Phase 1 (see OQ-3 in the plan): the
Phase 2 scoring engine reads `installed` to decide whether to run a live
query or skip/proxy for that data source.
"""
from odoo import api, fields, models


class EsgDataSource(models.Model):
    _name = 'esg.data.source'
    _description = 'ESG Data Source'
    _order = 'name'

    name = fields.Char(string='Name', required=True)
    model_name = fields.Char(
        string='Odoo Model',
        required=True,
        help='Technical name of the Odoo model that provides raw data, '
             'e.g. "hr.attendance", "fleet.vehicle", "account.move".',
    )
    field_name = fields.Char(
        string='Field / Domain',
        help='Field or aggregation domain within the model, e.g. "check_in", '
             'or a JSON-encoded domain string for filtered record counts.',
    )
    description = fields.Text(string='Description')

    # Computed — True only when the model is present in this Odoo instance
    installed = fields.Boolean(
        string='Available',
        compute='_compute_installed',
        store=False,   # intentionally not stored — checked fresh each time
        help='Whether the source model is currently installed on this instance.',
    )

    @api.depends('model_name')
    def _compute_installed(self):
        for rec in self:
            rec.installed = rec.model_name in self.env

    # Convenience method called by Phase 2 scoring engine
    def is_available(self):
        """Return True if this data source's model is installed."""
        self.ensure_one()
        return self.model_name in self.env
