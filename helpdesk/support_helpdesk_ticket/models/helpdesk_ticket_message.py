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


class HelpdeskTicketMessage(models.Model):
    _name = 'helpdesk.ticket.message'
    _description = 'Helpdesk Ticket Message'
    _order = 'date desc, id desc'

    ticket_id = fields.Many2one(
        'helpdesk.ticket',
        string='Ticket',
        required=True,
        ondelete='cascade',
        index=True,
        help='The ticket this message belongs to'
    )
    date = fields.Datetime(
        string='Date',
        required=True,
        default=fields.Datetime.now,
        help='Date and time of the message'
    )
    message_type = fields.Selection(
        [
            ('customer', 'Customer'),
            ('team', 'Team'),
        ],
        string='Type',
        required=True,
        default='team',
        help='Type of message: Customer or Team'
    )
    message = fields.Text(
        string='Message',
        required=True,
        help='Message content'
    )
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'helpdesk_ticket_message_attachment_rel',
        'message_id',
        'attachment_id',
        string='Attachments',
        help='Attachments related to this message'
    )
    user_id = fields.Many2one(
        'res.users',
        string='Author',
        default=lambda self: self.env.user,
        readonly=True,
        help='User who created this message'
    )

    @api.model
    def create(self, vals):
        """Override create to set date if not provided"""
        if 'date' not in vals or not vals.get('date'):
            vals['date'] = fields.Datetime.now()
        return super(HelpdeskTicketMessage, self).create(vals)
