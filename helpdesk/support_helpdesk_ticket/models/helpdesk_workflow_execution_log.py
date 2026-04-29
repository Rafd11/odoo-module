# -- coding: utf-8 --
##############################################################################
#                                                                            #
# Part of WebbyCrown Solutions (Website: www.webbycrown.com).                #
# Copyright © 2025 WebbyCrown Solutions. All Rights Reserved.                #
#                                                                            #
# This module is developed and maintained by WebbyCrown Solutions.           #
# Unauthorized copying of this file, via any medium, is strictly prohibited. #
# Licensed under the terms of the WebbyCrown Solutions License Agreement.    #
#                                                                            #
##############################################################################

import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class HelpdeskWorkflowExecutionLog(models.Model):
    _name = 'helpdesk.workflow.execution.log'
    _description = 'Workflow Rule Execution Log'
    _order = 'execution_date desc, id desc'
    _rec_name = 'display_name'

    rule_id = fields.Many2one(
        'helpdesk.workflow.rule',
        string='Workflow Rule',
        required=True,
        ondelete='cascade',
        index=True,
        help='The workflow rule that was executed'
    )
    ticket_id = fields.Many2one(
        'helpdesk.ticket',
        string='Ticket',
        required=True,
        ondelete='cascade',
        index=True,
        help='The ticket on which the rule was executed'
    )
    trigger_type = fields.Selection(
        [
            ('create', 'On Creation'),
            ('write', 'On Update'),
            ('state_change', 'On Status Change'),
            ('field_change', 'On Field Change'),
        ],
        string='Trigger Type',
        required=True,
        help='Type of trigger that caused rule execution'
    )
    status = fields.Selection(
        [
            ('executing', 'Executing'),
            ('success', 'Success'),
            ('error', 'Error'),
            ('skipped', 'Skipped'),
        ],
        string='Status',
        default='executing',
        required=True,
        help='Execution status of the rule'
    )
    execution_date = fields.Datetime(
        string='Execution Date',
        required=True,
        default=fields.Datetime.now,
        help='Date and time when the rule was executed'
    )
    error_message = fields.Text(
        string='Error Message',
        help='Error message if execution failed'
    )
    execution_time = fields.Float(
        string='Execution Time (seconds)',
        help='Time taken to execute the rule in seconds'
    )
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True,
        help='Display name for the log entry'
    )

    @api.depends('rule_id', 'ticket_id', 'execution_date', 'status')
    def _compute_display_name(self):
        """Compute display name"""
        for log in self:
            rule_name = log.rule_id.name if log.rule_id else _('Unknown Rule')
            ticket_number = log.ticket_id.ticket_number if log.ticket_id else _('Unknown Ticket')
            status_label = dict(log._fields['status'].selection).get(log.status, log.status)
            log.display_name = _('%s on %s - %s') % (rule_name, ticket_number, status_label)

    def action_view_ticket(self):
        """Open the ticket"""
        self.ensure_one()
        return {
            'name': _('Ticket'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket',
            'res_id': self.ticket_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_rule(self):
        """Open the workflow rule"""
        self.ensure_one()
        return {
            'name': _('Workflow Rule'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.workflow.rule',
            'res_id': self.rule_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
