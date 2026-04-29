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

import logging
from odoo import models, fields, api, _

_logger = logging.getLogger(__name__)


class HelpdeskModelLinkAccessLog(models.Model):
    _name = 'helpdesk.model.link.access.log'
    _description = 'Model Link Access Log'
    _order = 'access_date desc'
    _rec_name = 'display_name'

    link_id = fields.Many2one(
        'helpdesk.ticket.model.link',
        string='Model Link',
        required=True,
        ondelete='cascade',
        index=True,
        help='The model link this log entry refers to'
    )
    ticket_id = fields.Many2one(
        'helpdesk.ticket',
        string='Ticket',
        related='link_id.ticket_id',
        store=True,
        readonly=True,
        index=True,
        help='Related ticket'
    )
    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        default=lambda self: self.env.user,
        index=True,
        help='User who attempted the access'
    )
    access_date = fields.Datetime(
        string='Access Date',
        required=True,
        default=fields.Datetime.now,
        index=True,
        help='Date and time of access attempt'
    )
    access_type = fields.Selection(
        [
            ('create', 'Create Link'),
            ('read', 'Read/View'),
            ('open', 'Open Record'),
            ('validate', 'Validate Access'),
        ],
        string='Access Type',
        required=True,
        help='Type of access operation'
    )
    model_name = fields.Char(
        string='Model',
        required=True,
        help='Model technical name'
    )
    res_id = fields.Integer(
        string='Record ID',
        required=True,
        help='Record ID'
    )
    status = fields.Selection(
        [
            ('success', 'Success'),
            ('denied', 'Access Denied'),
            ('error', 'Error'),
            ('not_found', 'Record Not Found'),
        ],
        string='Status',
        required=True,
        help='Access attempt status'
    )
    error_message = fields.Text(
        string='Error Message',
        help='Error message if access failed'
    )
    ip_address = fields.Char(
        string='IP Address',
        help='IP address of the user (if available)'
    )
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )

    @api.depends('user_id', 'access_type', 'model_name', 'res_id', 'status', 'access_date')
    def _compute_display_name(self):
        """Compute display name"""
        for log in self:
            user_name = log.user_id.name if log.user_id else _('Unknown')
            access_type_label = dict(log._fields['access_type'].selection).get(log.access_type, log.access_type)
            status_label = dict(log._fields['status'].selection).get(log.status, log.status)
            log.display_name = _('%s - %s (%s) - %s') % (
                user_name, access_type_label, log.model_name, status_label
            )

    def action_view_link(self):
        """View the related model link"""
        self.ensure_one()
        return {
            'name': _('Model Link'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket.model.link',
            'res_id': self.link_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_ticket(self):
        """View the related ticket"""
        self.ensure_one()
        return {
            'name': _('Ticket'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket',
            'res_id': self.ticket_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
