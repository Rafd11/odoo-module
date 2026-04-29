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


class HelpdeskCallLogCreateTicketWizard(models.TransientModel):
    _name = 'helpdesk.call.log.create.ticket.wizard'
    _description = 'Create Ticket from Call Log Wizard'

    call_log_id = fields.Many2one(
        'helpdesk.call.log',
        string='Call Log',
        required=True,
        readonly=True,
        help='Call log to create ticket from'
    )
    phone_number = fields.Char(
        string='Phone Number',
        required=True,
        help='Phone number of the caller'
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Contact',
        help='Contact associated with this call'
    )
    name = fields.Char(
        string='Subject',
        required=True,
        help='Ticket subject'
    )
    description = fields.Html(
        string='Description',
        help='Ticket description'
    )
    category_id = fields.Many2one(
        'helpdesk.category',
        string='Category',
        help='Ticket category'
    )
    priority = fields.Selection(
        [
            ('0', 'Low'),
            ('1', 'Medium'),
            ('2', 'High'),
            ('3', 'Urgent'),
        ],
        string='Priority',
        default='1',
        required=True,
        help='Ticket priority'
    )
    ticket_type_id = fields.Many2one(
        'helpdesk.ticket.type',
        string='Ticket Type',
        help='Type of ticket'
    )
    team_id = fields.Many2one(
        'helpdesk.team',
        string='Team',
        help='Team to assign the ticket to'
    )

    @api.model
    def default_get(self, fields_list):
        """Set default values from call log"""
        res = super(HelpdeskCallLogCreateTicketWizard, self).default_get(fields_list)
        
        call_log_id = self.env.context.get('default_call_log_id') or self.env.context.get('active_id')
        if call_log_id:
            call_log = self.env['helpdesk.call.log'].browse(call_log_id)
            if 'call_log_id' in fields_list:
                res['call_log_id'] = call_log.id
            if 'phone_number' in fields_list and not res.get('phone_number'):
                res['phone_number'] = call_log.phone_number
            if 'partner_id' in fields_list and not res.get('partner_id'):
                res['partner_id'] = call_log.partner_id.id
            if 'name' in fields_list and not res.get('name'):
                res['name'] = call_log.subject or _('Support Request from Call')
            if 'description' in fields_list and not res.get('description'):
                res['description'] = call_log.description or ''
            if 'priority' in fields_list and not res.get('priority'):
                res['priority'] = '1'
        
        return res

    @api.onchange('phone_number')
    def _onchange_phone_number(self):
        """Try to find partner by phone number"""
        if self.phone_number:
            partner = self.env['res.partner'].search([
                '|',
                ('phone', '=', self.phone_number),
                ('mobile', '=', self.phone_number)
            ], limit=1)
            if partner:
                self.partner_id = partner

    def action_create_ticket(self):
        """Create ticket from call log"""
        self.ensure_one()
        
        # Create or find partner
        partner = self.partner_id
        if not partner and self.phone_number:
            partner = self.env['res.partner'].search([
                '|',
                ('phone', '=', self.phone_number),
                ('mobile', '=', self.phone_number)
            ], limit=1)
            
            if not partner:
                partner = self.env['res.partner'].create({
                    'name': self.phone_number,
                    'phone': self.phone_number,
                    'is_company': False,
                })
        
        # Prepare ticket values
        ticket_vals = {
            'name': self.name,
            'description': self.description,
            'partner_id': partner.id if partner else False,
            'phone_number': self.phone_number,
            'channel': 'phone',
            'state': 'new',
            'priority': self.priority,
            'category_id': self.category_id.id if self.category_id else False,
            'ticket_type_id': self.ticket_type_id.id if self.ticket_type_id else False,
            'team_id': self.team_id.id if self.team_id else False,
        }
        
        # Create ticket
        ticket = self.env['helpdesk.ticket'].create(ticket_vals)
        
        # Link call log to ticket
        if self.call_log_id:
            self.call_log_id.write({
                'ticket_id': ticket.id,
                'state': 'completed',
            })
        
        # Return action to view the created ticket
        action = {
            'name': _('Ticket Created'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket',
            'view_mode': 'form',
            'res_id': ticket.id,
            'target': 'current',
        }
        return action
