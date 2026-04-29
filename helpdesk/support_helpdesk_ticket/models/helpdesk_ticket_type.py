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


class HelpdeskTicketType(models.Model):
    _name = 'helpdesk.ticket.type'
    _description = 'Helpdesk Ticket Type'
    _inherit = ['mail.thread']

    name = fields.Char(
        string='Type Name',
        required=True,
        tracking=True,
        translate=True
    )
    description = fields.Text(
        string='Description',
        translate=True
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True
    )

    # ==================== Defaults & Configuration ====================
    default_priority = fields.Selection(
        selection=[
            ('0', 'Low'),
            ('1', 'Medium'),
            ('2', 'High'),
            ('3', 'Urgent'),
        ],
        string='Default Priority',
        help='Default priority to apply when this type is selected on a ticket.'
    )
    default_category_id = fields.Many2one(
        'helpdesk.category',
        string='Default Category',
        help='Default category to apply when this type is selected on a ticket.'
    )
    default_team_id = fields.Many2one(
        'helpdesk.team',
        string='Default Team',
        help='Default team to apply when this type is selected on a ticket.'
    )
    default_sla_policy_id = fields.Many2one(
        'helpdesk.sla.policy',
        string='Default SLA Policy',
        help='Default SLA policy to apply when this type is selected on a ticket.'
    )

    # Form fields configuration (Task 9.2 will use this)
    form_configuration = fields.Text(
        string='Form Fields Configuration',
        help='Optional JSON or notes describing which fields should be shown/required for this type. '
             'Used by type-based configuration logic.'
    )

    # Template linking
    default_template_id = fields.Many2one(
        'helpdesk.ticket.template',
        string='Default Template',
        help='Default ticket template to use when creating a ticket of this type.'
    )
    template_ids = fields.One2many(
        'helpdesk.ticket.template',
        'ticket_type_id',
        string='Templates',
        help='All templates associated with this ticket type.'
    )

    @api.depends('default_priority')
    def _compute_display_name(self):
        """Optional nicer display name including priority."""
        for rec in self:
            if rec.default_priority:
                priority_label = dict(self._fields['default_priority'].selection).get(rec.default_priority, '')
                rec.display_name = '%s (%s)' % (rec.name, priority_label) if priority_label else rec.name
            else:
                rec.display_name = rec.name
