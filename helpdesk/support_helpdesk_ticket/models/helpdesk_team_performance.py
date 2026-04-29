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
from datetime import datetime, timedelta


class HelpdeskTeamPerformance(models.TransientModel):
    _name = 'helpdesk.team.performance'
    _description = 'Helpdesk Team Performance Dashboard'

    # Date range filters
    date_from = fields.Date(
        string='From',
        help='Start date for performance calculation'
    )
    date_to = fields.Date(
        string='To',
        help='End date for performance calculation'
    )

    # Optional team filter
    team_id = fields.Many2one(
        'helpdesk.team',
        string='Team',
        help='Restrict metrics to a specific team'
    )

    # Aggregated metrics
    tickets_handled = fields.Integer(
        string='Tickets Handled',
        compute='_compute_metrics',
        help='Number of tickets resolved or closed in the selected period'
    )
    avg_resolution_time = fields.Float(
        string='Avg. Resolution Time (Days)',
        compute='_compute_metrics',
        help='Average number of days to resolve tickets in the selected period'
    )
    sla_compliance_rate = fields.Float(
        string='SLA Compliance (%)',
        compute='_compute_metrics',
        help='Percentage of tickets that met SLA resolution in the selected period'
    )
    customer_satisfaction = fields.Float(
        string='Customer Satisfaction (Avg Rating)',
        compute='_compute_metrics',
        help='Average customer satisfaction rating for tickets in the selected period'
    )
    first_response_time = fields.Float(
        string='First Response Time (Placeholder)',
        help='Placeholder for first response time metric'
    )

    @api.depends('date_from', 'date_to', 'team_id')
    def _compute_metrics(self):
        """Compute aggregated performance metrics for the selected period and team."""
        Ticket = self.env['helpdesk.ticket']
        for record in self:
            domain = []

            # Filter by resolution date within range if provided
            if record.date_from:
                domain.append(('resolved_date', '>=', fields.Datetime.to_datetime(record.date_from)))
            if record.date_to:
                # include the whole day
                dt_to = datetime.combine(record.date_to, datetime.max.time())
                domain.append(('resolved_date', '<=', dt_to))

            # Restrict to selected team if set
            if record.team_id:
                domain.append(('team_id', '=', record.team_id.id))

            # Only consider tickets that have been resolved/closed
            domain.append(('state', 'in', ['resolved', 'closed']))

            tickets = Ticket.search(domain)
            tickets_handled = len(tickets)

            # Average resolution time in days
            total_resolution_days = sum(t.days_to_resolve or 0 for t in tickets)
            avg_resolution_time = tickets_handled and (total_resolution_days / tickets_handled) or 0.0

            # SLA compliance rate (based on resolution SLA status)
            met_tickets = tickets.filtered(lambda t: t.sla_resolution_status == 'met')
            sla_compliance_rate = tickets_handled and (len(met_tickets) * 100.0 / tickets_handled) or 0.0

            # Customer satisfaction (average rating where rating is set)
            rated = tickets.filtered(lambda t: t.rating not in (False, None))
            total_rating = sum(float(t.rating or 0) for t in rated)
            customer_satisfaction = rated and (total_rating / len(rated)) or 0.0

            record.tickets_handled = tickets_handled
            record.avg_resolution_time = avg_resolution_time
            record.sla_compliance_rate = sla_compliance_rate
            record.customer_satisfaction = customer_satisfaction

