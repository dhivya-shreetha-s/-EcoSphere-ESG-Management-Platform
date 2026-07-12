# -*- coding: utf-8 -*-
"""
EcoSphere Controllers — AI Chat & Health check routing.

Registers JSON-RPC routes for the interactive OWL chat widgets.
Determines role context (Employee, Manager, Admin) server-side and enriches
Grok prompts with live Odoo metrics to enforce context safety.
"""
from odoo import http
from odoo.http import request
import logging

_logger = logging.getLogger(__name__)


class EcoSphereController(http.Controller):

    @http.route('/ecosphere/health', type='json', auth='user')
    def health_check(self):
        """Simple health-check endpoint. Returns module version."""
        return {
            'status': 'ok',
            'module': 'ecosphere',
            'version': '19.0.1.0.0',
        }

    @http.route('/ecosphere/ai/chat', type='json', auth='user')
    def ai_chat(self, message, conversation_history=None):
        """
        Interactive chat routing endpoint.
        Determines user security group to construct role-scoped context prompts.
        """
        user = request.env.user
        ai_service = request.env['esg.ai.service']
        
        # 1. Determine active role and context
        role = 'employee'
        system_instruction = (
            "You are the EcoSphere ESG Employee Assistant. Give the employee personalized, "
            "actionable sustainability coaching based on their metrics. Be encouraging and concise."
        )
        context_data = ""

        # Enforce server-side security groups
        if user.has_group('ecosphere.group_esg_admin'):
            role = 'admin'
            system_instruction = (
                "You are the EcoSphere ESG Executive Dashboard Advisor. Provide organization-wide "
                "sustainability strategy, compliance insights, and risk assessments. Keep answers strategic."
            )
            # Pull org-wide scores for prompt context
            score = request.env['esg.score'].search([('scope', '=', 'org')], limit=1, order='period_start desc')
            if score:
                context_data = (
                    f"Organization Overall Score: {score.score_overall:.1f}/100. "
                    f"E: {score.score_env:.1f}, S: {score.score_social:.1f}, G: {score.score_gov:.1f}."
                )

        elif user.has_group('ecosphere.group_esg_manager'):
            role = 'manager'
            system_instruction = (
                "You are the EcoSphere ESG Department Advisor. Answer questions about department-level "
                "performance metrics, CSR events, and team engagement. Be supportive and professional."
            )
            # Pull department scores for prompt context
            dept_id = user.employee_id.department_id.id
            if dept_id:
                score = request.env['esg.score'].search([
                    ('scope', '=', 'department'),
                    ('department_id', '=', dept_id)
                ], limit=1, order='period_start desc')
                if score:
                    context_data = (
                        f"Department Score: {score.score_overall:.1f}/100. "
                        f"E: {score.score_env:.1f}, S: {score.score_social:.1f}, G: {score.score_gov:.1f}."
                    )

        else:
            # Employee scope
            emp_id = user.employee_id.id
            if emp_id:
                score = request.env['esg.score'].search([
                    ('scope', '=', 'employee'),
                    ('employee_id', '=', emp_id)
                ], limit=1, order='period_start desc')
                if score:
                    context_data = (
                        f"Employee Score: {score.score_overall:.1f}/100. "
                        f"E: {score.score_env:.1f}, S: {score.score_social:.1f}, G: {score.score_gov:.1f}."
                    )

        # 2. Format final prompt including history and context
        history_str = ""
        if conversation_history:
            for turn in conversation_history[-5:]:  # keep context window small/cost-effective
                history_str += f"{turn['role'].capitalize()}: {turn['content']}\n"

        prompt = (
            f"Active User: {user.name} (Role: {role.capitalize()})\n"
            f"Live Context Metrics: {context_data}\n\n"
            f"Conversation History:\n{history_str}"
            f"User message: {message}\n"
        )

        response = ai_service._call_grok(
            prompt, system_instruction,
            feature='chat',
            role=role,
            employee_id=user.employee_id.id
        )

        if not response:
            return {
                'response': "I'm currently running in offline fallback mode. "
                            "Please check your network connection or verify that the Grok API key is configured."
            }

        return {
            'response': response
        }
