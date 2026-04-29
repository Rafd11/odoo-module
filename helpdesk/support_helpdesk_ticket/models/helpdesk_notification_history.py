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


class HelpdeskNotificationHistory(models.Model):
    _name = 'helpdesk.notification.history'
    _description = 'Notification History'
    _order = 'sent_date desc, id desc'
    _rec_name = 'display_name'

    template_id = fields.Many2one(
        'helpdesk.notification.template',
        string='Template',
        ondelete='set null',
        index=True,
        help='Template used for this notification'
    )
    ticket_id = fields.Many2one(
        'helpdesk.ticket',
        string='Ticket',
        required=True,
        ondelete='cascade',
        index=True,
        help='Ticket this notification was sent for'
    )
    notification_type = fields.Selection(
        [
            ('ticket_created', 'Ticket Created'),
            ('ticket_assigned', 'Ticket Assigned'),
            ('ticket_status_change', 'Status Changed'),
            ('ticket_updated', 'Ticket Updated'),
            ('ticket_resolved', 'Ticket Resolved'),
            ('ticket_closed', 'Ticket Closed'),
            ('ticket_escalated', 'Ticket Escalated'),
            ('ticket_sla_warning', 'SLA Warning'),
            ('ticket_sla_breach', 'SLA Breach'),
            ('ticket_comment', 'New Comment'),
            ('ticket_priority_change', 'Priority Changed'),
            ('custom', 'Custom'),
        ],
        string='Notification Type',
        required=True,
        help='Type of notification'
    )
    notification_channel = fields.Selection(
        [
            ('email', 'Email'),
            ('in_app', 'In-App'),
            ('both', 'Both'),
        ],
        string='Channel',
        required=True,
        help='Channel used for notification'
    )
    recipient_count = fields.Integer(
        string='Recipient Count',
        default=1,
        help='Number of recipients'
    )
    sent_date = fields.Datetime(
        string='Sent Date',
        required=True,
        default=fields.Datetime.now,
        index=True,
        help='Date and time when notification was sent'
    )
    status = fields.Selection(
        [
            ('sent', 'Sent'),
            ('failed', 'Failed'),
            ('pending', 'Pending'),
        ],
        string='Status',
        default='sent',
        help='Status of the notification'
    )
    error_message = fields.Text(
        string='Error Message',
        help='Error message if notification failed'
    )
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )

    @api.depends('template_id', 'ticket_id', 'sent_date', 'notification_type')
    def _compute_display_name(self):
        """Compute display name"""
        for history in self:
            template_name = history.template_id.name if history.template_id else _('Custom')
            ticket_number = history.ticket_id.ticket_number if history.ticket_id else _('Unknown')
            type_label = dict(history._fields['notification_type'].selection).get(history.notification_type, history.notification_type)
            history.display_name = _('%s - %s (%s)') % (template_name, ticket_number, type_label)

    def action_view_ticket(self):
        """Open the ticket"""
        self.ensure_one()
        return {
            'name': _('Ticket'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket',
            'res_id': self.ticket_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_view_template(self):
        """Open the notification template"""
        self.ensure_one()
        if not self.template_id:
            return False
        return {
            'name': _('Notification Template'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.notification.template',
            'res_id': self.template_id.id,
            'view_mode': 'form',
            'target': 'current',
        }
