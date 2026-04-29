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


class HelpdeskTicketStatusHistory(models.Model):
    _name = 'helpdesk.ticket.status.history'
    _description = 'Helpdesk Ticket Status History'
    _order = 'change_date desc'

    ticket_id = fields.Many2one(
        'helpdesk.ticket',
        string='Ticket',
        required=True,
        ondelete='cascade',
        index=True
    )
    old_state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('new', 'New'),
            ('assigned', 'Assigned'),
            ('in_progress', 'In Progress'),
            ('resolved', 'Resolved'),
            ('closed', 'Closed'),
            ('cancelled', 'Cancelled'),
        ],
        string='Previous Status',
        required=True
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
    change_date = fields.Datetime(
        string='Change Date',
        required=True,
        default=fields.Datetime.now
    )
    user_id = fields.Many2one(
        'res.users',
        string='Changed By',
        required=True,
        default=lambda self: self.env.user
    )
    note = fields.Text(
        string='Note',
        help='Optional note about the status change'
    )
    reason = fields.Selection(
        [
            ('auto', 'Automatic'),
            ('manual', 'Manual'),
            ('workflow', 'Workflow Rule'),
            ('escalation', 'Escalation'),
            ('sla', 'SLA Breach'),
        ],
        string='Change Reason',
        default='manual'
    )
