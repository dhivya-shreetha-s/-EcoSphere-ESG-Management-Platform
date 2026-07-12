# -*- coding: utf-8 -*-
"""
esg.ai.log — Audit log for every xAI Grok API call.

Serves two purposes:
  1. Cost control: `prompt_hash` enables response caching (Phase 3 reads this
     before calling the API; if a recent matching hash exists and cached=True,
     the cached response is returned).
  2. Security/compliance audit: every call is logged with role_context and
     employee_id, supporting Phase 6's security pass.

Model is append-only. No records should ever be deleted outside of a
data-retention policy approved by the team.
"""
from odoo import fields, models


class EsgAiLog(models.Model):
    _name = 'esg.ai.log'
    _description = 'ESG AI Call Log'
    _order = 'created_at desc'

    feature = fields.Selection(
        selection=[
            ('explanation', 'Score Explanation'),
            ('action_items', 'Action Item Generation'),
            ('alert_narrative', 'Alert Narrative'),
            ('chat', 'AI Chat Assistant'),
            ('goal_coaching', 'Goal Coaching'),
        ],
        string='Feature',
        required=True,
        index=True,
    )
    role_context = fields.Selection(
        selection=[
            ('employee', 'Employee'),
            ('manager', 'Manager'),
            ('admin', 'Admin'),
        ],
        string='Role Context',
        required=True,
        index=True,
        help='Which role-scoped context builder was used for the prompt.',
    )
    employee_id = fields.Many2one(
        comodel_name='hr.employee',
        string='Requesting Employee',
        ondelete='set null',
        index=True,
        help='The Odoo user who triggered this AI call.',
    )
    prompt_hash = fields.Char(
        string='Prompt Hash (SHA-256)',
        index=True,
        help='SHA-256 of the prompt text, used for cache lookups.',
    )
    cached = fields.Boolean(
        string='Served from Cache',
        default=False,
        help='True = response was returned from cache; no API call made.',
    )
    tokens_used = fields.Integer(
        string='Tokens Used',
        default=0,
        help='Total tokens (prompt + completion) billed for this call.',
    )
    response_time_ms = fields.Integer(
        string='Response Time (ms)',
        help='Wall-clock time of the API call in milliseconds.',
    )
    error = fields.Text(
        string='Error',
        help='Empty = success. Contains error message or HTTP status on failure.',
    )
    created_at = fields.Datetime(
        string='Created At',
        required=True,
        default=fields.Datetime.now,
        index=True,
    )
