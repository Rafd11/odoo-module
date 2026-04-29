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
from odoo.exceptions import ValidationError, UserError


class HelpdeskTicketMergeWizard(models.TransientModel):
    _name = 'helpdesk.ticket.merge.wizard'
    _description = 'Helpdesk Ticket Merge Wizard'

    ticket_id = fields.Many2one(
        'helpdesk.ticket',
        string='Master Ticket',
        required=True,
        readonly=True,
        help='The ticket that will remain after merge (master ticket)'
    )
    ticket_ids = fields.Many2many(
        'helpdesk.ticket',
        'helpdesk_ticket_merge_wizard_rel',
        'wizard_id',
        'ticket_id',
        string='Tickets to Merge',
        required=True,
        domain="[('id', '!=', ticket_id), ('state', 'not in', ['closed', 'cancelled'])]",
        help='Tickets that will be merged into the master ticket'
    )
    merge_messages = fields.Boolean(
        string='Merge Messages',
        default=True,
        help='Copy all messages from merged tickets to master ticket'
    )
    merge_attachments = fields.Boolean(
        string='Merge Attachments',
        default=True,
        help='Copy all attachments from merged tickets to master ticket'
    )
    merge_activities = fields.Boolean(
        string='Merge Activities',
        default=True,
        help='Copy all activities from merged tickets to master ticket'
    )
    merge_links = fields.Boolean(
        string='Merge Linked Records',
        default=True,
        help='Copy all linked records from merged tickets to master ticket'
    )
    close_merged_tickets = fields.Boolean(
        string='Close Merged Tickets',
        default=True,
        help='Close the merged tickets after merge'
    )
    note = fields.Text(
        string='Merge Note',
        help='Optional note about the merge operation'
    )

    @api.constrains('ticket_id', 'ticket_ids')
    def _check_tickets(self):
        """Ensure master ticket is not in tickets to merge"""
        for wizard in self:
            if wizard.ticket_id in wizard.ticket_ids:
                raise ValidationError(_('Master ticket cannot be in the list of tickets to merge.'))

    def action_merge_tickets(self):
        """Merge selected tickets into master ticket"""
        self.ensure_one()
        if not self.ticket_ids:
            raise UserError(_('Please select at least one ticket to merge.'))

        master_ticket = self.ticket_id
        tickets_to_merge = self.ticket_ids

        # Validate tickets can be merged
        self._validate_merge(tickets_to_merge)

        # Merge messages
        if self.merge_messages:
            self._merge_messages(master_ticket, tickets_to_merge)

        # Merge attachments
        if self.merge_attachments:
            self._merge_attachments(master_ticket, tickets_to_merge)

        # Merge activities
        if self.merge_activities:
            self._merge_activities(master_ticket, tickets_to_merge)

        # Merge linked records
        if self.merge_links:
            self._merge_links(master_ticket, tickets_to_merge)

        # Add merge note
        if self.note:
            master_ticket.message_post(
                body=_('Merge Note: %s') % self.note,
                subject=_('Ticket Merge')
            )

        # Create merge history record
        self._create_merge_history(master_ticket, tickets_to_merge)

        # Close merged tickets if requested
        if self.close_merged_tickets:
            tickets_to_merge.write({
                'state': 'closed',
                'internal_note': (tickets_to_merge.internal_note or '') + _('\n\n[Merged into %s]') % master_ticket.ticket_number
            })

        # Post merge notification
        master_ticket.message_post(
            body=_('Merged %d ticket(s): %s') % (
                len(tickets_to_merge),
                ', '.join(tickets_to_merge.mapped('ticket_number'))
            ),
            subject=_('Tickets Merged')
        )

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket',
            'res_id': master_ticket.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _validate_merge(self, tickets):
        """Validate that tickets can be merged"""
        for ticket in tickets:
            if ticket.state in ['closed', 'cancelled']:
                raise ValidationError(_('Cannot merge closed or cancelled tickets: %s') % ticket.ticket_number)

    def _merge_messages(self, master_ticket, tickets):
        """Merge messages from tickets to master ticket"""
        for ticket in tickets:
            # Get all messages from the ticket
            messages = self.env['mail.message'].search([
                ('model', '=', 'helpdesk.ticket'),
                ('res_id', '=', ticket.id),
                ('message_type', '!=', 'notification'),
            ])
            
            for message in messages:
                # Create a copy of the message for master ticket
                master_ticket.message_post(
                    body=message.body,
                    subject=message.subject or _('Message from %s') % ticket.ticket_number,
                    message_type=message.message_type,
                    author_id=message.author_id.id,
                    date=message.date,
                )

    def _merge_attachments(self, master_ticket, tickets):
        """Merge attachments from tickets to master ticket"""
        for ticket in tickets:
            # Get all attachments from the ticket
            attachments = ticket.message_attachment_ids
            
            for attachment in attachments:
                # Copy attachment to master ticket
                attachment.copy({
                    'res_model': 'helpdesk.ticket',
                    'res_id': master_ticket.id,
                })

    def _merge_activities(self, master_ticket, tickets):
        """Merge activities from tickets to master ticket"""
        for ticket in tickets:
            # Get all activities from the ticket
            activities = ticket.activity_ids
            
            for activity in activities:
                # Copy activity to master ticket
                activity.copy({
                    'res_id': master_ticket.id,
                })

    def _merge_links(self, master_ticket, tickets):
        """Merge linked records from tickets to master ticket"""
        for ticket in tickets:
            # Get all linked records
            links = ticket.model_link_ids
            
            for link in links:
                # Check if link already exists in master ticket
                existing_link = self.env['helpdesk.ticket.model.link'].search([
                    ('ticket_id', '=', master_ticket.id),
                    ('model_id', '=', link.model_id.id),
                    ('res_id', '=', link.res_id),
                ], limit=1)
                
                if not existing_link:
                    # Copy link to master ticket
                    link.copy({
                        'ticket_id': master_ticket.id,
                    })

    def _create_merge_history(self, master_ticket, tickets):
        """Create merge history record"""
        self.env['helpdesk.ticket.merge.history'].create({
            'master_ticket_id': master_ticket.id,
            'merged_ticket_ids': [(6, 0, tickets.ids)],
            'merge_date': fields.Datetime.now(),
            'user_id': self.env.user.id,
            'note': self.note or '',
        })
