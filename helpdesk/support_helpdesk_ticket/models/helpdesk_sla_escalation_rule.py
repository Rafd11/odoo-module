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
from odoo.exceptions import ValidationError
import logging

_logger = logging.getLogger(__name__)


class HelpdeskSLAEscalationRule(models.Model):
    _name = 'helpdesk.sla.escalation.rule'
    _description = 'SLA Escalation Rule'
    _order = 'sequence, name'

    # ==================== Basic Fields ====================
    name = fields.Char(
        string='Rule Name',
        required=True,
        help='Name of the escalation rule'
    )
    sla_policy_id = fields.Many2one(
        'helpdesk.sla.policy',
        string='SLA Policy',
        required=True,
        ondelete='cascade',
        index=True,
        help='SLA policy this rule belongs to'
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help='If unchecked, this rule will be disabled'
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Sequence order for rule execution (lower = higher priority)'
    )

    # ==================== Trigger Conditions ====================
    trigger_type = fields.Selection(
        [
            ('response_time', 'Response Time Elapsed'),
            ('resolution_time', 'Resolution Time Elapsed'),
            ('both', 'Both Response and Resolution'),
        ],
        string='Trigger Type',
        required=True,
        default='response_time',
        help='Type of SLA time that triggers this escalation'
    )
    trigger_percentage = fields.Float(
        string='Trigger Percentage (%)',
        required=True,
        default=80.0,
        help='Percentage of SLA time elapsed to trigger escalation (0-100)'
    )
    trigger_hours = fields.Float(
        string='Trigger Hours',
        help='Alternative: trigger after specific hours (overrides percentage if set)'
    )

    # ==================== Escalation Actions ====================
    action_type = fields.Selection(
        [
            ('notify', 'Notify Users'),
            ('assign', 'Reassign Ticket'),
            ('priority_upgrade', 'Upgrade Priority'),
            ('team_escalate', 'Escalate to Team'),
            ('custom', 'Custom Action'),
        ],
        string='Action Type',
        required=True,
        default='notify',
        help='Action to take when escalation is triggered'
    )
    
    # Notification
    notify_user_ids = fields.Many2many(
        'res.users',
        'helpdesk_sla_escalation_rule_user_rel',
        'escalation_rule_id',
        'user_id',
        string='Notify Users',
        help='Users to notify when escalation is triggered'
    )
    notify_team_id = fields.Many2one(
        'helpdesk.team',
        string='Notify Team',
        help='Team to notify (all team members)'
    )
    email_template_id = fields.Many2one(
        'mail.template',
        string='Email Template',
        domain=[('model', '=', 'helpdesk.ticket')],
        help='Email template to send notification'
    )
    
    # Reassignment
    assign_team_id = fields.Many2one(
        'helpdesk.team',
        string='Assign to Team',
        help='Team to reassign ticket to'
    )
    assign_user_id = fields.Many2one(
        'res.users',
        string='Assign to User',
        help='User to reassign ticket to'
    )
    
    # Priority upgrade
    new_priority = fields.Selection(
        [
            ('0', 'Low'),
            ('1', 'Medium'),
            ('2', 'High'),
            ('3', 'Urgent'),
        ],
        string='New Priority',
        help='New priority level to set'
    )
    
    # Team escalation
    escalate_to_team_id = fields.Many2one(
        'helpdesk.team',
        string='Escalate to Team',
        help='Team to escalate ticket to'
    )
    
    # Custom action
    custom_action_code = fields.Text(
        string='Custom Action Code',
        help='Python code to execute (advanced users only)'
    )

    # ==================== Additional Settings ====================
    repeat_escalation = fields.Boolean(
        string='Repeat Escalation',
        default=False,
        help='Allow this escalation to trigger multiple times'
    )
    repeat_interval = fields.Float(
        string='Repeat Interval (Hours)',
        default=24.0,
        help='Hours between repeated escalations'
    )
    max_repeats = fields.Integer(
        string='Max Repeats',
        default=3,
        help='Maximum number of times to repeat escalation'
    )

    # ==================== Statistics ====================
    trigger_count = fields.Integer(
        string='Trigger Count',
        compute='_compute_trigger_count',
        help='Number of times this rule has been triggered'
    )

    @api.depends('name')
    def _compute_trigger_count(self):
        """Compute trigger count (placeholder - would need escalation history model)"""
        for rule in self:
            rule.trigger_count = 0  # TODO: Implement escalation history tracking

    # ==================== Constraints ====================
    @api.constrains('trigger_percentage')
    def _check_trigger_percentage(self):
        """Validate trigger percentage"""
        for record in self:
            if record.trigger_percentage < 0 or record.trigger_percentage > 100:
                raise ValidationError(_('Trigger percentage must be between 0 and 100.'))

    @api.constrains('action_type', 'notify_user_ids', 'assign_team_id', 'assign_user_id', 'new_priority')
    def _check_action_configuration(self):
        """Validate action configuration"""
        for record in self:
            if record.action_type == 'notify' and not record.notify_user_ids and not record.notify_team_id:
                raise ValidationError(_('Please specify users or team to notify.'))
            elif record.action_type == 'assign' and not record.assign_team_id and not record.assign_user_id:
                raise ValidationError(_('Please specify team or user to assign to.'))
            elif record.action_type == 'priority_upgrade' and not record.new_priority:
                raise ValidationError(_('Please specify new priority level.'))
            elif record.action_type == 'team_escalate' and not record.escalate_to_team_id:
                raise ValidationError(_('Please specify team to escalate to.'))

    def execute(self, ticket):
        """Execute escalation rule for a ticket"""
        self.ensure_one()
        
        if self.action_type == 'notify':
            self._execute_notify(ticket)
        elif self.action_type == 'assign':
            self._execute_assign(ticket)
        elif self.action_type == 'priority_upgrade':
            self._execute_priority_upgrade(ticket)
        elif self.action_type == 'team_escalate':
            self._execute_team_escalate(ticket)
        elif self.action_type == 'custom':
            self._execute_custom(ticket)

    def _execute_notify(self, ticket):
        """Execute notify action"""
        users_to_notify = self.notify_user_ids
        if self.notify_team_id:
            users_to_notify |= self.notify_team_id.member_ids
        
        for user in users_to_notify:
            # Create activity or send email
            if self.email_template_id:
                self.email_template_id.send_mail(ticket.id, force_send=True)
            else:
                ticket.activity_schedule(
                    activity_type_id=self.env.ref('mail.mail_activity_data_todo').id,
                    user_id=user.id,
                    note=_('SLA Escalation: %s') % self.name
                )

    def _execute_assign(self, ticket):
        """Execute assign action"""
        if self.assign_team_id:
            ticket.write({'team_id': self.assign_team_id.id})
        if self.assign_user_id:
            ticket.write({'user_id': self.assign_user_id.id})

    def _execute_priority_upgrade(self, ticket):
        """Execute priority upgrade action"""
        if self.new_priority:
            ticket.write({'priority': self.new_priority})

    def _execute_team_escalate(self, ticket):
        """Execute team escalation"""
        if self.escalate_to_team_id:
            ticket.write({'team_id': self.escalate_to_team_id.id})
            # Optionally unassign from current user
            if ticket.user_id:
                ticket.write({'user_id': False})

    def _execute_custom(self, ticket):
        """Execute custom action code"""
        if self.custom_action_code:
            try:
                # Execute custom code in safe context
                local_dict = {
                    'self': self,
                    'ticket': ticket,
                    'env': self.env,
                }
                exec(self.custom_action_code, {'__builtins__': {}}, local_dict)
            except Exception as e:
                _logger.error(f"Error executing custom escalation action: {e}")
