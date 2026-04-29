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


class HelpdeskCategory(models.Model):
    _name = 'helpdesk.category'
    _description = 'Helpdesk Category'
    _order = 'sequence, name'
    _inherit = ['mail.thread']

    name = fields.Char(
        string='Category Name',
        required=True,
        tracking=True,
        translate=True,
        help='Name of the category'
    )
    description = fields.Text(
        string='Description',
        translate=True,
        help='Description of the category'
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True,
        help='If unchecked, this category will be hidden'
    )
    color = fields.Integer(
        string='Color',
        default=0,
        help='Color for category display'
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Sequence order for display'
    )
    
    # Routing Configuration
    default_team_id = fields.Many2one(
        'helpdesk.team',
        string='Default Team',
        help='Default team to assign tickets in this category'
    )
    default_user_id = fields.Many2one(
        'res.users',
        string='Default Assignee',
        help='Default user to assign tickets in this category'
    )
    default_priority = fields.Selection(
        [
            ('0', 'Low'),
            ('1', 'Medium'),
            ('2', 'High'),
            ('3', 'Urgent'),
        ],
        string='Default Priority',
        help='Default priority for tickets in this category'
    )
    default_sla_policy_id = fields.Many2one(
        'helpdesk.sla.policy',
        string='Default SLA Policy',
        help='Default SLA policy for tickets in this category'
    )
    
    # Statistics
    ticket_count = fields.Integer(
        string='Ticket Count',
        compute='_compute_ticket_count',
        help='Number of tickets in this category'
    )
    open_ticket_count = fields.Integer(
        string='Open Tickets',
        compute='_compute_ticket_count',
        help='Number of open tickets in this category'
    )

    @api.depends('name')
    def _compute_ticket_count(self):
        """Compute ticket statistics for the category"""
        for category in self:
            tickets = self.env['helpdesk.ticket'].search([
                ('category_id', '=', category.id)
            ])
            category.ticket_count = len(tickets)
            category.open_ticket_count = len(tickets.filtered(
                lambda t: t.state not in ['closed', 'cancelled']
            ))

    def action_view_tickets(self):
        """Open tickets for this category"""
        self.ensure_one()
        return {
            'name': _('Category Tickets'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket',
            'view_mode': 'kanban,tree,form',
            'domain': [('category_id', '=', self.id)],
            'context': {'default_category_id': self.id},
        }
