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
import logging
from datetime import timedelta
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class HelpdeskReminderRule(models.Model):
    _name = 'helpdesk.reminder.rule'
    _description = 'Reminder Rule'
    _order = 'sequence, id'

    name = fields.Char(
        string='Rule Name',
        required=True,
        help='Name of the reminder rule'
    )
    description = fields.Text(
        string='Description',
        help='Description of what this rule does'
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Whether this rule is active'
    )
    sequence = fields.Integer(
        string='Priority',
        default=10,
        help='Lower number = higher priority. Rules are evaluated in order.'
    )
    
    # ==================== Trigger Configuration ====================
    trigger_type = fields.Selection(
        [
            ('status_based', 'Status-Based'),
            ('time_based', 'Time-Based'),
            ('sla_based', 'SLA-Based'),
        ],
        string='Trigger Type',
        required=True,
        default='time_based',
        help='Type of trigger for reminder'
    )
    
    # Status-Based Trigger
    status_trigger_states = fields.Selection(
        [
            ('new', 'New'),
            ('assigned', 'Assigned'),
            ('in_progress', 'In Progress'),
            ('resolved', 'Resolved'),
        ],
        string='Status to Monitor',
        help='Status to monitor for reminder (for status-based reminders)'
    )
    status_trigger_hours = fields.Float(
        string='Hours in Status',
        default=24.0,
        help='Number of hours ticket can remain in this status before reminder'
    )
    
    # Time-Based Trigger
    time_trigger_type = fields.Selection(
        [
            ('since_creation', 'Hours Since Creation'),
            ('since_update', 'Hours Since Last Update'),
            ('since_assignment', 'Hours Since Assignment'),
            ('since_status_change', 'Hours Since Status Change'),
        ],
        string='Time Trigger Type',
        help='Type of time-based trigger'
    )
    time_trigger_hours = fields.Float(
        string='Trigger After (Hours)',
        default=48.0,
        help='Number of hours after which to trigger reminder'
    )
    
    # SLA-Based Trigger
    sla_trigger_type = fields.Selection(
        [
            ('response_time', 'Response Time'),
            ('resolution_time', 'Resolution Time'),
            ('both', 'Both'),
        ],
        string='SLA Trigger Type',
        help='Type of SLA time to monitor'
    )
    sla_trigger_percentage = fields.Float(
        string='SLA Trigger Percentage (%)',
        default=50.0,
        help='Percentage of SLA time elapsed to trigger reminder (0-100)'
    )
    
    # ==================== Condition Configuration ====================
    condition_domain = fields.Text(
        string='Condition Domain',
        help='Domain expression to evaluate. Rule executes only if ticket matches this domain.'
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
        help='Priority level this rule applies to'
    )
    category_ids = fields.Many2many(
        'helpdesk.category',
        'helpdesk_reminder_rule_category_rel',
        'rule_id',
        'category_id',
        string='Categories',
        help='Categories this rule applies to (leave empty for all)'
    )
    team_ids = fields.Many2many(
        'helpdesk.team',
        'helpdesk_reminder_rule_team_rel',
        'rule_id',
        'team_id',
        string='Teams',
        help='Teams this rule applies to (leave empty for all)'
    )
    
    # ==================== Reminder Configuration ====================
    reminder_user_type = fields.Selection(
        [
            ('assigned_user', 'Assigned User'),
            ('team_members', 'Team Members'),
            ('team_leader', 'Team Leader'),
            ('custom_users', 'Custom Users'),
        ],
        string='Remind User',
        required=True,
        default='assigned_user',
        help='Who should receive the reminder'
    )
    reminder_user_ids = fields.Many2many(
        'res.users',
        'helpdesk_reminder_rule_user_rel',
        'rule_id',
        'user_id',
        string='Remind Users',
        help='Specific users to remind (for custom_users type)'
    )
    reminder_message = fields.Text(
        string='Reminder Message',
        help='Message to include in reminder'
    )
    email_template_id = fields.Many2one(
        'mail.template',
        string='Email Template',
        domain="[('model', '=', 'helpdesk.ticket')]",
        help='Email template to use for reminder'
    )
    
    # Recurrence
    is_recurring = fields.Boolean(
        string='Recurring Reminder',
        default=False,
        help='Create recurring reminders'
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
    
    # ==================== Execution Tracking ====================
    execution_count = fields.Integer(
        string='Execution Count',
        default=0,
        readonly=True,
        help='Number of reminders created by this rule'
    )
    last_execution_date = fields.Datetime(
        string='Last Execution',
        readonly=True,
        help='Date and time of last rule execution'
    )

    @api.constrains('sla_trigger_percentage')
    def _check_sla_trigger_percentage(self):
        """Validate SLA trigger percentage"""
        for rule in self:
            if rule.trigger_type == 'sla_based' and rule.sla_trigger_percentage:
                if rule.sla_trigger_percentage < 0 or rule.sla_trigger_percentage > 100:
                    raise ValidationError(_('SLA trigger percentage must be between 0 and 100.'))
    
    @api.constrains('time_trigger_hours', 'status_trigger_hours')
    def _check_trigger_hours(self):
        """Validate trigger hours"""
        for rule in self:
            if rule.trigger_type == 'time_based' and rule.time_trigger_hours < 0:
                raise ValidationError(_('Time trigger hours must be positive.'))
            if rule.trigger_type == 'status_based' and rule.status_trigger_hours < 0:
                raise ValidationError(_('Status trigger hours must be positive.'))
    
    # ==================== Rule Evaluation ====================
    def _evaluate_condition(self, ticket):
        """Evaluate if ticket matches rule conditions"""
        self.ensure_one()
        
        if not self.active:
            return False
        
        # Check priority filter
        if self.priority_filter != 'all' and ticket.priority != self.priority_filter:
            return False
        
        # Check category filter
        if self.category_ids and ticket.category_id not in self.category_ids:
            return False
        
        # Check team filter
        if self.team_ids and ticket.team_id not in self.team_ids:
            return False
        
        # Evaluate domain condition
        if self.condition_domain:
            try:
                domain = ast.literal_eval(self.condition_domain)
                if not ticket.filtered_domain(domain):
                    return False
            except (ValueError, SyntaxError):
                return False
        
        return True
    
    def _evaluate_trigger(self, ticket):
        """Evaluate if reminder trigger condition is met"""
        self.ensure_one()
        
        if self.trigger_type == 'status_based':
            return self._evaluate_status_trigger(ticket)
        elif self.trigger_type == 'time_based':
            return self._evaluate_time_trigger(ticket)
        elif self.trigger_type == 'sla_based':
            return self._evaluate_sla_trigger(ticket)
        
        return False
    
    def _evaluate_status_trigger(self, ticket):
        """Evaluate status-based trigger"""
        if ticket.state != self.status_trigger_states:
            return False
        
        if not ticket.last_stage_update:
            return False
        
        now = fields.Datetime.now()
        elapsed = (now - ticket.last_stage_update).total_seconds() / 3600.0
        
        return elapsed >= self.status_trigger_hours
    
    def _evaluate_time_trigger(self, ticket):
        """Evaluate time-based trigger"""
        now = fields.Datetime.now()
        
        if self.time_trigger_type == 'since_creation':
            elapsed = (now - ticket.create_date).total_seconds() / 3600.0
        elif self.time_trigger_type == 'since_update':
            elapsed = (now - ticket.write_date).total_seconds() / 3600.0
        elif self.time_trigger_type == 'since_assignment':
            if not ticket.assigned_date:
                return False
            elapsed = (now - ticket.assigned_date).total_seconds() / 3600.0
        elif self.time_trigger_type == 'since_status_change':
            if not ticket.last_stage_update:
                return False
            elapsed = (now - ticket.last_stage_update).total_seconds() / 3600.0
        else:
            return False
        
        return elapsed >= self.time_trigger_hours
    
    def _evaluate_sla_trigger(self, ticket):
        """Evaluate SLA-based trigger"""
        if not ticket.sla_policy_id:
            return False
        
        now = fields.Datetime.now()
        policy = ticket.sla_policy_id
        
        if self.sla_trigger_type in ['response_time', 'both']:
            if ticket.sla_response_deadline:
                elapsed = (now - ticket.create_date).total_seconds() / 3600.0
                total_time = policy.response_time
                percentage = (elapsed / total_time) * 100 if total_time > 0 else 0
                if percentage >= self.sla_trigger_percentage:
                    return True
        
        if self.sla_trigger_type in ['resolution_time', 'both']:
            if ticket.sla_resolution_deadline:
                elapsed = (now - ticket.create_date).total_seconds() / 3600.0
                total_time = policy.resolution_time
                percentage = (elapsed / total_time) * 100 if total_time > 0 else 0
                if percentage >= self.sla_trigger_percentage:
                    return True
        
        return False
    
    def _get_reminder_users(self, ticket):
        """Get users to remind"""
        users = []
        
        if self.reminder_user_type == 'assigned_user':
            if ticket.user_id:
                users.append(ticket.user_id)
        
        elif self.reminder_user_type == 'team_members':
            if ticket.team_id:
                users.extend(ticket.team_id.member_ids)
        
        elif self.reminder_user_type == 'team_leader':
            if ticket.team_id and ticket.team_id.team_leader_id:
                users.append(ticket.team_id.team_leader_id)
        
        elif self.reminder_user_type == 'custom_users':
            users.extend(self.reminder_user_ids)
        
        return users
    
    def create_reminder(self, ticket):
        """Create reminder for ticket if conditions match"""
        self.ensure_one()
        
        # Evaluate conditions
        if not self._evaluate_condition(ticket):
            return False
        
        # Evaluate trigger
        if not self._evaluate_trigger(ticket):
            return False
        
        # Check if reminder already exists
        existing = self.env['helpdesk.reminder'].search([
            ('ticket_id', '=', ticket.id),
            ('reminder_rule_id', '=', self.id),
            ('status', 'in', ['pending', 'sent'])
        ], limit=1)
        
        if existing:
            return False
        
        # Get users to remind
        users = self._get_reminder_users(ticket)
        if not users:
            return False
        
        # Calculate reminder date
        reminder_date = fields.Datetime.now()
        
        # Create reminders for each user
        for user in users:
            self.env['helpdesk.reminder'].create({
                'ticket_id': ticket.id,
                'user_id': user.id,
                'reminder_type': 'auto_%s' % self.trigger_type.replace('_based', ''),
                'reminder_date': reminder_date,
                'reminder_message': self.reminder_message,
                'reminder_rule_id': self.id,
                'notify_email': True,
                'notify_in_app': True,
                'email_template_id': self.email_template_id.id,
                'is_recurring': self.is_recurring,
                'recurrence_interval': self.recurrence_interval,
                'max_recurrences': self.max_recurrences,
            })
        
        # Update execution tracking
        self.write({
            'execution_count': self.execution_count + 1,
            'last_execution_date': fields.Datetime.now()
        })
        
        return True
    
    def action_test_rule(self):
        """Test rule on sample tickets"""
        self.ensure_one()
        domain = []
        if self.condition_domain:
            try:
                domain = ast.literal_eval(self.condition_domain)
            except:
                pass
        
        return {
            'name': _('Test Reminder Rule'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket',
            'view_mode': 'tree,form',
            'domain': domain,
            'context': {'default_name': _('Test Ticket for Rule: %s') % self.name},
        }
    
    def action_view_reminders(self):
        """View reminders created by this rule"""
        self.ensure_one()
        return {
            'name': _('Reminders'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.reminder',
            'view_mode': 'tree,form',
            'domain': [('reminder_rule_id', '=', self.id)],
            'context': {'default_reminder_rule_id': self.id},
        }
