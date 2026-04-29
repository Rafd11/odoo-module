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
from odoo.exceptions import ValidationError


class HelpdeskTicketStatusChangeWizard(models.TransientModel):
    _name = 'helpdesk.ticket.status.change.wizard'
    _description = 'Helpdesk Ticket Status Change Wizard'

    ticket_id = fields.Many2one(
        'helpdesk.ticket',
        string='Ticket',
        required=True,
        readonly=True
    )
    old_state = fields.Selection(
        related='ticket_id.state',
        string='Current Status',
        readonly=True
    )
    new_state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('new', 'New'),
            ('assigned', 'Assigned'),
            ('in_progress', 'In Progress'),
            ('resolved', 'Resolved'),
            ('closed', 'Closed'),
            ('cancelled', 'Cancelled'),
        ],
        string='New Status',
        required=True
    )
    note = fields.Text(
        string='Note',
        help='Optional note about the status change'
    )
    send_notification = fields.Boolean(
        string='Send Notification',
        default=True,
        help='Send email notification to customer about status change'
    )
    notify_team = fields.Boolean(
        string='Notify Team',
        default=False,
        help='Send notification to team members'
    )

    @api.constrains('new_state', 'old_state')
    def _check_state_transition(self):
        """Validate state transition"""
        for wizard in self:
            if wizard.old_state == wizard.new_state:
                raise ValidationError(_('New status must be different from current status.'))
            
            # Define allowed transitions
            allowed_transitions = {
                'draft': ['new', 'cancelled'],
                'new': ['assigned', 'in_progress', 'cancelled'],
                'assigned': ['in_progress', 'new', 'cancelled'],
                'in_progress': ['resolved', 'assigned', 'cancelled'],
                'resolved': ['closed', 'in_progress', 'cancelled'],
                'closed': ['in_progress'],  # Reopen
                'cancelled': ['new'],  # Reactivate
            }
            
            if wizard.old_state in allowed_transitions:
                if wizard.new_state not in allowed_transitions[wizard.old_state]:
                    raise ValidationError(_(
                        'Invalid status transition from %s to %s. '
                        'Allowed transitions: %s'
                    ) % (
                        dict(wizard._fields['new_state'].selection)[wizard.old_state],
                        dict(wizard._fields['new_state'].selection)[wizard.new_state],
                        ', '.join([dict(wizard._fields['new_state'].selection)[s] 
                                  for s in allowed_transitions[wizard.old_state]])
                    ))

    def action_change_status(self):
        """Change ticket status"""
        self.ensure_one()
        
        # Validate transition
        self._check_state_transition()
        
        # Change status
        self.ticket_id.write({
            'state': self.new_state
        })
        
        # Create status history record
        self.env['helpdesk.ticket.status.history'].create({
            'ticket_id': self.ticket_id.id,
            'old_state': self.old_state,
            'new_state': self.new_state,
            'user_id': self.env.user.id,
            'note': self.note,
            'reason': 'manual'
        })
        
        # Send notifications
        if self.send_notification:
            self.ticket_id._send_status_change_notification(
                old_state=self.old_state,
                new_state=self.new_state,
                note=self.note
            )
        
        if self.notify_team and self.ticket_id.team_id:
            self.ticket_id._notify_team_status_change(
                old_state=self.old_state,
                new_state=self.new_state,
                note=self.note
            )
        
        return {
            'type': 'ir.actions.act_window_close'
        }
