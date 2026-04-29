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


class HelpdeskTicketTemplate(models.Model):
    _name = 'helpdesk.ticket.template'
    _description = 'Helpdesk Ticket Template'
    _order = 'sequence, name'
    _inherit = ['mail.thread']

    name = fields.Char(
        string='Template Name',
        required=True,
        tracking=True,
        translate=True,
        help='Name of the template'
    )
    description = fields.Text(
        string='Description',
        translate=True,
        help='Description of the template'
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True,
        help='If unchecked, this template will be hidden'
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Sequence order for display'
    )
    
    # Template Content
    subject = fields.Char(
        string='Subject',
        translate=True,
        help='Default subject for tickets created from this template'
    )
    description_template = fields.Html(
        string='Description Template',
        translate=True,
        help='Default description template'
    )
    
    # Default Values
    ticket_type_id = fields.Many2one(
        'helpdesk.ticket.type',
        string='Ticket Type',
        help='Default ticket type'
    )
    category_id = fields.Many2one(
        'helpdesk.category',
        string='Category',
        help='Default category'
    )
    tag_ids = fields.Many2many(
        'helpdesk.tag',
        'helpdesk_template_tag_rel',
        'template_id',
        'tag_id',
        string='Tags',
        help='Default tags'
    )
    priority = fields.Selection(
        [
            ('0', 'Low'),
            ('1', 'Medium'),
            ('2', 'High'),
            ('3', 'Urgent'),
        ],
        string='Priority',
        help='Default priority'
    )
    team_id = fields.Many2one(
        'helpdesk.team',
        string='Team',
        help='Default team'
    )
    user_id = fields.Many2one(
        'res.users',
        string='Assigned To',
        help='Default assignee'
    )
    channel_id = fields.Many2one(
        'helpdesk.channel',
        string='Channel',
        help='Default channel'
    )
    sla_policy_id = fields.Many2one(
        'helpdesk.sla.policy',
        string='SLA Policy',
        help='Default SLA policy'
    )
    
    # Model-Specific Templates
    model_name = fields.Char(
        string='Model',
        help='Odoo model this template applies to (e.g., product.product, sale.order). Leave empty for general templates.'
    )
    model_display_name = fields.Char(
        string='Model Display Name',
        compute='_compute_model_display_name',
        help='Display name of the model'
    )
    
    # Usage Statistics
    usage_count = fields.Integer(
        string='Usage Count',
        compute='_compute_usage_count',
        help='Number of times this template has been used'
    )

    @api.depends('model_name')
    def _compute_model_display_name(self):
        """Compute display name of the model"""
        for template in self:
            if template.model_name:
                try:
                    model = self.env['ir.model'].search([
                        ('model', '=', template.model_name)
                    ], limit=1)
                    template.model_display_name = model.name if model else template.model_name
                except Exception:
                    template.model_display_name = template.model_name
            else:
                template.model_display_name = _('General')

    @api.depends('name')
    def _compute_usage_count(self):
        """Compute usage count (placeholder - would need tracking)"""
        for template in self:
            # TODO: Implement usage tracking
            template.usage_count = 0

    def action_apply_template(self, ticket_id=None):
        """Apply template to a ticket"""
        self.ensure_one()
        if not ticket_id:
            # Create new ticket from template
            return self._create_ticket_from_template()
        else:
            # Apply template to existing ticket
            ticket = self.env['helpdesk.ticket'].browse(ticket_id)
            return self._apply_template_to_ticket(ticket)

    def _create_ticket_from_template(self):
        """Create a new ticket from template"""
        self.ensure_one()
        # This would be called from a wizard or action
        # For now, return action to create ticket with template context
        return {
            'name': _('Create Ticket from Template'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket',
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'default_template_id': self.id,
                'template_apply': True,
            }
        }

    def _apply_template_to_ticket(self, ticket):
        """Apply template values to existing ticket"""
        self.ensure_one()
        values = self._get_template_values()
        ticket.write(values)
        return True

    def _get_template_values(self):
        """Get template values as dictionary"""
        self.ensure_one()
        values = {}
        
        # Basic fields
        if self.subject:
            values['name'] = self.subject
        if self.description_template:
            values['description'] = self.description_template
        
        # Default values
        if self.ticket_type_id:
            values['ticket_type_id'] = self.ticket_type_id.id
        if self.category_id:
            values['category_id'] = self.category_id.id
        if self.tag_ids:
            values['tag_ids'] = [(6, 0, self.tag_ids.ids)]
        if self.priority:
            values['priority'] = self.priority
        if self.team_id:
            values['team_id'] = self.team_id.id
        if self.user_id:
            values['user_id'] = self.user_id.id
        if self.channel:
            values['channel'] = self.channel
        if self.sla_policy_id:
            values['sla_policy_id'] = self.sla_policy_id.id
        
        return values

    @api.model
    def get_templates_for_model(self, model_name=None):
        """Get available templates for a specific model"""
        domain = [('active', '=', True)]
        if model_name:
            domain.append('|')
            domain.append(('model_name', '=', model_name))
            domain.append(('model_name', '=', False))
        else:
            domain.append(('model_name', '=', False))
        return self.search(domain, order='sequence, name')
    
    @api.model
    def get_templates_for_type(self, ticket_type_id=None):
        """Task 9.2: Get available templates for a specific ticket type"""
        domain = [('active', '=', True)]
        if ticket_type_id:
            domain.append('|')
            domain.append(('ticket_type_id', '=', ticket_type_id))
            domain.append(('ticket_type_id', '=', False))
        else:
            domain.append(('ticket_type_id', '=', False))
        return self.search(domain, order='sequence, name')
