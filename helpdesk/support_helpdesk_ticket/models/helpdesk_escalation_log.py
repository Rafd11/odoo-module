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

from odoo import models, fields, api, _


class HelpdeskEscalationLog(models.Model):
    _name = 'helpdesk.escalation.log'
    _description = 'Escalation Execution Log'
    _order = 'escalation_date desc, id desc'
    _rec_name = 'display_name'

    rule_id = fields.Many2one(
        'helpdesk.escalation.rule',
        string='Escalation Rule',
        required=True,
        ondelete='cascade',
        index=True,
        help='The escalation rule that was executed'
    )
    ticket_id = fields.Many2one(
        'helpdesk.ticket',
        string='Ticket',
        required=True,
        ondelete='cascade',
        index=True,
        help='The ticket that was escalated'
    )
    escalation_date = fields.Datetime(
        string='Escalation Date',
        required=True,
        default=fields.Datetime.now,
        help='Date and time when escalation occurred'
    )
    escalation_level = fields.Integer(
        string='Escalation Level',
        default=1,
        help='Level of escalation (1 = first, 2 = second, etc.)'
    )
    trigger_type = fields.Selection(
        string='Trigger Type',
        related='rule_id.trigger_type',
        store=True,
        help='Type of trigger that caused escalation'
    )
    action_type = fields.Selection(
        string='Action Type',
        related='rule_id.action_type',
        store=True,
        help='Action that was executed'
    )
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True,
        help='Display name for the escalation log entry'
    )

    @api.depends('rule_id', 'ticket_id', 'escalation_date', 'escalation_level')
    def _compute_display_name(self):
        """Compute display name"""
        for log in self:
            rule_name = log.rule_id.name if log.rule_id else _('Unknown Rule')
            ticket_number = log.ticket_id.ticket_number if log.ticket_id else _('Unknown Ticket')
            log.display_name = _('%s - Level %d on %s') % (rule_name, log.escalation_level, ticket_number)

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
        """Open the escalation rule"""
        self.ensure_one()
        return {
            'name': _('Escalation Rule'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.escalation.rule',
            'res_id': self.rule_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
