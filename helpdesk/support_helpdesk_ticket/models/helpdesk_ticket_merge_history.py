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


class HelpdeskTicketMergeHistory(models.Model):
    _name = 'helpdesk.ticket.merge.history'
    _description = 'Helpdesk Ticket Merge History'
    _order = 'merge_date desc'

    master_ticket_id = fields.Many2one(
        'helpdesk.ticket',
        string='Master Ticket',
        required=True,
        ondelete='cascade',
        help='The ticket that remained after merge'
    )
    merged_ticket_ids = fields.Many2many(
        'helpdesk.ticket',
        'helpdesk_ticket_merge_history_rel',
        'history_id',
        'ticket_id',
        string='Merged Tickets',
        help='Tickets that were merged into the master ticket'
    )
    merge_date = fields.Datetime(
        string='Merge Date',
        required=True,
        default=fields.Datetime.now,
        help='Date when the merge occurred'
    )
    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        default=lambda self: self.env.user,
        help='User who performed the merge'
    )
    note = fields.Text(
        string='Note',
        help='Optional note about the merge'
    )
