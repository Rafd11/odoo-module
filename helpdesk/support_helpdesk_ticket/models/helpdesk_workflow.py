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
from odoo.exceptions import ValidationError
import ast

_logger = logging.getLogger(__name__)


class HelpdeskWorkflowRule(models.Model):
    _name = 'helpdesk.workflow.rule'
    _description = 'Helpdesk Workflow Rule'
    _inherit = ['mail.thread']
    _order = 'sequence, id'

    name = fields.Char(
        string='Rule Name',
        required=True,
        tracking=True,
        help='Name of the workflow rule'
    )
    description = fields.Text(
        string='Description',
        help='Description of what this rule does'
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True,
        help='Whether this rule is active'
    )
    sequence = fields.Integer(
        string='Priority',
        default=10,
        help='Lower number = higher priority. Rules are evaluated in order.'
    )
    
    # ==================== Trigger Configuration ====================
    trigger = fields.Selection(
        [
            ('on_create', 'On Ticket Creation'),
            ('on_update', 'On Ticket Update'),
            ('on_status_change', 'On Status Change'),
            ('on_field_change', 'On Field Change'),
        ],
        string='Trigger',
        required=True,
        help='When this rule should be triggered'
    )
    trigger_field_ids = fields.Many2many(
        'ir.model.fields',
        'helpdesk_workflow_rule_trigger_field_rel',
        'rule_id',
        'field_id',
        string='Trigger Fields',
        domain="[('model', '=', 'helpdesk.ticket')]",
        help='Fields that trigger this rule when changed (for "On Field Change" trigger)'
    )
    
    # ==================== Condition Configuration ====================
    condition_domain = fields.Text(
        string='Condition Domain',
        help="Domain expression to evaluate. Rule executes only if the ticket matches this domain.\n"
             "Example: [('priority', '=', '3'), ('category_id', '!=', False)]"
    )
    ticket_type_ids = fields.Many2many(
        'helpdesk.ticket.type',
        'helpdesk_workflow_rule_ticket_type_rel',
        'rule_id',
        'ticket_type_id',
        string='Ticket Types',
        help='If set, this workflow rule only applies to the selected ticket types. '
             'Leave empty to apply to all types.'
    )
    condition_use_working_hours = fields.Boolean(
        string='Respect Working Hours',
        default=False,
        help='Only execute rule during working hours (if working hours calendar is set)'
    )
    condition_working_hours_id = fields.Many2one(
        'resource.calendar',
        string='Working Hours Calendar',
        help='Working hours calendar for condition evaluation'
    )
    
    # ==================== Action Configuration ====================
    action_type = fields.Selection(
        [
            ('assign', 'Assign to User/Team'),
            ('escalate', 'Escalate'),
            ('notify', 'Send Notification'),
            ('set_field', 'Set Field Value'),
            ('change_priority', 'Change Priority'),
            ('change_state', 'Change State'),
            ('add_tag', 'Add Tag'),
            ('remove_tag', 'Remove Tag'),
            ('post_message', 'Post Message'),
            ('create_task', 'Create Task'),
        ],
        string='Action Type',
        required=True,
        help='Type of action to perform'
    )
    
    # Action: Assign
    action_assign_user_id = fields.Many2one(
        'res.users',
        string='Assign to User',
        help='User to assign ticket to (for Assign action). Leave empty to use assignment algorithm.'
    )
    action_assign_team_id = fields.Many2one(
        'helpdesk.team',
        string='Assign to Team',
        help='Team to assign ticket to (for Assign action). Required for algorithm-based assignment.'
    )
    action_assign_algorithm = fields.Selection(
        [
            ('manual', 'Manual (Use specified user)'),
            ('round_robin', 'Round-Robin'),
            ('workload_based', 'Workload-Based'),
            ('skill_based', 'Skill-Based'),
        ],
        string='Assignment Algorithm',
        default='manual',
        help='Algorithm to use for automatic assignment. Only applies if no user is specified.'
    )
    
    # Action: Escalate
    action_escalate_priority = fields.Selection(
        [
            ('0', 'Low'),
            ('1', 'Medium'),
            ('2', 'High'),
            ('3', 'Urgent'),
        ],
        string='Escalate to Priority',
        help='Priority level to escalate to (for Escalate action)'
    )
    action_escalate_team_id = fields.Many2one(
        'helpdesk.team',
        string='Escalate to Team',
        help='Team to escalate ticket to (for Escalate action)'
    )
    
    # Action: Notify
    action_notify_user_ids = fields.Many2many(
        'res.users',
        'helpdesk_workflow_rule_notify_user_rel',
        'rule_id',
        'user_id',
        string='Notify Users',
        help='Users to notify (for Notify action)'
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
    
    # Action: Set Field
    action_set_field_name = fields.Char(
        string='Field Name',
        help='Name of field to set (for Set Field action)'
    )
    action_set_field_value = fields.Char(
        string='Field Value',
        help='Value to set (for Set Field action). Use Python expressions for dynamic values.'
    )
    
    # Action: Change Priority
    action_change_priority_value = fields.Selection(
        [
            ('0', 'Low'),
            ('1', 'Medium'),
            ('2', 'High'),
            ('3', 'Urgent'),
        ],
        string='New Priority',
        help='Priority value to set (for Change Priority action)'
    )
    
    # Action: Change State
    action_change_state_value = fields.Selection(
        [
            ('draft', 'Draft'),
            ('new', 'New'),
            ('assigned', 'Assigned'),
            ('in_progress', 'In Progress'),
            ('resolved', 'Resolved'),
            ('closed', 'Closed'),
            ('cancelled', 'Cancelled'),
        ],
        string='New State',
        help='State value to set (for Change State action)'
    )
    
    # Action: Add/Remove Tag
    action_tag_ids = fields.Many2many(
        'helpdesk.tag',
        'helpdesk_workflow_rule_tag_rel',
        'rule_id',
        'tag_id',
        string='Tags',
        help='Tags to add or remove (for Add/Remove Tag actions)'
    )
    
    # Action: Post Message
    action_post_message_body = fields.Html(
        string='Message Body',
        help='Message body to post on ticket (for Post Message action)'
    )
    action_post_message_subtype = fields.Selection(
        [
            ('mail.mt_comment', 'Comment'),
            ('mail.mt_note', 'Note'),
        ],
        string='Message Subtype',
        default='mail.mt_note',
        help='Message subtype for posting'
    )
    
    # Action: Create Task
    action_create_task_user_id = fields.Many2one(
        'res.users',
        string='Assign Task to User',
        help='User to assign the task to (for Create Task action)'
    )
    action_create_task_summary = fields.Char(
        string='Task Summary',
        help='Summary/name of the task to create'
    )
    action_create_task_note = fields.Text(
        string='Task Note',
        help='Additional notes for the task'
    )
    action_create_task_date_deadline = fields.Date(
        string='Task Deadline',
        help='Deadline for the task (optional)'
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
    
    # ==================== Validation ====================
    @api.constrains('condition_domain')
    def _check_condition_domain(self):
        """Validate condition domain syntax"""
        for rule in self:
            if rule.condition_domain:
                try:
                    ast.literal_eval(rule.condition_domain)
                except (ValueError, SyntaxError):
                    raise ValidationError(_('Invalid domain syntax. Please check your condition domain.'))
    
    @api.constrains('action_type', 'action_assign_user_id', 'action_assign_team_id', 'action_assign_algorithm')
    def _check_assign_action(self):
        """Validate assign action has user or team"""
        for rule in self:
            if rule.action_type == 'assign':
                # If manual algorithm, user is required
                if rule.action_assign_algorithm == 'manual':
                    if not rule.action_assign_user_id:
                        raise ValidationError(_('Assign action with Manual algorithm requires a user to be specified.'))
                # For other algorithms, team is required
                elif rule.action_assign_algorithm:
                    if not rule.action_assign_team_id:
                        raise ValidationError(_('Assign action with %s algorithm requires a team to be specified.') % dict(rule._fields['action_assign_algorithm'].selection)[rule.action_assign_algorithm])
                # Fallback: require either user or team if algorithm not set
                else:
                    if not rule.action_assign_user_id and not rule.action_assign_team_id:
                        raise ValidationError(_('Assign action requires either a user or team to be specified.'))
    
    @api.constrains('action_type', 'action_set_field_name')
    def _check_set_field_action(self):
        """Validate set field action has field name"""
        for rule in self:
            if rule.action_type == 'set_field':
                if not rule.action_set_field_name:
                    raise ValidationError(_('Set Field action requires a field name to be specified.'))
    
    @api.constrains('action_type', 'action_create_task_summary')
    def _check_create_task_action(self):
        """Validate create task action has summary"""
        for rule in self:
            if rule.action_type == 'create_task':
                if not rule.action_create_task_summary:
                    raise ValidationError(_('Create Task action requires a task summary to be specified.'))
    
    # ==================== Rule Execution ====================
    def _evaluate_condition(self, ticket):
        """Evaluate if ticket matches rule conditions"""
        self.ensure_one()

        # Check if rule is active
        if not self.active:
            return False

        # Task 9.3: Type-specific workflows - filter by ticket type if configured
        if self.ticket_type_ids:
            if not ticket.ticket_type_id or ticket.ticket_type_id not in self.ticket_type_ids:
                return False

        # Evaluate domain condition
        if self.condition_domain:
            try:
                domain = ast.literal_eval(self.condition_domain)
                if not ticket.filtered_domain(domain):
                    return False
            except (ValueError, SyntaxError):
                # Invalid domain, skip rule
                return False
        
        # Check working hours if enabled
        if self.condition_use_working_hours and self.condition_working_hours_id:
            # This would require checking current time against working hours
            # For now, we'll skip this check (can be enhanced later)
            pass
        
        return True
    
    def _execute_action(self, ticket):
        """Execute the workflow rule action on ticket"""
        self.ensure_one()
        
        if self.action_type == 'assign':
            vals = {}
            assignment_method = 'workflow'
            
            # Set team if specified
            if self.action_assign_team_id:
                vals['team_id'] = self.action_assign_team_id.id
            
            # Assign user
            if self.action_assign_user_id:
                # Manual assignment via workflow
                vals['user_id'] = self.action_assign_user_id.id
            elif self.action_assign_team_id and self.action_assign_algorithm != 'manual':
                # Algorithm-based assignment
                algorithm_map = {
                    'round_robin': 'round_robin',
                    'workload_based': 'workload_based',
                    'skill_based': 'skill_based',
                }
                assignment_method = algorithm_map.get(self.action_assign_algorithm, 'workflow')
                user = self._get_assigned_user(ticket, self.action_assign_team_id, self.action_assign_algorithm)
                if user:
                    vals['user_id'] = user.id
            
            if vals:
                # Pass assignment method and workflow rule in context for history tracking
                ticket.with_context(
                    assignment_method=assignment_method,
                    workflow_rule_id=self.id
                ).write(vals)
        
        elif self.action_type == 'escalate':
            vals = {}
            if self.action_escalate_priority:
                vals['priority'] = self.action_escalate_priority
            if self.action_escalate_team_id:
                vals['team_id'] = self.action_escalate_team_id.id
            if vals:
                ticket.write(vals)
        
        elif self.action_type == 'notify':
            self._send_notification(ticket)
        
        elif self.action_type == 'set_field':
            if self.action_set_field_name:
                try:
                    # Try to evaluate as Python expression, fallback to literal value
                    try:
                        value = ast.literal_eval(self.action_set_field_value)
                    except:
                        value = self.action_set_field_value
                    ticket.write({self.action_set_field_name: value})
                except:
                    pass  # Skip if field doesn't exist or value is invalid
        
        elif self.action_type == 'change_priority':
            if self.action_change_priority_value:
                ticket.write({'priority': self.action_change_priority_value})
        
        elif self.action_type == 'change_state':
            if self.action_change_state_value:
                ticket.write({'state': self.action_change_state_value})
        
        elif self.action_type == 'add_tag':
            if self.action_tag_ids:
                ticket.write({'tag_ids': [(4, tag.id) for tag in self.action_tag_ids]})
        
        elif self.action_type == 'remove_tag':
            if self.action_tag_ids:
                ticket.write({'tag_ids': [(3, tag.id) for tag in self.action_tag_ids]})
        
        elif self.action_type == 'post_message':
            if self.action_post_message_body:
                subtype_xmlid = self.action_post_message_subtype or 'mail.mt_note'
                subtype = self.env.ref(subtype_xmlid, raise_if_not_found=False)
                ticket.message_post(
                    body=self.action_post_message_body,
                    subtype_id=subtype.id if subtype else False
                )
        
        elif self.action_type == 'create_task':
            self._create_task(ticket)
        
        # Update execution tracking
        self.write({
            'execution_count': self.execution_count + 1,
            'last_execution_date': fields.Datetime.now()
        })
    
    def _send_notification(self, ticket):
        """Send notification to users/team"""
        self.ensure_one()
        recipients = []
        
        if self.action_notify_user_ids:
            recipients.extend(self.action_notify_user_ids.mapped('partner_id'))
        
        if self.action_notify_team_id:
            recipients.extend(self.action_notify_team_id.member_ids.mapped('partner_id'))
        
        if recipients:
            message = self.action_notify_message or _('Workflow rule "%s" was triggered for ticket %s') % (self.name, ticket.ticket_number)
            
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
    
    def _create_task(self, ticket):
        """Create a task (activity) for the ticket"""
        self.ensure_one()
        
        # Create a mail activity (task)
        summary = self.action_create_task_summary or _('Task from workflow rule: %s') % self.name
        note = self.action_create_task_note or _('Automatically created by workflow rule "%s" for ticket %s') % (self.name, ticket.ticket_number)
        
        # Get the default activity type (Todo)
        activity_type = False
        try:
            activity_type = self.env.ref('mail.mail_activity_data_todo').id
        except:
            # If default activity type doesn't exist, try to get any activity type
            activity_type_obj = self.env['mail.activity.type'].search([], limit=1)
            if activity_type_obj:
                activity_type = activity_type_obj.id
        
        activity_vals = {
            'res_id': ticket.id,
            'res_model_id': self.env['ir.model']._get_id('helpdesk.ticket'),
            'summary': summary,
            'note': note,
            'user_id': self.action_create_task_user_id.id if self.action_create_task_user_id else ticket.user_id.id or self.env.user.id,
        }
        
        if self.action_create_task_date_deadline:
            activity_vals['date_deadline'] = self.action_create_task_date_deadline
        
        if activity_type:
            activity_vals['activity_type_id'] = activity_type
        
        try:
            self.env['mail.activity'].create(activity_vals)
        except Exception as e:
            # If activity creation fails, log and continue
            _logger.warning('Failed to create task for workflow rule %s: %s', self.name, str(e))
    
    def execute_on_ticket(self, ticket, trigger_type=None):
        """Execute rule on ticket if conditions match"""
        self.ensure_one()
        
        # Check trigger type matches
        if trigger_type:
            trigger_map = {
                'create': 'on_create',
                'write': 'on_update',
                'state_change': 'on_status_change',
            }
            if self.trigger != trigger_map.get(trigger_type, self.trigger):
                return False
        
        # Evaluate conditions
        if not self._evaluate_condition(ticket):
            return False
        
        # Execute action
        self._execute_action(ticket)
        return True
    
    def _get_assigned_user(self, ticket, team, algorithm):
        """
        Get user to assign based on algorithm
        
        :param ticket: The ticket to assign
        :param team: The team to assign from
        :param algorithm: The algorithm to use
        :return: res.users record or False
        """
        self.ensure_one()
        
        if not team or not team.member_ids:
            return False
        
        members = team.member_ids.filtered(lambda u: u.active)
        if not members:
            return False
        
        if algorithm == 'round_robin':
            return self._assign_round_robin(ticket, members)
        elif algorithm == 'workload_based':
            return self._assign_workload_based(ticket, members)
        elif algorithm == 'skill_based':
            return self._assign_skill_based(ticket, members)
        
        return False
    
    def _assign_round_robin(self, ticket, members):
        """Assign using round-robin algorithm"""
        # Get the last assigned user for this team
        last_ticket = self.env['helpdesk.ticket'].search([
            ('team_id', '=', ticket.team_id.id if ticket.team_id else False),
            ('user_id', 'in', members.ids),
        ], order='create_date desc', limit=1)
        
        if last_ticket and last_ticket.user_id in members:
            # Find next user in sequence
            current_index = members.ids.index(last_ticket.user_id.id)
            next_index = (current_index + 1) % len(members)
            return members[next_index]
        else:
            # First assignment, use first member
            return members[0] if members else False
    
    def _assign_workload_based(self, ticket, members):
        """Assign based on current workload (number of open tickets)"""
        # Count open tickets per user
        open_states = ['new', 'assigned', 'in_progress']
        workload = {}
        
        for member in members:
            ticket_count = self.env['helpdesk.ticket'].search_count([
                ('user_id', '=', member.id),
                ('state', 'in', open_states),
            ])
            workload[member.id] = ticket_count
        
        # Assign to user with least workload
        if workload:
            min_workload = min(workload.values())
            candidates = [uid for uid, count in workload.items() if count == min_workload]
            # If multiple users have same workload, use round-robin among them
            if len(candidates) > 1:
                # Get last assigned from candidates
                last_ticket = self.env['helpdesk.ticket'].search([
                    ('user_id', 'in', candidates),
                ], order='create_date desc', limit=1)
                if last_ticket and last_ticket.user_id.id in candidates:
                    current_index = candidates.index(last_ticket.user_id.id)
                    next_index = (current_index + 1) % len(candidates)
                    return self.env['res.users'].browse(candidates[next_index])
            return self.env['res.users'].browse(candidates[0])
        
        return members[0] if members else False
    
    def _assign_skill_based(self, ticket, members):
        """
        Assign based on skills/category matching
        Note: This is a basic implementation. Can be enhanced with a skills model.
        """
        # Basic implementation: prefer users who have handled similar tickets
        if ticket.category_id:
            # Find users who have resolved tickets in this category
            category_tickets = self.env['helpdesk.ticket'].search([
                ('category_id', '=', ticket.category_id.id),
                ('user_id', 'in', members.ids),
                ('state', '=', 'closed'),
            ])
            
            if category_tickets:
                # Count resolved tickets per user
                user_counts = {}
                for t in category_tickets:
                    user_counts[t.user_id.id] = user_counts.get(t.user_id.id, 0) + 1
                
                # Assign to user with most experience in this category
                if user_counts:
                    max_count = max(user_counts.values())
                    experienced_users = [uid for uid, count in user_counts.items() if count == max_count]
                    if len(experienced_users) == 1:
                        return self.env['res.users'].browse(experienced_users[0])
                    else:
                        # Multiple users with same experience, use workload-based
                        return self._assign_workload_based(ticket, members.filtered(lambda u: u.id in experienced_users))
        
        # Fallback to workload-based
        return self._assign_workload_based(ticket, members)
    
    def _assign_team_based(self, ticket, team):
        """
        Assign ticket to team using team's default assignment algorithm
        
        :param ticket: The ticket to assign
        :param team: The team to assign to
        :return: res.users record or False
        """
        self.ensure_one()
        
        if not team or not team.member_ids:
            return False
        
        # Use team's default algorithm if auto-assignment is enabled
        if team.auto_assign_enabled and team.default_assignment_algorithm:
            return self._get_assigned_user(ticket, team, team.default_assignment_algorithm)
        
        # Otherwise, assign to team leader if available
        if team.team_leader_id and team.team_leader_id in team.member_ids:
            return team.team_leader_id
        
        # Fallback to first member
        return team.member_ids[0] if team.member_ids else False
    
    def action_test_rule(self):
        """Test rule on sample tickets"""
        self.ensure_one()
        return {
            'name': _('Test Workflow Rule'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket',
            'view_mode': 'tree,form',
            'domain': self.condition_domain and ast.literal_eval(self.condition_domain) or [],
            'context': {'default_name': _('Test Ticket for Rule: %s') % self.name},
        }
    
    def action_view_execution_logs(self):
        """View execution logs for this rule"""
        self.ensure_one()
        return {
            'name': _('Execution Logs'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.workflow.execution.log',
            'view_mode': 'tree,form',
            'domain': [('rule_id', '=', self.id)],
            'context': {'default_rule_id': self.id},
        }
    
    def action_debug_rule(self):
        """Debug workflow rule - test on current tickets"""
        self.ensure_one()
        # Find tickets that match this rule's conditions
        domain = []
        if self.condition_domain:
            try:
                domain = ast.literal_eval(self.condition_domain)
            except:
                pass
        
        return {
            'name': _('Debug Workflow Rule: %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket',
            'view_mode': 'tree,form',
            'domain': domain,
            'context': {
                'default_name': _('Debug Test for Rule: %s') % self.name,
                'workflow_debug_mode': True,
            },
        }
