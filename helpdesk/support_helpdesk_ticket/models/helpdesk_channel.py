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


class HelpdeskChannel(models.Model):
    _name = 'helpdesk.channel'
    _description = 'Helpdesk Channel'
    _order = 'sequence, name'
    _inherit = ['mail.thread']

    name = fields.Char(
        string='Channel Name',
        required=True,
        tracking=True,
        translate=True,
        help='Name of the channel (e.g., Email, Web Portal, Phone, Social Media)'
    )
    code = fields.Char(
        string='Code',
        required=True,
        copy=False,
        help='Unique code for the channel (e.g., email, web, phone)'
    )
    description = fields.Text(
        string='Description',
        translate=True,
        help='Description of the channel'
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True,
        help='If unchecked, this channel will be hidden'
    )
    color = fields.Integer(
        string='Color',
        default=0,
        help='Color for channel display'
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Sequence order for display'
    )
    icon = fields.Char(
        string='Icon',
        help='Font Awesome icon class (e.g., fa-envelope, fa-globe, fa-phone)'
    )
    
    # Default Configuration
    default_team_id = fields.Many2one(
        'helpdesk.team',
        string='Default Team',
        help='Default team to assign tickets from this channel'
    )
    default_user_id = fields.Many2one(
        'res.users',
        string='Default Assignee',
        help='Default user to assign tickets from this channel'
    )
    default_priority = fields.Selection(
        [
            ('0', 'Low'),
            ('1', 'Medium'),
            ('2', 'High'),
            ('3', 'Urgent'),
        ],
        string='Default Priority',
        help='Default priority for tickets from this channel'
    )
    default_sla_policy_id = fields.Many2one(
        'helpdesk.sla.policy',
        string='Default SLA Policy',
        help='Default SLA policy for tickets from this channel'
    )
    
    # Statistics
    ticket_count = fields.Integer(
        string='Ticket Count',
        compute='_compute_ticket_count',
        help='Number of tickets from this channel'
    )
    open_ticket_count = fields.Integer(
        string='Open Tickets',
        compute='_compute_ticket_count',
        help='Number of open tickets from this channel'
    )

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'Channel code must be unique!'),
    ]

    @api.depends('name')
    @api.depends('name')
    def _compute_ticket_count(self):
        """Compute ticket counts for this channel"""
        Ticket = self.env['helpdesk.ticket']
        for channel in self:
            domain = [('channel_id', '=', channel.id)]
            channel.ticket_count = Ticket.search_count(domain)
            domain.append(('state', 'not in', ['closed', 'cancelled']))
            channel.open_ticket_count = Ticket.search_count(domain)

    @api.model_create_multi
    def create(self, vals_list):
        """Generate code from name if not provided (batch-friendly)"""
        for vals in vals_list:
            if not vals.get('code') and vals.get('name'):
                vals['code'] = vals['name'].lower().replace(' ', '_')
        return super(HelpdeskChannel, self).create(vals_list)

    def name_get(self):
        """Return display name with icon if available"""
        result = []
        for channel in self:
            name = channel.name
            if channel.icon:
                name = f"{name} ({channel.icon})"
            result.append((channel.id, name))
        return result
