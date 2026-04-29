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

import json
from datetime import timedelta
from odoo import models, fields, api, _


class HelpdeskNotificationSchedule(models.Model):
    _name = 'helpdesk.notification.schedule'
    _description = 'Scheduled Notification'
    _order = 'scheduled_date, id'

    template_id = fields.Many2one(
        'helpdesk.notification.template',
        string='Template',
        required=True,
        ondelete='cascade',
        index=True,
        help='Notification template to use'
    )
    ticket_id = fields.Many2one(
        'helpdesk.ticket',
        string='Ticket',
        required=True,
        ondelete='cascade',
        index=True,
        help='Ticket to send notification for'
    )
    scheduled_date = fields.Datetime(
        string='Scheduled Date',
        required=True,
        index=True,
        help='Date and time when notification should be sent'
    )
    sent_date = fields.Datetime(
        string='Sent Date',
        readonly=True,
        help='Date and time when notification was actually sent'
    )
    status = fields.Selection(
        [
            ('pending', 'Pending'),
            ('sent', 'Sent'),
            ('failed', 'Failed'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='pending',
        required=True,
        help='Status of the scheduled notification'
    )
    context = fields.Text(
        string='Context',
        help='Additional context data for notification (JSON format)'
    )
    error_message = fields.Text(
        string='Error Message',
        help='Error message if sending failed'
    )

    def action_send_now(self):
        """Send notification immediately"""
        self.ensure_one()
        if self.status != 'pending':
            return False
        
        try:
            # Parse context - handle both JSON string and dict
            if isinstance(self.context, str) and self.context:
                try:
                    context = json.loads(self.context)
                except:
                    context = {}
            else:
                context = self.context or {}
            
            sent = self.template_id.send_notification(self.ticket_id, context)
            
            if sent:
                self.write({
                    'status': 'sent',
                    'sent_date': fields.Datetime.now()
                })
            else:
                self.write({
                    'status': 'failed',
                    'error_message': _('Notification template conditions not met or no recipients')
                })
        except Exception as e:
            self.write({
                'status': 'failed',
                'error_message': str(e)
            })
        
        return True

    def action_cancel(self):
        """Cancel scheduled notification"""
        self.ensure_one()
        if self.status == 'pending':
            self.write({'status': 'cancelled'})
        return True

    @api.model
    def process_scheduled_notifications(self):
        """Process scheduled notifications that are due"""
        now = fields.Datetime.now()
        due_notifications = self.search([
            ('status', '=', 'pending'),
            ('scheduled_date', '<=', now)
        ])
        
        for notification in due_notifications:
            notification.action_send_now()
        
        return len(due_notifications)
