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

import ast
from datetime import timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HelpdeskNotificationTemplate(models.Model):
    _name = 'helpdesk.notification.template'
    _description = 'Notification Template'
    _order = 'name'

    name = fields.Char(
        string='Template Name',
        required=True,
        help='Name of the notification template'
    )
    description = fields.Text(
        string='Description',
        help='Functional description of when and how this notification is used'
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Whether this template is active'
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
        help='Type of notification this template handles'
    )
    notification_channel = fields.Selection(
        [
            ('email', 'Email'),
            ('in_app', 'In-App'),
            ('both', 'Both'),
        ],
        string='Notification Channel',
        required=True,
        default='both',
        help='Channel(s) to send notification through'
    )
    email_template_id = fields.Many2one(
        'mail.template',
        string='Email Template',
        domain="[('model', '=', 'helpdesk.ticket')]",
        help='Email template to use for email notifications'
    )
    subject = fields.Char(
        string='Subject',
        help='Subject line for email notifications (if not using email template)'
    )
    body_html = fields.Html(
        string='Message Body',
        help='Message body for notifications (HTML supported)'
    )
    in_app_message = fields.Text(
        string='In-App Message',
        help='Message to display in-app notifications'
    )
    
    # Recipient Configuration
    recipient_type = fields.Selection(
        [
            ('customer', 'Customer'),
            ('assigned_user', 'Assigned User'),
            ('team_members', 'Team Members'),
            ('team_leader', 'Team Leader'),
            ('custom_users', 'Custom Users'),
            ('all', 'All (Customer + Team)'),
        ],
        string='Recipient Type',
        required=True,
        default='customer',
        help='Who should receive this notification'
    )
    recipient_user_ids = fields.Many2many(
        'res.users',
        'helpdesk_notification_template_user_rel',
        'template_id',
        'user_id',
        string='Recipient Users',
        help='Specific users to notify (for custom_users recipient type)'
    )
    
    # Conditions
    condition_domain = fields.Text(
        string='Condition Domain',
        help='Domain expression. Notification sent only if ticket matches this domain.'
    )
    priority_filter = fields.Selection(
        [
            ('0', 'Low'),
            ('1', 'Medium'),
            ('2', 'High'),
            ('3', 'Urgent'),
            ('all', 'All Priorities'),
        ],
        string='Priority Filter',
        default='all',
        help='Priority level this template applies to'
    )
    category_ids = fields.Many2many(
        'helpdesk.category',
        'helpdesk_notification_template_category_rel',
        'template_id',
        'category_id',
        string='Categories',
        help='Categories this template applies to (leave empty for all)'
    )
    
    # Scheduling
    send_immediately = fields.Boolean(
        string='Send Immediately',
        default=True,
        help='Send notification immediately when triggered'
    )
    delay_hours = fields.Float(
        string='Delay (Hours)',
        default=0.0,
        help='Delay before sending notification (hours). Only used if Send Immediately is False.'
    )
    
    # Usage Statistics
    usage_count = fields.Integer(
        string='Usage Count',
        default=0,
        readonly=True,
        help='Number of times this template has been used'
    )
    last_used_date = fields.Datetime(
        string='Last Used',
        readonly=True,
        help='Date when this template was last used'
    )

    # ==================== UI Helper Actions ====================

    def action_test_template(self):
        """UI action: perform a simple test send using this template.

        For now, this only validates configuration and logs that a test
        was triggered. It can be extended to send to a test ticket/user.
        """
        for template in self:
            # Reuse existing validation; will raise if misconfigured
            template._check_email_configuration()
        return True

    def action_view_history(self):
        """Open notification history filtered for this template."""
        self.ensure_one()
        action = self.env.ref('support_helpdesk_ticket.action_helpdesk_notification_history')
        result = action.read()[0]
        result['domain'] = [('template_id', '=', self.id)]
        return result

    @api.constrains('email_template_id', 'subject', 'body_html')
    def _check_email_configuration(self):
        """Validate email configuration"""
        for template in self:
            if template.notification_channel in ['email', 'both']:
                if not template.email_template_id and not (template.subject and template.body_html):
                    raise ValidationError(_('Email notification requires either an email template or subject and body.'))

    def send_notification(self, ticket, context=None):
        """
        Send notification using this template
        
        :param ticket: helpdesk.ticket record
        :param context: Additional context dictionary
        :return: True if sent successfully
        """
        self.ensure_one()
        context = context or {}
        
        # Check user preferences
        recipients = self._get_recipients(ticket)
        if not recipients:
            return False
        
        # Filter recipients based on preferences
        filtered_recipients = self._filter_by_preferences(recipients, ticket)
        if not filtered_recipients:
            return False
        
        # Check conditions
        if not self._check_conditions(ticket):
            return False
        
        # Schedule or send immediately
        if self.send_immediately or self.delay_hours == 0:
            return self._send_notification_now(ticket, filtered_recipients, context)
        else:
            # Schedule for later
            import json
            scheduled_date = fields.Datetime.now() + timedelta(hours=self.delay_hours)
            self.env['helpdesk.notification.schedule'].create({
                'template_id': self.id,
                'ticket_id': ticket.id,
                'scheduled_date': scheduled_date,
                'context': json.dumps(context) if context else '',
            })
            return True
    
    def _send_notification_now(self, ticket, recipients, context):
        """Send notification immediately"""
        # Send notifications
        sent = False
        if self.notification_channel in ['email', 'both']:
            sent = self._send_email_notification(ticket, recipients, context) or sent
        
        if self.notification_channel in ['in_app', 'both']:
            sent = self._send_in_app_notification(ticket, recipients, context) or sent
        
        # Update statistics
        if sent:
            self.write({
                'usage_count': self.usage_count + 1,
                'last_used_date': fields.Datetime.now()
            })
            
            # Log notification
            self.env['helpdesk.notification.history'].create({
                'template_id': self.id,
                'ticket_id': ticket.id,
                'notification_type': self.notification_type,
                'notification_channel': self.notification_channel,
                'recipient_count': len(recipients),
                'sent_date': fields.Datetime.now(),
            })
        
        return sent
    
    def _filter_by_preferences(self, recipients, ticket):
        """Filter recipients based on user notification preferences"""
        filtered = []
        
        for recipient in recipients:
            # Get user for this partner
            user = recipient.user_ids[0] if recipient.user_ids else None
            
            if not user:
                # No user associated, include if it's customer
                if recipient == ticket.partner_id:
                    filtered.append(recipient)
                continue
            
            # Get preference
            preference = self.env['helpdesk.notification.preference'].get_preference(
                user.id,
                self.notification_type
            )
            
            # Check if user wants this type of notification
            if self.notification_channel == 'email' and preference.email_enabled:
                filtered.append(recipient)
            elif self.notification_channel == 'in_app' and preference.in_app_enabled:
                filtered.append(recipient)
            elif self.notification_channel == 'both':
                if preference.email_enabled or preference.in_app_enabled:
                    filtered.append(recipient)
        
        return filtered
    
    def _check_conditions(self, ticket):
        """Check if ticket matches template conditions"""
        # Check priority filter
        if self.priority_filter != 'all' and ticket.priority != self.priority_filter:
            return False
        
        # Check category filter
        if self.category_ids and ticket.category_id not in self.category_ids:
            return False
        
        # Check domain condition
        if self.condition_domain:
            try:
                domain = ast.literal_eval(self.condition_domain)
                if not ticket.filtered_domain(domain):
                    return False
            except (ValueError, SyntaxError):
                return False
        
        return True
    
    def _get_recipients(self, ticket):
        """Get list of recipients for notification"""
        recipients = []
        
        if self.recipient_type == 'customer':
            if ticket.partner_id:
                recipients.append(ticket.partner_id)
        
        elif self.recipient_type == 'assigned_user':
            if ticket.user_id and ticket.user_id.partner_id:
                recipients.append(ticket.user_id.partner_id)
        
        elif self.recipient_type == 'team_members':
            if ticket.team_id:
                recipients.extend(ticket.team_id.member_ids.mapped('partner_id'))
        
        elif self.recipient_type == 'team_leader':
            if ticket.team_id and ticket.team_id.team_leader_id:
                recipients.append(ticket.team_id.team_leader_id.partner_id)
        
        elif self.recipient_type == 'custom_users':
            recipients.extend(self.recipient_user_ids.mapped('partner_id'))
        
        elif self.recipient_type == 'all':
            if ticket.partner_id:
                recipients.append(ticket.partner_id)
            if ticket.team_id:
                recipients.extend(ticket.team_id.member_ids.mapped('partner_id'))
        
        # Filter out duplicates and ensure email exists
        unique_recipients = []
        seen_ids = set()
        for recipient in recipients:
            if recipient.id not in seen_ids and recipient.email:
                unique_recipients.append(recipient)
                seen_ids.add(recipient.id)
        
        return unique_recipients
    
    def _send_email_notification(self, ticket, recipients, context):
        """Send email notification"""
        if self.email_template_id:
            # Use email template
            for recipient in recipients:
                self.email_template_id.with_context(
                    email_to=recipient.email,
                    **context
                ).send_mail(ticket.id, force_send=True)
            return True
        elif self.subject and self.body_html:
            # Use custom subject and body
            subtype = self.env.ref('mail.mt_comment', raise_if_not_found=False)
            for recipient in recipients:
                ticket.message_post(
                    body=self.body_html,
                    subject=self.subject,
                    partner_ids=[recipient.id],
                    subtype_id=subtype.id if subtype else False,
                )
            return True
        return False
    
    def _send_in_app_notification(self, ticket, recipients, context):
        """Send in-app notification"""
        message = self.in_app_message or self.subject or _('Notification: %s') % ticket.ticket_number
        
        # Post message on ticket
        subtype = self.env.ref('mail.mt_comment', raise_if_not_found=False)
        ticket.message_post(
            body=message,
            partner_ids=[r.id for r in recipients],
            subtype_id=subtype.id if subtype else False
        )
        
        # Create activities for users
        for recipient in recipients:
            if recipient.user_ids:
                user = recipient.user_ids[0]
                ticket.activity_schedule(
                    activity_type_id=self.env.ref('mail.mail_activity_data_todo').id,
                    user_id=user.id,
                    note=message
                )
        
        return True
