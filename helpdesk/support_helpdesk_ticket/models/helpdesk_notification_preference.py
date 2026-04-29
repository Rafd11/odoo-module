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


class HelpdeskNotificationPreference(models.Model):
    _name = 'helpdesk.notification.preference'
    _description = 'Notification Preference'
    _rec_name = 'display_name'

    user_id = fields.Many2one(
        'res.users',
        string='User',
        required=True,
        default=lambda self: self.env.user,
        index=True,
        help='User these preferences belong to'
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
        ],
        string='Notification Type',
        required=True,
        help='Type of notification'
    )
    email_enabled = fields.Boolean(
        string='Email Notifications',
        default=True,
        help='Receive email notifications for this type'
    )
    in_app_enabled = fields.Boolean(
        string='In-App Notifications',
        default=True,
        help='Receive in-app notifications for this type'
    )
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )

    @api.depends('user_id', 'notification_type')
    def _compute_display_name(self):
        """Compute display name"""
        for pref in self:
            user_name = pref.user_id.name if pref.user_id else _('Unknown')
            type_label = dict(pref._fields['notification_type'].selection).get(pref.notification_type, pref.notification_type)
            pref.display_name = _('%s - %s') % (user_name, type_label)

    _sql_constraints = [
        ('user_type_unique', 'unique(user_id, notification_type)', 
         'A user can only have one preference per notification type.')
    ]

    @api.model
    def get_preference(self, user_id, notification_type):
        """Get preference for user and notification type"""
        preference = self.search([
            ('user_id', '=', user_id),
            ('notification_type', '=', notification_type)
        ], limit=1)
        
        if preference:
            return preference
        
        # Return default preference
        return self.create({
            'user_id': user_id,
            'notification_type': notification_type,
            'email_enabled': True,
            'in_app_enabled': True,
        })
