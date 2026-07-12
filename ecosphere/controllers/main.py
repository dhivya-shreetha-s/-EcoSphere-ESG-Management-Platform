# -*- coding: utf-8 -*-
"""
EcoSphere controllers — Phase 1 stub.

Phase 3 will add JSON-RPC endpoints for:
  - /ecosphere/ai/chat       — AI assistant chat stream
  - /ecosphere/ai/explain    — score explanation request
  - /ecosphere/score/refresh — trigger scoring engine run

All endpoints will enforce Odoo session auth and role-scoped context.
"""
from odoo import http


class EcoSphereController(http.Controller):

    @http.route('/ecosphere/health', type='json', auth='user')
    def health_check(self):
        """Simple health-check endpoint. Returns module version."""
        return {
            'status': 'ok',
            'module': 'ecosphere',
            'version': '19.0.1.0.0',
        }
