# -*- coding: utf-8 -*-
"""
esg.ai.service — Shared AI service module for calling the xAI Grok API.

Implements standard requests, caching using esg.ai.log, fallback handling,
and template prompts for explaining scores, authoring recommendations,
mitigating alerts, and handling chat.
"""
from odoo import api, fields, models
import os
import requests
import hashlib
import json
import logging
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class EsgAiService(models.AbstractModel):
    _name = 'esg.ai.service'
    _description = 'ESG AI Integration Service'

    @api.model
    def _get_api_key(self):
        """Read API key from environmental variable."""
        return os.environ.get('GROK_API_KEY')

    @api.model
    def _get_model(self):
        """Read model name from environment variable, default to grok-4.5."""
        return os.environ.get('GROK_MODEL', 'grok-4.5')

    @api.model
    def _get_base_url(self):
        """Read base URL from environment variable, default to xAI endpoint."""
        return os.environ.get('GROK_BASE_URL', 'https://api.x.ai/v1')

    @api.model
    def _call_grok(self, prompt, system_instruction, feature, role, employee_id=False):
        """
        Low-level xAI Grok client. Implements SHA-256 caching and fallback handling.
        """
        api_key = self._get_api_key()
        if not api_key:
            _logger.warning("xAI API key not set. EcoSphere will run in fallback/offline mode.")
            return False

        # Compute SHA-256 hash of prompt and instructions
        payload_str = f"{system_instruction or ''}|||{prompt or ''}"
        prompt_hash = hashlib.sha256(payload_str.encode('utf-8')).hexdigest()

        # Check Cache (valid for 2 hours)
        cache_limit = fields.Datetime.now() - timedelta(hours=2)
        cached_log = self.env['esg.ai.log'].search([
            ('prompt_hash', '=', prompt_hash),
            ('error', '=', False),
            ('created_at', '>=', cache_limit)
        ], limit=1)

        # If cache exists, return it immediately without billing
        if cached_log:
            # We record a new log entry flagged as cached
            self.env['esg.ai.log'].create({
                'feature': feature,
                'role_context': role,
                'employee_id': employee_id,
                'prompt_hash': prompt_hash,
                'cached': True,
                'tokens_used': 0,
                'response_time_ms': 0,
            })
            # To fetch response text, we search the corresponding uncached response log
            original_log = self.env['esg.ai.log'].search([
                ('prompt_hash', '=', prompt_hash),
                ('error', '=', False),
                ('cached', '=', False)
            ], limit=1, order='created_at desc')
            if original_log and original_log.notes:
                return original_log.notes

        # Call Grok API with 5 seconds timeout
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        data = {
            'model': self._get_model(),
            'messages': [
                {'role': 'system', 'content': system_instruction},
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.7
        }

        url = f"{self._get_base_url().rstrip('/')}/chat/completions"
        start_time = datetime.now()
        error_msg = False
        response_text = ""
        tokens_used = 0

        try:
            res = requests.post(url, headers=headers, json=data, timeout=5)
            duration = int((datetime.now() - start_time).total_seconds() * 1000)

            if res.status_code == 200:
                res_data = res.json()
                response_text = res_data['choices'][0]['message']['content']
                tokens_used = res_data.get('usage', {}).get('total_tokens', 0)
            else:
                error_msg = f"HTTP {res.status_code}: {res.text}"
                _logger.error("xAI API error: %s", error_msg)
        except requests.exceptions.Timeout:
            duration = int((datetime.now() - start_time).total_seconds() * 1000)
            error_msg = "Request timed out (5s limit exceeded)"
            _logger.warning("xAI API timeout during request.")
        except Exception as e:
            duration = int((datetime.now() - start_time).total_seconds() * 1000)
            error_msg = str(e)
            _logger.error("xAI request failed: %s", error_msg)

        # Write to log
        log_vals = {
            'feature': feature,
            'role_context': role,
            'employee_id': employee_id,
            'prompt_hash': prompt_hash,
            'cached': False,
            'tokens_used': tokens_used,
            'response_time_ms': duration,
            'error': error_msg,
            'notes': response_text if not error_msg else False,  # use notes to store cached text
        }
        self.env['esg.ai.log'].create(log_vals)

        return response_text if not error_msg else False

    @api.model
    def get_score_explanation(self, score):
        """Generate score explanation with simple fallback if offline."""
        system_instruction = (
            "You are EcoSphere, a helpful sustainability analyst. Summarize "
            "the user's ESG score performance. Keep explanations under 3 sentences, "
            "positive, encouraging, and clear."
        )

        # Extract factor breakdown details for prompt
        breakdown = score.get_factor_breakdown()
        metrics_str = ""
        if breakdown and 'metrics' in breakdown:
            for m in breakdown['metrics']:
                metrics_str += f"- {m['name']}: Raw: {m['raw_value']} {m['unit']} (Normalized Score: {m['normalized_score']}/100)\n"

        prompt = (
            f"The subject scope is {score.scope}. Overall score is {score.score_overall}/100. "
            f"Environmental category: {score.score_env}/100. "
            f"Social category: {score.score_social}/100. "
            f"Governance category: {score.score_gov}/100.\n"
            f"Metrics detailed breakdown:\n{metrics_str}"
        )

        response = self._call_grok(
            prompt, system_instruction,
            feature='explanation',
            role=score.scope if score.scope in ('employee', 'manager', 'admin') else 'employee',
            employee_id=score.employee_id.id if score.scope == 'employee' else False
        )

        if not response:
            # Clean fallback message
            return (
                f"Your overall ESG Score is {score.score_overall:.1f} (Tier: {score.score_label.capitalize()}). "
                f"Environmental is {score.score_env:.1f}, Social is {score.score_social:.1f}, and "
                f"Governance is {score.score_gov:.1f}. Try raising your volunteering hours or reducing electricity "
                "consumption to improve your score."
            )
        return response

    @api.model
    def get_alert_narrative(self, alert):
        """Generate high-impact narrative for alert card."""
        system_instruction = (
            "Write a brief 1-sentence mitigative context for an ESG threshold alert. "
            "Be direct, highlight the operational impact, and suggest the first mitigation step."
        )
        prompt = (
            f"Alert Title: {alert.name}\n"
            f"Triggering Metric: {alert.metric_id.name if alert.metric_id else 'Threshold Limit'}\n"
            f"Threshold Value: {alert.threshold_value}\n"
            f"Actual Value: {alert.actual_value}\n"
            f"Severity: {alert.severity}\n"
            f"Operational Scope: {alert.scope} ({alert.department_id.name if alert.department_id else 'Company-wide'})\n"
        )

        response = self._call_grok(
            prompt, system_instruction,
            feature='alert_narrative',
            role='manager' if alert.target_role == 'manager' else 'admin'
        )

        if not response:
            return f"Action required: {alert.message} Crossed threshold of {alert.threshold_value}."
        return response

    @api.model
    def get_score_recommendations(self, score):
        """Return Grok-suggested action items based on gaps."""
        system_instruction = (
            "Analyze the ESG metrics and suggest exactly 3 actionable items to improve the score. "
            "Return a JSON array of objects with keys 'title', 'description', 'priority' ('high', 'medium', 'low'), "
            "and 'xp_reward' (integer between 50 and 150 based on task complexity)."
        )

        breakdown = score.get_factor_breakdown()
        metrics_str = ""
        if breakdown and 'metrics' in breakdown:
            for m in breakdown['metrics']:
                metrics_str += f"- Metric {m['name']} (ID {m['id']}): Normalized Score {m['normalized_score']}/100\n"

        prompt = (
            f"Scope: {score.scope}. Overall: {score.score_overall}. "
            f"E: {score.score_env}, S: {score.score_social}, G: {score.score_gov}.\n"
            f"Please identify the worst performing metrics and suggest mitigations.\n"
            f"Metrics list:\n{metrics_str}"
        )

        response = self._call_grok(
            prompt, system_instruction,
            feature='action_items',
            role=score.scope if score.scope in ('employee', 'manager', 'admin') else 'employee',
            employee_id=score.employee_id.id if score.scope == 'employee' else False
        )

        # Fallback recommendations if offline
        fallback_recs = [
            {
                'title': 'Attend Upcoming CSR Event',
                'description': 'Register and check-in to an active sustainability workshop or planting drive.',
                'priority': 'medium',
                'xp_reward': 100
            },
            {
                'title': 'Reduce Operational Electricity Usage',
                'description': 'Ensure all monitors and office workstations are shut down at the end of the day.',
                'priority': 'high',
                'xp_reward': 120
            },
            {
                'title': 'Complete ESG Policy Review',
                'description': 'Sign off the quarterly corporate policy list in the compliance folder.',
                'priority': 'low',
                'xp_reward': 50
            }
        ]

        if not response:
            return fallback_recs

        try:
            # Attempt to clean potential markdown wrappers (```json ... ```)
            cleaned = response.strip()
            if cleaned.startswith('```'):
                cleaned = '\n'.join(cleaned.split('\n')[1:-1])
            return json.loads(cleaned)
        except Exception:
            _logger.warning("Failed to parse Grok JSON recommendations. Falling back.")
            return fallback_recs
# Extend esg.ai.log to include cache text storage
class EsgAiLogExt(models.Model):
    _inherit = 'esg.ai.log'

    notes = fields.Text(string='Cached Response Text')
