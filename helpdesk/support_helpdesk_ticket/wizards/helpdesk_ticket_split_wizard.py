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


class HelpdeskTicketSplitWizard(models.TransientModel):
    _name = 'helpdesk.ticket.split.wizard'
    _description = 'Helpdesk Ticket Split Wizard'

    ticket_id = fields.Many2one(
        'helpdesk.ticket',
        string='Source Ticket',
        required=True,
        readonly=True,
        help='The ticket to split'
    )
    new_ticket_name = fields.Char(
        string='New Ticket Subject',
        required=True,
        help='Subject for the new ticket'
    )
    new_ticket_description = fields.Html(
        string='New Ticket Description',
        help='Description for the new ticket'
    )
    message_ids = fields.Many2many(
        'mail.message',
        'helpdesk_ticket_split_message_rel',
        'wizard_id',
        'message_id',
        string='Messages to Include',
        domain="[('model', '=', 'helpdesk.ticket'), ('res_id', '=', ticket_id)]",
        help='Select messages to include in the new ticket'
    )
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'helpdesk_ticket_split_attachment_rel',
        'wizard_id',
        'attachment_id',
        string='Attachments to Include',
        domain="[('res_model', '=', 'helpdesk.ticket'), ('res_id', '=', ticket_id)]",
        help='Select attachments to include in the new ticket'
    )
    copy_assignee = fields.Boolean(
        string='Copy Assignee',
        default=True,
        help='Copy assignee from source ticket'
    )
    copy_team = fields.Boolean(
        string='Copy Team',
        default=True,
        help='Copy team from source ticket'
    )
    copy_category = fields.Boolean(
        string='Copy Category',
        default=True,
        help='Copy category from source ticket'
    )
    copy_tags = fields.Boolean(
        string='Copy Tags',
        default=True,
        help='Copy tags from source ticket'
    )
    copy_priority = fields.Boolean(
        string='Copy Priority',
        default=True,
        help='Copy priority from source ticket'
    )
    copy_sla = fields.Boolean(
        string='Copy SLA Policy',
        default=True,
        help='Copy SLA policy from source ticket'
    )
    link_to_parent = fields.Boolean(
        string='Link to Parent Ticket',
        default=True,
        help='Create parent-child relationship between tickets'
    )
    note = fields.Text(
        string='Split Note',
        help='Optional note about the split operation'
    )

    @api.model
    def default_get(self, fields_list):
        """Set default values"""
        res = super(HelpdeskTicketSplitWizard, self).default_get(fields_list)
        if 'ticket_id' in res and res.get('ticket_id'):
            ticket = self.env['helpdesk.ticket'].browse(res['ticket_id'])
            if 'new_ticket_name' in fields_list and not res.get('new_ticket_name'):
                res['new_ticket_name'] = _('Split from %s') % ticket.ticket_number
            if 'new_ticket_description' in fields_list and not res.get('new_ticket_description'):
                res['new_ticket_description'] = _('This ticket was split from %s') % ticket.ticket_number
        return res

    def action_split_ticket(self):
        """Split ticket into new ticket"""
        self.ensure_one()
        if not self.new_ticket_name:
            raise UserError(_('Please provide a subject for the new ticket.'))

        source_ticket = self.ticket_id

        # Prepare values for new ticket
        ticket_vals = {
            'name': self.new_ticket_name,
            'description': self.new_ticket_description or '',
            'partner_id': source_ticket.partner_id.id,
            'partner_email': source_ticket.partner_email,
            'partner_phone': source_ticket.partner_phone,
            'state': 'new',
            'channel': source_ticket.channel,
        }

        # Copy fields if requested
        if self.copy_assignee and source_ticket.user_id:
            ticket_vals['user_id'] = source_ticket.user_id.id
        if self.copy_team and source_ticket.team_id:
            ticket_vals['team_id'] = source_ticket.team_id.id
        if self.copy_category and source_ticket.category_id:
            ticket_vals['category_id'] = source_ticket.category_id.id
        if self.copy_tags and source_ticket.tag_ids:
            ticket_vals['tag_ids'] = [(6, 0, source_ticket.tag_ids.ids)]
        if self.copy_priority:
            ticket_vals['priority'] = source_ticket.priority
        if self.copy_sla and source_ticket.sla_policy_id:
            ticket_vals['sla_policy_id'] = source_ticket.sla_policy_id.id

        # Create new ticket
        new_ticket = self.env['helpdesk.ticket'].create(ticket_vals)

        # Link to parent if requested
        if self.link_to_parent:
            new_ticket.parent_ticket_id = source_ticket.id

        # Copy selected messages
        if self.message_ids:
            for message in self.message_ids:
                new_ticket.message_post(
                    body=message.body,
                    subject=message.subject or _('Message from %s') % source_ticket.ticket_number,
                    message_type=message.message_type,
                    author_id=message.author_id.id,
                    date=message.date,
                )

        # Copy selected attachments
        if self.attachment_ids:
            for attachment in self.attachment_ids:
                attachment.copy({
                    'res_model': 'helpdesk.ticket',
                    'res_id': new_ticket.id,
                })

        # Add split note
        if self.note:
            new_ticket.message_post(
                body=_('Split Note: %s') % self.note,
                subject=_('Ticket Split')
            )

        # Create split history record
        self._create_split_history(source_ticket, new_ticket)

        # Post split notification to both tickets
        new_ticket.message_post(
            body=_('This ticket was split from %s') % source_ticket.ticket_number,
            subject=_('Ticket Split')
        )
        source_ticket.message_post(
            body=_('Ticket split: Created %s') % new_ticket.ticket_number,
            subject=_('Ticket Split')
        )

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket',
            'res_id': new_ticket.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def _create_split_history(self, source_ticket, new_ticket):
        """Create split history record"""
        from odoo import fields
        self.env['helpdesk.ticket.split.history'].create({
            'source_ticket_id': source_ticket.id,
            'new_ticket_id': new_ticket.id,
            'split_date': fields.Datetime.now(),
            'user_id': self.env.user.id,
            'note': self.note or '',
        })
