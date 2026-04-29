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

_logger = None


class HelpdeskTicketAssignmentHistory(models.Model):
    _name = 'helpdesk.ticket.assignment.history'
    _description = 'Ticket Assignment History'
    _order = 'assignment_date desc, id desc'
    _rec_name = 'display_name'

    ticket_id = fields.Many2one(
        'helpdesk.ticket',
        string='Ticket',
        required=True,
        ondelete='cascade',
        index=True,
        help='The ticket that was assigned'
    )
    old_user_id = fields.Many2one(
        'res.users',
        string='Previous Assignee',
        index=True,
        help='User who was previously assigned'
    )
    new_user_id = fields.Many2one(
        'res.users',
        string='New Assignee',
        required=True,
        index=True,
        help='User who is now assigned'
    )
    old_team_id = fields.Many2one(
        'helpdesk.team',
        string='Previous Team',
        index=True,
        help='Team that was previously assigned'
    )
    new_team_id = fields.Many2one(
        'helpdesk.team',
        string='New Team',
        index=True,
        help='Team that is now assigned'
    )
    assignment_date = fields.Datetime(
        string='Assignment Date',
        required=True,
        default=fields.Datetime.now,
        index=True,
        help='Date and time when assignment was made'
    )
    assigned_by_id = fields.Many2one(
        'res.users',
        string='Assigned By',
        required=True,
        default=lambda self: self.env.user,
        help='User who made the assignment'
    )
    assignment_method = fields.Selection(
        [
            ('manual', 'Manual'),
            ('workflow', 'Workflow Rule'),
            ('round_robin', 'Round-Robin Algorithm'),
            ('workload_based', 'Workload-Based Algorithm'),
            ('skill_based', 'Skill-Based Algorithm'),
            ('team_based', 'Team-Based Assignment'),
            ('escalation', 'Escalation'),
            ('sla', 'SLA Rule'),
        ],
        string='Assignment Method',
        required=True,
        default='manual',
        help='Method used to assign the ticket'
    )
    workflow_rule_id = fields.Many2one(
        'helpdesk.workflow.rule',
        string='Workflow Rule',
        help='Workflow rule that triggered this assignment (if applicable)'
    )
    note = fields.Text(
        string='Note',
        help='Optional note about the assignment'
    )
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True,
        help='Display name for the assignment history entry'
    )

    @api.depends('ticket_id', 'old_user_id', 'new_user_id', 'assignment_date', 'assignment_method')
    def _compute_display_name(self):
        """Compute display name"""
        for history in self:
            ticket_number = history.ticket_id.ticket_number if history.ticket_id else _('Unknown Ticket')
            old_user = history.old_user_id.name if history.old_user_id else _('Unassigned')
            new_user = history.new_user_id.name if history.new_user_id else _('Unassigned')
            method_label = dict(history._fields['assignment_method'].selection).get(history.assignment_method, history.assignment_method)
            history.display_name = _('%s: %s → %s (%s)') % (ticket_number, old_user, new_user, method_label)

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

    def action_view_old_user(self):
        """Open the previous assignee"""
        self.ensure_one()
        if not self.old_user_id:
            return False
        return {
            'name': _('Previous Assignee'),
            'type': 'ir.actions.act_window',
            'res_model': 'res.users',
            'res_id': self.old_user_id.id,
            'view_mode': 'form',
            'target': 'new',
        }

    def action_view_new_user(self):
        """Open the new assignee"""
        self.ensure_one()
        return {
            'name': _('New Assignee'),
            'type': 'ir.actions.act_window',
            'res_model': 'res.users',
            'res_id': self.new_user_id.id,
            'view_mode': 'form',
            'target': 'new',
        }
