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


class HelpdeskTag(models.Model):
    _name = 'helpdesk.tag'
    _description = 'Helpdesk Tag'
    _order = 'sequence, name'
    _inherit = ['mail.thread']

    name = fields.Char(
        string='Tag Name',
        required=True,
        tracking=True,
        translate=True,
        help='Name of the tag'
    )
    description = fields.Text(
        string='Description',
        translate=True,
        help='Description of the tag'
    )
    color = fields.Integer(
        string='Color',
        default=0,
        help='Color for tag display'
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True,
        help='If unchecked, this tag will be hidden'
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Sequence order for display'
    )
    
    # Statistics
    ticket_count = fields.Integer(
        string='Ticket Count',
        compute='_compute_ticket_count',
        help='Number of tickets with this tag'
    )
    open_ticket_count = fields.Integer(
        string='Open Tickets',
        compute='_compute_ticket_count',
        help='Number of open tickets with this tag'
    )

    @api.depends('name')
    def _compute_ticket_count(self):
        """Compute ticket statistics for the tag"""
        for tag in self:
            tickets = self.env['helpdesk.ticket'].search([
                ('tag_ids', 'in', [tag.id])
            ])
            tag.ticket_count = len(tickets)
            tag.open_ticket_count = len(tickets.filtered(
                lambda t: t.state not in ['closed', 'cancelled']
            ))

    def action_view_tickets(self):
        """Open tickets with this tag"""
        self.ensure_one()
        return {
            'name': _('Tagged Tickets'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket',
            'view_mode': 'kanban,tree,form',
            'domain': [('tag_ids', 'in', [self.id])],
            'context': {'default_tag_ids': [(4, self.id)]},
        }
