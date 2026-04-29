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
from datetime import timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class HelpdeskReminder(models.Model):
    _name = 'helpdesk.reminder'
    _description = 'Follow-up Reminder'
    _order = 'reminder_date, id'
    _rec_name = 'display_name'

    ticket_id = fields.Many2one(
        'helpdesk.ticket',
        string='Ticket',
        required=True,
        ondelete='cascade',
        index=True,
        help='Ticket this reminder is for'
    )
    user_id = fields.Many2one(
        'res.users',
        string='Remind User',
        required=True,
        default=lambda self: self.env.user,
        index=True,
        help='User to remind'
    )
    reminder_type = fields.Selection(
        [
            ('manual', 'Manual'),
            ('auto_status', 'Auto: Status-Based'),
            ('auto_time', 'Auto: Time-Based'),
            ('auto_sla', 'Auto: SLA-Based'),
        ],
        string='Reminder Type',
        required=True,
        default='manual',
        help='Type of reminder'
    )
    reminder_date = fields.Datetime(
        string='Reminder Date',
        required=True,
        index=True,
        help='Date and time when reminder should be sent'
    )
    reminder_message = fields.Text(
        string='Reminder Message',
        help='Custom message for the reminder'
    )
    status = fields.Selection(
        [
            ('pending', 'Pending'),
            ('sent', 'Sent'),
            ('dismissed', 'Dismissed'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='pending',
        required=True,
        help='Status of the reminder'
    )
    sent_date = fields.Datetime(
        string='Sent Date',
        readonly=True,
        help='Date and time when reminder was sent'
    )
    dismissed_date = fields.Datetime(
        string='Dismissed Date',
        readonly=True,
        help='Date and time when reminder was dismissed'
    )
    
    # Configuration (for auto reminders)
    reminder_rule_id = fields.Many2one(
        'helpdesk.reminder.rule',
        string='Reminder Rule',
        ondelete='set null',
        help='Reminder rule that created this reminder (for auto reminders)'
    )
    
    # Notification settings
    notify_email = fields.Boolean(
        string='Send Email',
        default=True,
        help='Send email notification for reminder'
    )
    notify_in_app = fields.Boolean(
        string='In-App Notification',
        default=True,
        help='Create in-app activity for reminder'
    )
    email_template_id = fields.Many2one(
        'mail.template',
        string='Email Template',
        domain="[('model', '=', 'helpdesk.ticket')]",
        help='Email template to use for reminder notification'
    )
    
    # Recurrence
    is_recurring = fields.Boolean(
        string='Recurring',
        default=False,
        help='Repeat this reminder periodically'
    )
    recurrence_interval = fields.Integer(
        string='Recurrence Interval (Days)',
        default=7,
        help='Days between recurring reminders'
    )
    max_recurrences = fields.Integer(
        string='Max Recurrences',
        default=5,
        help='Maximum number of times to repeat reminder'
    )
    recurrence_count = fields.Integer(
        string='Recurrence Count',
        default=0,
        readonly=True,
        help='Number of times reminder has been sent'
    )
    
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True
    )

    @api.depends('ticket_id', 'reminder_date', 'user_id', 'status')
    def _compute_display_name(self):
        """Compute display name"""
        for reminder in self:
            ticket_number = reminder.ticket_id.ticket_number if reminder.ticket_id else _('Unknown')
            user_name = reminder.user_id.name if reminder.user_id else _('Unknown')
            status_label = dict(reminder._fields['status'].selection).get(reminder.status, reminder.status)
            reminder.display_name = _('%s - %s (%s)') % (ticket_number, user_name, status_label)

    @api.constrains('reminder_date')
    def _check_reminder_date(self):
        """Validate reminder date"""
        for reminder in self:
            if reminder.reminder_date < fields.Datetime.now() and reminder.status == 'pending':
                # Allow past dates for manual reminders, but warn
                pass

    def action_send_now(self):
        """Send reminder immediately"""
        self.ensure_one()
        if self.status != 'pending':
            return False
        
        try:
            self._send_reminder()
            self.write({
                'status': 'sent',
                'sent_date': fields.Datetime.now(),
                'recurrence_count': self.recurrence_count + 1
            })
            
            # Create next recurrence if needed
            if self.is_recurring and self.recurrence_count < self.max_recurrences:
                self._create_next_recurrence()
            
            return True
        except Exception as e:
            _logger.error('Error sending reminder %s: %s', self.id, str(e))
            return False
    
    def action_dismiss(self):
        """Dismiss reminder"""
        self.ensure_one()
        if self.status == 'pending':
            self.write({
                'status': 'dismissed',
                'dismissed_date': fields.Datetime.now()
            })
        return True
    
    def action_cancel(self):
        """Cancel reminder"""
        self.ensure_one()
        if self.status == 'pending':
            self.write({'status': 'cancelled'})
        return True
    
    def _send_reminder(self):
        """Send reminder notification"""
        self.ensure_one()
        
        message = self.reminder_message or _('Reminder: Follow up on ticket %s') % self.ticket_id.ticket_number
        
        # Email notification
        if self.notify_email:
            if self.email_template_id:
                self.email_template_id.send_mail(self.ticket_id.id, force_send=True)
            elif self.user_id.email:
                subtype = self.env.ref('mail.mt_comment', raise_if_not_found=False)
                self.ticket_id.message_post(
                    body=message,
                    subject=_('Reminder: %s') % self.ticket_id.ticket_number,
                    partner_ids=[self.user_id.partner_id.id],
                    subtype_id=subtype.id if subtype else False,
                )
        
        # In-app notification
        if self.notify_in_app:
            # Post message on ticket
            subtype = self.env.ref('mail.mt_note', raise_if_not_found=False)
            self.ticket_id.message_post(
                body=_('🔔 <b>Reminder:</b> %s') % message,
                partner_ids=[self.user_id.partner_id.id],
                subtype_id=subtype.id if subtype else False
            )
            
            # Create activity
            self.ticket_id.activity_schedule(
                activity_type_id=self.env.ref('mail.mail_activity_data_todo').id,
                user_id=self.user_id.id,
                note=message,
                date_deadline=self.reminder_date.date() if self.reminder_date else fields.Date.today()
            )
    
    def _create_next_recurrence(self):
        """Create next recurrence of reminder"""
        self.ensure_one()
        next_date = self.reminder_date + timedelta(days=self.recurrence_interval)
        
        self.create({
            'ticket_id': self.ticket_id.id,
            'user_id': self.user_id.id,
            'reminder_type': self.reminder_type,
            'reminder_date': next_date,
            'reminder_message': self.reminder_message,
            'reminder_rule_id': self.reminder_rule_id.id,
            'notify_email': self.notify_email,
            'notify_in_app': self.notify_in_app,
            'email_template_id': self.email_template_id.id,
            'is_recurring': self.is_recurring,
            'recurrence_interval': self.recurrence_interval,
            'max_recurrences': self.max_recurrences,
            'recurrence_count': self.recurrence_count + 1,
        })
    
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

    @api.model
    def process_due_reminders(self):
        """Process reminders that are due"""
        now = fields.Datetime.now()
        due_reminders = self.search([
            ('status', '=', 'pending'),
            ('reminder_date', '<=', now)
        ])
        
        sent_count = 0
        for reminder in due_reminders:
            if reminder.action_send_now():
                sent_count += 1
        
        return sent_count
