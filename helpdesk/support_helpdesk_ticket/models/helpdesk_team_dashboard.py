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


class HelpdeskTeamDashboard(models.TransientModel):
    """Transient model for Team Dashboard"""
    _name = 'helpdesk.team.dashboard'
    _description = 'Team Dashboard'

    name = fields.Char(
        string='Dashboard',
        default='Team Dashboard',
        readonly=True
    )
    
    # Computed fields to show in form view (for demo purposes)
    total_teams_count = fields.Integer(
        string='Total Teams',
        compute='_compute_dashboard_stats',
        readonly=True
    )
    
    active_teams_count = fields.Integer(
        string='Active Teams',
        compute='_compute_dashboard_stats',
        readonly=True
    )
    
    total_team_tickets_count = fields.Integer(
        string='Team Tickets',
        compute='_compute_dashboard_stats',
        readonly=True
    )
    
    open_team_tickets_count = fields.Integer(
        string='Open Team Tickets',
        compute='_compute_dashboard_stats',
        readonly=True
    )

    @api.depends()
    def _compute_dashboard_stats(self):
        """Compute dashboard statistics"""
        for record in self:
            teams = self.env['helpdesk.team'].search([])
            record.total_teams_count = len(teams)
            record.active_teams_count = len(teams.filtered(lambda t: t.active))
            
            tickets = self.env['helpdesk.ticket'].search([])
            record.total_team_tickets_count = len(tickets.filtered(lambda t: t.team_id))
            record.open_team_tickets_count = len(tickets.filtered(lambda t: t.team_id and t.state not in ['closed', 'cancelled']))

    @api.model
    def default_get(self, fields_list):
        """Create a default dashboard record"""
        res = super(HelpdeskTeamDashboard, self).default_get(fields_list)
        return res

    def dummy(self):
        """Dummy method for button actions that are handled by JavaScript"""
        return True
