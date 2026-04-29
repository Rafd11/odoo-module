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

from odoo import models, fields, api


class HelpdeskDashboard(models.TransientModel):
    """Transient model for Helpdesk Dashboard"""
    _name = 'helpdesk.dashboard'
    _description = 'Helpdesk Dashboard'

    name = fields.Char(
        string='Dashboard',
        default='Helpdesk Dashboard',
        readonly=True
    )
    
    # Computed fields to show in form view (for demo purposes)
    total_tickets_count = fields.Integer(
        string='Total Tickets',
        compute='_compute_dashboard_stats',
        readonly=True
    )
    
    my_tickets_count = fields.Integer(
        string='My Tickets',
        compute='_compute_dashboard_stats',
        readonly=True
    )
    
    unassigned_count = fields.Integer(
        string='Unassigned',
        compute='_compute_dashboard_stats',
        readonly=True
    )
    
    sla_at_risk_count = fields.Integer(
        string='SLA At Risk',
        compute='_compute_dashboard_stats',
        readonly=True
    )
    
    # Filter fields
    filter_date_from = fields.Date(
        string='Date From',
        help='Filter tickets from this date'
    )
    
    filter_date_to = fields.Date(
        string='Date To',
        help='Filter tickets until this date'
    )
    
    filter_team_id = fields.Many2one(
        'helpdesk.team',
        string='Team',
        help='Filter tickets by team'
    )
    
    filter_state = fields.Selection(
        [
            ('new', 'New'),
            ('assigned', 'Assigned'),
            ('in_progress', 'In Progress'),
            ('resolved', 'Resolved'),
            ('closed', 'Closed'),
            ('cancelled', 'Cancelled'),
        ],
        string='State',
        help='Filter tickets by state'
    )

    @api.depends('filter_date_from', 'filter_date_to', 'filter_team_id', 'filter_state')
    def _compute_dashboard_stats(self):
        """Compute dashboard statistics with filters"""
        for record in self:
            # Build domain based on filters
            domain = []
            
            if record.filter_date_from:
                domain.append(('create_date', '>=', record.filter_date_from))
            if record.filter_date_to:
                domain.append(('create_date', '<=', record.filter_date_to))
            if record.filter_team_id:
                domain.append(('team_id', '=', record.filter_team_id.id))
            if record.filter_state:
                domain.append(('state', '=', record.filter_state))
            
            tickets = self.env['helpdesk.ticket'].search(domain)
            record.total_tickets_count = len(tickets)
            record.my_tickets_count = len(tickets.filtered(lambda t: t.user_id.id == self.env.user.id))
            record.unassigned_count = len(tickets.filtered(lambda t: not t.user_id))
            record.sla_at_risk_count = len(tickets.filtered(lambda t: t.sla_response_status in ['at_risk', 'breached'] and t.state not in ['closed', 'cancelled']))

    @api.model
    def default_get(self, fields_list):
        """Create a default dashboard record"""
        res = super(HelpdeskDashboard, self).default_get(fields_list)
        return res

    def dummy(self):
        """Dummy method for button actions that are handled by JavaScript"""
        return True
    
    def action_apply_filters(self):
        """Apply filters - handled by JavaScript, no reload"""
        self.ensure_one()
        # JavaScript handles the filter application via API
        return False
    
    def action_reset_filters(self):
        """Reset all filters - handled by JavaScript, no reload"""
        self.ensure_one()
        # JavaScript handles the reset
        return False
    
    def save_filters(self, date_from=None, date_to=None, team_id=None, state=None):
        """Save filter values to dashboard record"""
        self.ensure_one()
        
        vals = {}
        if date_from:
            vals['filter_date_from'] = date_from
        else:
            vals['filter_date_from'] = False
            
        if date_to:
            vals['filter_date_to'] = date_to
        else:
            vals['filter_date_to'] = False
            
        if team_id:
            vals['filter_team_id'] = int(team_id)
        else:
            vals['filter_team_id'] = False
            
        if state:
            vals['filter_state'] = state
        else:
            vals['filter_state'] = False
        
        self.write(vals)
        
        return {
            'success': True,
            'message': 'Filters saved successfully'
        }
