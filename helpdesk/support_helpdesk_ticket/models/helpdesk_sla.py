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


class HelpdeskSLAPolicy(models.Model):
    _name = 'helpdesk.sla.policy'
    _description = 'Helpdesk SLA Policy'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'sequence, name'

    # ==================== Basic Fields ====================
    name = fields.Char(
        string='Policy Name',
        required=True,
        tracking=True,
        help='Name of the SLA policy'
    )
    description = fields.Text(
        string='Description',
        tracking=True,
        help='Description of the SLA policy'
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True,
        help='If unchecked, this policy will be hidden'
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Sequence order for policy matching (lower = higher priority)'
    )

    # ==================== Rule-Based Assignment ====================
    # Priority-based rules (priority is a selection field, not a model)
    priority_selection = fields.Selection(
        [
            ('0', 'Low'),
            ('1', 'Medium'),
            ('2', 'High'),
            ('3', 'Urgent'),
        ],
        string='Priority',
        help='Priority level this SLA applies to (leave empty for all priorities)'
    )
    priority_all = fields.Boolean(
        string='All Priorities',
        default=True,
        compute='_compute_priority_all',
        inverse='_inverse_priority_all',
        help='Apply to all priorities if no specific priority selected'
    )

    # Category-based rules
    category_ids = fields.Many2many(
        'helpdesk.category',
        'helpdesk_sla_policy_category_rel',
        'sla_policy_id',
        'category_id',
        string='Categories',
        help='Categories this SLA policy applies to (leave empty for all)'
    )
    category_all = fields.Boolean(
        string='All Categories',
        default=True,
        help='Apply to all categories if no specific categories selected'
    )

    # Type-based rules
    ticket_type_ids = fields.Many2many(
        'helpdesk.ticket.type',
        'helpdesk_sla_policy_ticket_type_rel',
        'sla_policy_id',
        'ticket_type_id',
        string='Ticket Types',
        help='Ticket types this SLA policy applies to (leave empty for all)'
    )
    ticket_type_all = fields.Boolean(
        string='All Ticket Types',
        default=True,
        help='Apply to all ticket types if no specific types selected'
    )

    # Team-based rules (optional)
    team_ids = fields.Many2many(
        'helpdesk.team',
        'helpdesk_sla_policy_team_rel',
        'sla_policy_id',
        'team_id',
        string='Teams',
        help='Teams this SLA policy applies to (leave empty for all teams)'
    )
    team_all = fields.Boolean(
        string='All Teams',
        default=True,
        help='Apply to all teams if no specific teams selected'
    )

    # ==================== SLA Time Configuration ====================
    response_time = fields.Float(
        string='Response Time (Hours)',
        required=True,
        default=24.0,
        tracking=True,
        help='Time in hours for first response (assignment or first comment)'
    )
    resolution_time = fields.Float(
        string='Resolution Time (Hours)',
        required=True,
        default=72.0,
        tracking=True,
        help='Time in hours for ticket resolution'
    )
    
    # Response time thresholds
    response_warning_threshold = fields.Float(
        string='Response Warning Threshold (%)',
        default=80.0,
        help='Percentage of response time elapsed to trigger warning (default: 80%)'
    )
    response_escalation_threshold = fields.Float(
        string='Response Escalation Threshold (%)',
        default=90.0,
        help='Percentage of response time elapsed to trigger escalation (default: 90%)'
    )
    
    # Resolution time thresholds
    resolution_warning_threshold = fields.Float(
        string='Resolution Warning Threshold (%)',
        default=80.0,
        help='Percentage of resolution time elapsed to trigger warning (default: 80%)'
    )
    resolution_escalation_threshold = fields.Float(
        string='Resolution Escalation Threshold (%)',
        default=90.0,
        help='Percentage of resolution time elapsed to trigger escalation (default: 90%)'
    )

    # ==================== Working Hours Configuration ====================
    working_hours = fields.Boolean(
        string='Use Working Hours',
        default=False,
        tracking=True,
        help='Calculate SLA based on working hours only (excludes weekends and holidays)'
    )
    working_hours_id = fields.Many2one(
        'resource.calendar',
        string='Working Hours Calendar',
        help='Working hours calendar to use for SLA calculation'
    )
    timezone = fields.Selection(
        '_get_timezone_selection',
        string='Timezone',
        default='UTC',
        help='Timezone for working hours calculation'
    )

    # ==================== Escalation Rules ====================
    escalation_rule_ids = fields.One2many(
        'helpdesk.sla.escalation.rule',
        'sla_policy_id',
        string='Escalation Rules',
        help='Escalation rules for this SLA policy'
    )
    auto_escalate = fields.Boolean(
        string='Auto-Escalate on Breach',
        default=False,
        help='Automatically escalate tickets when SLA is breached'
    )
    escalation_team_id = fields.Many2one(
        'helpdesk.team',
        string='Escalation Team',
        help='Team to escalate to when SLA is breached'
    )
    escalation_user_id = fields.Many2one(
        'res.users',
        string='Escalation User',
        help='User to notify when SLA is breached'
    )

    # ==================== Statistics ====================
    ticket_count = fields.Integer(
        string='Tickets Count',
        compute='_compute_ticket_statistics',
        help='Number of tickets using this SLA policy'
    )
    active_ticket_count = fields.Integer(
        string='Active Tickets',
        compute='_compute_ticket_statistics',
        help='Number of active tickets using this SLA policy'
    )
    met_count = fields.Integer(
        string='SLA Met',
        compute='_compute_ticket_statistics',
        help='Number of tickets that met SLA'
    )
    breached_count = fields.Integer(
        string='SLA Breached',
        compute='_compute_ticket_statistics',
        help='Number of tickets that breached SLA'
    )

    # ==================== Computed Methods ====================
    @api.depends('priority_selection')
    def _compute_priority_all(self):
        """Compute priority_all based on priority_selection"""
        for record in self:
            record.priority_all = not bool(record.priority_selection)

    def _inverse_priority_all(self):
        """Inverse priority_all - clear priority_selection if all priorities"""
        for record in self:
            if record.priority_all:
                record.priority_selection = False

    @api.onchange('category_ids')
    def _onchange_category_ids(self):
        """Update category_all when categories change"""
        if self.category_ids:
            self.category_all = False
        elif not self.category_ids:
            self.category_all = True

    @api.onchange('category_all')
    def _onchange_category_all(self):
        """Clear categories when all categories is selected"""
        if self.category_all:
            self.category_ids = False

    @api.onchange('ticket_type_ids')
    def _onchange_ticket_type_ids(self):
        """Update ticket_type_all when types change"""
        if self.ticket_type_ids:
            self.ticket_type_all = False
        elif not self.ticket_type_ids:
            self.ticket_type_all = True

    @api.onchange('ticket_type_all')
    def _onchange_ticket_type_all(self):
        """Clear ticket types when all types is selected"""
        if self.ticket_type_all:
            self.ticket_type_ids = False

    @api.onchange('team_ids')
    def _onchange_team_ids(self):
        """Update team_all when teams change"""
        if self.team_ids:
            self.team_all = False
        elif not self.team_ids:
            self.team_all = True

    @api.onchange('team_all')
    def _onchange_team_all(self):
        """Clear teams when all teams is selected"""
        if self.team_all:
            self.team_ids = False

    @api.model
    def _get_timezone_selection(self):
        """Get timezone selection list"""
        # Common timezones - can be extended
        return [
            ('UTC', 'UTC'),
            ('America/New_York', 'Eastern Time (US)'),
            ('America/Chicago', 'Central Time (US)'),
            ('America/Denver', 'Mountain Time (US)'),
            ('America/Los_Angeles', 'Pacific Time (US)'),
            ('Europe/London', 'London'),
            ('Europe/Paris', 'Paris'),
            ('Asia/Tokyo', 'Tokyo'),
            ('Asia/Shanghai', 'Shanghai'),
            ('Asia/Kolkata', 'India'),
        ]

    @api.depends('name')
    def _compute_ticket_statistics(self):
        """Compute ticket statistics for this SLA policy"""
        for policy in self:
            tickets = self.env['helpdesk.ticket'].search([
                ('sla_policy_id', '=', policy.id)
            ])
            policy.ticket_count = len(tickets)
            policy.active_ticket_count = len(tickets.filtered(
                lambda t: t.state not in ['closed', 'cancelled', 'resolved']
            ))
            policy.met_count = len(tickets.filtered(
                lambda t: t.sla_response_status == 'met' and t.sla_resolution_status == 'met'
            ))
            policy.breached_count = len(tickets.filtered(
                lambda t: t.sla_response_status == 'breached' or t.sla_resolution_status == 'breached'
            ))

    # ==================== Action Methods ====================
    def action_view_tickets(self):
        """View tickets using this SLA policy"""
        self.ensure_one()
        action = {
            'name': _('Tickets with %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket',
            'view_mode': 'tree,form,kanban',
            'domain': [('sla_policy_id', '=', self.id)],
            'context': {'default_sla_policy_id': self.id},
        }
        return action

    def action_view_active_tickets(self):
        """View active tickets using this SLA policy"""
        self.ensure_one()
        action = {
            'name': _('Active Tickets with %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket',
            'view_mode': 'tree,form,kanban',
            'domain': [
                ('sla_policy_id', '=', self.id),
                ('state', 'not in', ['closed', 'cancelled', 'resolved'])
            ],
            'context': {'default_sla_policy_id': self.id},
        }
        return action

    # ==================== Policy Matching Logic ====================
    @api.model
    def _find_matching_policy(self, ticket):
        """Find matching SLA policy for a ticket"""
        # Search for active policies
        # Note: We can't search on computed fields (priority_all, category_all, etc.)
        # So we search broadly and filter using _matches_ticket
        domain = [('active', '=', True)]
        
        # Build domain based on ticket attributes
        priority_domain = []
        
        if ticket.priority:
            # Match policies with this priority OR policies with no priority selection (all priorities)
            priority_domain = [
                '|',
                ('priority_selection', '=', False),
                ('priority_selection', '=', ticket.priority)
            ]
            domain += priority_domain
        
        # For Many2many fields (category_ids, ticket_type_ids, team_ids),
        # we can't easily search for empty in domain, so we search for all active policies
        # and let _matches_ticket filter them properly
        
        # Find matching policies, ordered by sequence (lower = higher priority)
        policies = self.search(domain, order='sequence')
        
        # Filter policies to ensure they actually match
        # This handles Many2many empty checks and computed field logic
        for policy in policies:
            if policy._matches_ticket(ticket):
                return policy
        
        return False

    def _matches_ticket(self, ticket):
        """Check if this policy matches a ticket"""
        self.ensure_one()
        
        # Check priority
        if not self.priority_all:
            if not ticket.priority or ticket.priority != self.priority_selection:
                return False
        
        # Check category
        if not self.category_all:
            if not ticket.category_id or ticket.category_id not in self.category_ids:
                return False
        
        # Check ticket type
        if not self.ticket_type_all:
            if not ticket.ticket_type_id or ticket.ticket_type_id not in self.ticket_type_ids:
                return False
        
        # Check team
        if not self.team_all:
            if not ticket.team_id or ticket.team_id not in self.team_ids:
                return False
        
        return True

    # ==================== Constraints ====================
    @api.constrains('response_time', 'resolution_time')
    def _check_sla_times(self):
        """Validate SLA times are positive"""
        for record in self:
            if record.response_time <= 0:
                raise ValidationError(_('Response time must be greater than 0.'))
            if record.resolution_time <= 0:
                raise ValidationError(_('Resolution time must be greater than 0.'))
            if record.resolution_time < record.response_time:
                raise ValidationError(_('Resolution time must be greater than or equal to response time.'))

    @api.constrains('response_warning_threshold', 'response_escalation_threshold',
                    'resolution_warning_threshold', 'resolution_escalation_threshold')
    def _check_thresholds(self):
        """Validate threshold percentages"""
        for record in self:
            for threshold in ['response_warning_threshold', 'response_escalation_threshold',
                            'resolution_warning_threshold', 'resolution_escalation_threshold']:
                value = getattr(record, threshold)
                if value < 0 or value > 100:
                    raise ValidationError(_('Threshold percentages must be between 0 and 100.'))
            
            if record.response_warning_threshold >= record.response_escalation_threshold:
                raise ValidationError(_('Response warning threshold must be less than escalation threshold.'))
            if record.resolution_warning_threshold >= record.resolution_escalation_threshold:
                raise ValidationError(_('Resolution warning threshold must be less than escalation threshold.'))

    @api.constrains('working_hours', 'working_hours_id')
    def _check_working_hours(self):
        """Validate working hours configuration"""
        for record in self:
            if record.working_hours and not record.working_hours_id:
                raise ValidationError(_('Working hours calendar is required when "Use Working Hours" is enabled.'))
