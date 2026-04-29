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
import ast
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class HelpdeskEscalationRule(models.Model):
    _name = 'helpdesk.escalation.rule'
    _description = 'Helpdesk Escalation Rule'
    _order = 'sequence, id'

    name = fields.Char(
        string='Rule Name',
        required=True,
        help='Name of the escalation rule'
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
            ('sla_based', 'SLA-Based'),
            ('time_based', 'Time-Based'),
            ('status_based', 'Status-Based'),
        ],
        string='Trigger Type',
        required=True,
        default='time_based',
        help='Type of trigger for escalation'
    )
    
    # SLA-Based Trigger
    sla_trigger_type = fields.Selection(
        [
            ('response_time', 'Response Time'),
            ('resolution_time', 'Resolution Time'),
            ('both', 'Both'),
        ],
        string='SLA Trigger Type',
        help='Type of SLA time to monitor (for SLA-based escalation)'
    )
    sla_trigger_percentage = fields.Float(
        string='SLA Trigger Percentage (%)',
        default=90.0,
        help='Percentage of SLA time elapsed to trigger escalation (0-100)'
    )
    sla_policy_ids = fields.Many2many(
        'helpdesk.sla.policy',
        'helpdesk_escalation_rule_sla_policy_rel',
        'escalation_rule_id',
        'sla_policy_id',
        string='SLA Policies',
        help='SLA policies this rule applies to (leave empty for all)'
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
        help='Type of time-based trigger (for time-based escalation)'
    )
    time_trigger_hours = fields.Float(
        string='Trigger After (Hours)',
        default=24.0,
        help='Number of hours after which to trigger escalation'
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
        help='Status to monitor for escalation (for status-based escalation)'
    )
    status_trigger_hours = fields.Float(
        string='Hours in Status',
        default=48.0,
        help='Number of hours ticket can remain in this status before escalation'
    )
    
    # ==================== Condition Configuration ====================
    condition_domain = fields.Text(
        string='Condition Domain',
        help="Domain expression to evaluate. Rule executes only if the ticket matches this domain.\n"
             "Example: [('priority', '=', '3'), ('category_id', '!=', False)]"
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
        help='Priority level this rule applies to (leave as "All Priorities" for all)'
    )
    category_ids = fields.Many2many(
        'helpdesk.category',
        'helpdesk_escalation_rule_category_rel',
        'rule_id',
        'category_id',
        string='Categories',
        help='Categories this rule applies to (leave empty for all)'
    )
    team_ids = fields.Many2many(
        'helpdesk.team',
        'helpdesk_escalation_rule_team_rel',
        'rule_id',
        'team_id',
        string='Teams',
        help='Teams this rule applies to (leave empty for all)'
    )
    
    # ==================== Escalation Path Configuration ====================
    escalation_level = fields.Integer(
        string='Escalation Level',
        default=1,
        help='Level of escalation (1 = first escalation, 2 = second, etc.)'
    )
    parent_rule_id = fields.Many2one(
        'helpdesk.escalation.rule',
        string='Parent Rule',
        help='Parent escalation rule (for escalation paths)'
    )
    child_rule_ids = fields.One2many(
        'helpdesk.escalation.rule',
        'parent_rule_id',
        string='Next Level Rules',
        help='Next level escalation rules'
    )
    
    # ==================== Action Configuration ====================
    action_type = fields.Selection(
        [
            ('notify', 'Notify Users/Team'),
            ('assign', 'Reassign Ticket'),
            ('priority_upgrade', 'Upgrade Priority'),
            ('team_escalate', 'Escalate to Team'),
            ('state_change', 'Change Status'),
            ('post_message', 'Post Message'),
        ],
        string='Action Type',
        required=True,
        default='notify',
        help='Action to take when escalation is triggered'
    )
    
    # Action: Notify
    action_notify_user_ids = fields.Many2many(
        'res.users',
        'helpdesk_escalation_rule_notify_user_rel',
        'rule_id',
        'user_id',
        string='Notify Users',
        help='Users to notify when escalation is triggered'
    )
    action_notify_team_id = fields.Many2one(
        'helpdesk.team',
        string='Notify Team',
        help='Team to notify (all team members will be notified)'
    )
    action_notify_template_id = fields.Many2one(
        'mail.template',
        string='Email Template',
        domain="[('model', '=', 'helpdesk.ticket')]",
        help='Email template to use for notification'
    )
    action_notify_message = fields.Text(
        string='Notification Message',
        help='Message to include in notification'
    )
    
    # Action: Assign
    action_assign_user_id = fields.Many2one(
        'res.users',
        string='Assign to User',
        help='User to assign ticket to'
    )
    action_assign_team_id = fields.Many2one(
        'helpdesk.team',
        string='Assign to Team',
        help='Team to assign ticket to'
    )
    
    # Action: Priority Upgrade
    action_priority_upgrade_to = fields.Selection(
        [
            ('0', 'Low'),
            ('1', 'Medium'),
            ('2', 'High'),
            ('3', 'Urgent'),
        ],
        string='Upgrade to Priority',
        help='Priority level to upgrade to'
    )
    
    # Action: Team Escalate
    action_escalate_to_team_id = fields.Many2one(
        'helpdesk.team',
        string='Escalate to Team',
        help='Team to escalate ticket to'
    )
    
    # Action: State Change
    action_change_state_to = fields.Selection(
        [
            ('new', 'New'),
            ('assigned', 'Assigned'),
            ('in_progress', 'In Progress'),
            ('resolved', 'Resolved'),
            ('closed', 'Closed'),
        ],
        string='Change Status To',
        help='Status to change ticket to'
    )
    
    # Action: Post Message
    action_post_message_body = fields.Html(
        string='Message Body',
        help='Message body to post on ticket'
    )
    
    # ==================== Execution Settings ====================
    repeat_escalation = fields.Boolean(
        string='Repeat Escalation',
        default=False,
        help='Allow this escalation to trigger multiple times'
    )
    repeat_interval_hours = fields.Float(
        string='Repeat Interval (Hours)',
        default=24.0,
        help='Hours between repeated escalations'
    )
    max_repeats = fields.Integer(
        string='Max Repeats',
        default=3,
        help='Maximum number of times to repeat escalation'
    )
    
    # ==================== Execution Tracking ====================
    execution_count = fields.Integer(
        string='Execution Count',
        default=0,
        readonly=True,
        help='Number of times this rule has been executed'
    )
    last_execution_date = fields.Datetime(
        string='Last Execution',
        readonly=True,
        help='Date and time of last rule execution'
    )
    
    # ==================== UI Helper Actions ====================

    def action_test_rule(self):
        """UI action: perform a dry-run test of the escalation rule.

        Currently this only logs that the rule was tested. It can be
        extended to run against sample tickets if needed.
        """
        for rule in self:
            _logger.info('Helpdesk escalation rule "%s" (ID: %s) test triggered from UI.', rule.name, rule.id)
        return True

    def action_view_execution_logs(self):
        """Open escalation logs filtered by this rule."""
        self.ensure_one()
        action = self.env.ref('support_helpdesk_ticket.action_helpdesk_escalation_log')
        result = action.read()[0]
        result['domain'] = [('rule_id', '=', self.id)]
        return result
    
    # ==================== Validation ====================
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
        
        # Check if rule is active
        if not self.active:
            return False
        
        # Evaluate domain condition
        if self.condition_domain:
            try:
                domain = ast.literal_eval(self.condition_domain)
                if not ticket.filtered_domain(domain):
                    return False
            except (ValueError, SyntaxError):
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
        
        return True
    
    def _evaluate_trigger(self, ticket):
        """Evaluate if escalation trigger condition is met"""
        self.ensure_one()
        
        if self.trigger_type == 'sla_based':
            return self._evaluate_sla_trigger(ticket)
        elif self.trigger_type == 'time_based':
            return self._evaluate_time_trigger(ticket)
        elif self.trigger_type == 'status_based':
            return self._evaluate_status_trigger(ticket)
        
        return False
    
    def _evaluate_sla_trigger(self, ticket):
        """Evaluate SLA-based trigger"""
        if not ticket.sla_policy_id:
            return False
        
        # Check if rule applies to this SLA policy
        if self.sla_policy_ids and ticket.sla_policy_id not in self.sla_policy_ids:
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
    
    def _evaluate_status_trigger(self, ticket):
        """Evaluate status-based trigger"""
        if ticket.state != self.status_trigger_states:
            return False
        
        if not ticket.last_stage_update:
            return False
        
        now = fields.Datetime.now()
        elapsed = (now - ticket.last_stage_update).total_seconds() / 3600.0
        
        return elapsed >= self.status_trigger_hours
    
    # ==================== Action Execution ====================
    def _execute_action(self, ticket):
        """Execute the escalation action on ticket"""
        self.ensure_one()
        
        if self.action_type == 'notify':
            self._execute_notify(ticket)
        elif self.action_type == 'assign':
            self._execute_assign(ticket)
        elif self.action_type == 'priority_upgrade':
            self._execute_priority_upgrade(ticket)
        elif self.action_type == 'team_escalate':
            self._execute_team_escalate(ticket)
        elif self.action_type == 'state_change':
            self._execute_state_change(ticket)
        elif self.action_type == 'post_message':
            self._execute_post_message(ticket)
        
        # Update execution tracking
        self.write({
            'execution_count': self.execution_count + 1,
            'last_execution_date': fields.Datetime.now()
        })
    
    def _execute_notify(self, ticket):
        """Execute notify action"""
        recipients = []
        
        if self.action_notify_user_ids:
            recipients.extend(self.action_notify_user_ids.mapped('partner_id'))
        
        if self.action_notify_team_id:
            recipients.extend(self.action_notify_team_id.member_ids.mapped('partner_id'))
        
        if recipients:
            message = self.action_notify_message or _('Escalation rule "%s" was triggered for ticket %s') % (self.name, ticket.ticket_number)
            
            if self.action_notify_template_id:
                # Use email template
                self.action_notify_template_id.send_mail(ticket.id, force_send=True)
            else:
                # Post message on ticket
                subtype = self.env.ref('mail.mt_comment', raise_if_not_found=False)
                ticket.message_post(
                    body=message,
                    partner_ids=recipients.ids,
                    subtype_id=subtype.id if subtype else False
                )
    
    def _execute_assign(self, ticket):
        """Execute assign action"""
        vals = {}
        if self.action_assign_user_id:
            vals['user_id'] = self.action_assign_user_id.id
        if self.action_assign_team_id:
            vals['team_id'] = self.action_assign_team_id.id
        if vals:
            ticket.with_context(assignment_method='escalation').write(vals)
    
    def _execute_priority_upgrade(self, ticket):
        """Execute priority upgrade action"""
        if self.action_priority_upgrade_to:
            current_priority = int(ticket.priority) if ticket.priority else 0
            new_priority = int(self.action_priority_upgrade_to)
            if new_priority > current_priority:
                ticket.write({'priority': self.action_priority_upgrade_to})
    
    def _execute_team_escalate(self, ticket):
        """Execute team escalation"""
        if self.action_escalate_to_team_id:
            ticket.with_context(assignment_method='escalation').write({
                'team_id': self.action_escalate_to_team_id.id,
            })
    
    def _execute_state_change(self, ticket):
        """Execute state change action"""
        if self.action_change_state_to:
            ticket.with_context(
                skip_state_validation=True,
                status_change_reason='escalation'
            ).write({'state': self.action_change_state_to})
    
    def _execute_post_message(self, ticket):
        """Execute post message action"""
        if self.action_post_message_body:
            subtype = self.env.ref('mail.mt_note', raise_if_not_found=False)
            ticket.message_post(
                body=self.action_post_message_body,
                subtype_id=subtype.id if subtype else False
            )
    
    def execute_on_ticket(self, ticket):
        """Execute escalation rule on ticket if conditions match"""
        self.ensure_one()
        
        # Evaluate conditions
        if not self._evaluate_condition(ticket):
            return False
        
        # Evaluate trigger
        if not self._evaluate_trigger(ticket):
            return False
        
        # Check if already executed (unless repeat is enabled)
        if not self.repeat_escalation:
            # Check last execution
            if self.last_execution_date:
                # Check if this ticket was escalated recently
                escalation_log = self.env['helpdesk.escalation.log'].search([
                    ('rule_id', '=', self.id),
                    ('ticket_id', '=', ticket.id),
                ], order='escalation_date desc', limit=1)
                if escalation_log:
                    return False
        
        # Execute action
        self._execute_action(ticket)
        
        # Log escalation
        self.env['helpdesk.escalation.log'].create({
            'rule_id': self.id,
            'ticket_id': ticket.id,
            'escalation_date': fields.Datetime.now(),
            'escalation_level': self.escalation_level,
        })
        
        return True
