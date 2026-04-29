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


class HelpdeskTicketTemplateApplyWizard(models.TransientModel):
    _name = 'helpdesk.ticket.template.apply.wizard'
    _description = 'Helpdesk Ticket Template Apply Wizard'

    ticket_id = fields.Many2one(
        'helpdesk.ticket',
        string='Ticket',
        required=True,
        readonly=True
    )
    template_id = fields.Many2one(
        'helpdesk.ticket.template',
        string='Template',
        required=True,
        domain="[('active', '=', True)]",
        help='Select a template to apply'
    )
    model_name = fields.Char(
        string='Linked Model',
        help='Model name if ticket has linked models'
    )
    available_templates = fields.Many2many(
        'helpdesk.ticket.template',
        string='Available Templates',
        compute='_compute_available_templates'
    )
    overwrite_existing = fields.Boolean(
        string='Overwrite Existing Values',
        default=False,
        help='If checked, template values will overwrite existing ticket values. If unchecked, only empty fields will be filled.'
    )

    @api.depends('ticket_id', 'model_name')
    def _compute_available_templates(self):
        """Compute available templates based on ticket and linked models"""
        for wizard in self:
            templates = self.env['helpdesk.ticket.template']
            if wizard.ticket_id:
                # Get templates for linked models
                if wizard.ticket_id.model_link_ids:
                    for link in wizard.ticket_id.model_link_ids:
                        model_templates = self.env['helpdesk.ticket.template'].get_templates_for_model(link.model_name)
                        templates |= model_templates
                # Get general templates
                general_templates = self.env['helpdesk.ticket.template'].get_templates_for_model()
                templates |= general_templates
            else:
                # If no ticket, show all active templates
                templates = self.env['helpdesk.ticket.template'].search([
                    ('active', '=', True)
                ])
            wizard.available_templates = templates

    @api.onchange('template_id')
    def _onchange_template_id(self):
        """Update model_name when template changes"""
        if self.template_id and self.template_id.model_name:
            self.model_name = self.template_id.model_name

    def action_apply_template(self):
        """Apply selected template to ticket"""
        self.ensure_one()
        if not self.template_id:
            return
        
        # Get template values
        template_values = self.template_id._get_template_values()
        
        # Filter values based on overwrite_existing
        if not self.overwrite_existing:
            # Only apply values for empty fields
            final_values = {}
            for key, value in template_values.items():
                if not getattr(self.ticket_id, key, False):
                    final_values[key] = value
            template_values = final_values
        
        # Apply template
        self.ticket_id.write(template_values)
        
        # Update template reference
        self.ticket_id.template_id = self.template_id.id
        
        return {
            'type': 'ir.actions.act_window_close'
        }
