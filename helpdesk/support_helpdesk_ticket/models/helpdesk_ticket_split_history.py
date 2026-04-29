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

from odoo import models, fields, api


class HelpdeskTicketSplitHistory(models.Model):
    _name = 'helpdesk.ticket.split.history'
    _description = 'Helpdesk Ticket Split History'
    _order = 'split_date desc'

    source_ticket_id = fields.Many2one(
        'helpdesk.ticket',
        string='Source Ticket',
        required=True,
        ondelete='cascade',
        help='The original ticket that was split'
    )
    new_ticket_id = fields.Many2one(
        'helpdesk.ticket',
        string='New Ticket',
        required=True,
        ondelete='cascade',
        help='The new ticket created from the split'
    )
    split_date = fields.Datetime(
        string='Split Date',
        required=True,
        default=fields.Datetime.now,
        help='Date when the split occurred'
    )
    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        default=lambda self: self.env.user,
        help='User who performed the split'
    )
    note = fields.Text(
        string='Note',
        help='Optional note about the split'
    )
