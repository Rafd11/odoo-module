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

from odoo import http, fields
from odoo.http import request
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta


class HelpdeskDashboardController(http.Controller):
    """Controller for Helpdesk Dashboard"""
    
    @http.route('/helpdesk/dashboard/kpis', type='jsonrpc', auth='user', methods=['POST'], csrf=False)
    def get_kpis(self, date_from=None, date_to=None, team_id=None, state=None, **kwargs):
        """Get KPI data for dashboard"""
        try:
            domain = []
            
            # Date filters
            if date_from:
                domain.append(('create_date', '>=', date_from))
            if date_to:
                domain.append(('create_date', '<=', date_to))
            if team_id:
                domain.append(('team_id', '=', int(team_id)))
            if state:
                domain.append(('state', '=', state))
            
            tickets = request.env['helpdesk.ticket'].search(domain)
            user = request.env.user
            
            # Calculate KPIs
            total_tickets = len(tickets)
            
            # My tickets count
            my_tickets = len(tickets.filtered(lambda t: t.user_id.id == user.id and t.state not in ['closed', 'cancelled']))
            
            # Unassigned tickets count
            unassigned = len(tickets.filtered(lambda t: not t.user_id and t.state not in ['closed', 'cancelled']))
            
            # SLA at risk count
            sla_at_risk = len(tickets.filtered(lambda t: t.sla_response_status in ['at_risk', 'breached'] and t.state not in ['closed', 'cancelled']))
            
            # Today's tickets count
            today = fields.Datetime.now().replace(hour=0, minute=0, second=0)
            tomorrow = today + timedelta(days=1)
            today_tickets = len(tickets.filtered(lambda t: t.create_date >= today and t.create_date < tomorrow))
            
            # State counts
            state_counts = {}
            ticket_model = request.env['helpdesk.ticket']
            if 'state' in ticket_model._fields:
                state_selection = ticket_model._fields['state'].selection
                if state_selection:
                    for state_value, state_label in state_selection:
                        count = len(tickets.filtered(lambda t: t.state == state_value))
                        if count > 0:
                            state_counts[state_value] = {
                                'label': state_label,
                                'count': count
                            }
            
            # Priority counts
            priority_counts = {}
            if 'priority' in ticket_model._fields:
                priority_selection = ticket_model._fields['priority'].selection
                if priority_selection:
                    for priority_value, priority_label in priority_selection:
                        count = len(tickets.filtered(lambda t: t.priority == priority_value))
                        if count > 0:
                            priority_counts[priority_value] = {
                                'label': priority_label,
                                'count': count
                            }
            
            # Overdue tickets
            overdue_count = len(tickets.filtered(lambda t: t.is_overdue))
            
            # Resolved today
            resolved_today = len(tickets.filtered(lambda t: t.state == 'resolved' and t.resolved_date and t.resolved_date >= today and t.resolved_date < tomorrow))
            
            # Reminder statistics
            reminders = request.env['helpdesk.reminder'].search([])
            total_reminders = len(reminders)
            pending_reminders = len(reminders.filtered(lambda r: r.status == 'pending'))
            sent_reminders = len(reminders.filtered(lambda r: r.status == 'sent'))
            
            # Upcoming reminders (next 7 days)
            next_week = today + timedelta(days=7)
            upcoming_reminders = len(reminders.filtered(
                lambda r: r.status == 'pending' and r.reminder_date and 
                r.reminder_date >= fields.Datetime.now() and 
                r.reminder_date <= next_week
            ))
            
            return {
                'success': True,
                'kpis': {
                    'total_tickets': total_tickets,
                    'my_tickets': my_tickets,
                    'unassigned': unassigned,
                    'sla_at_risk': sla_at_risk,
                    'today_tickets': today_tickets,
                    'overdue_count': overdue_count,
                    'resolved_today': resolved_today,
                    'total_reminders': total_reminders,
                    'pending_reminders': pending_reminders,
                    'sent_reminders': sent_reminders,
                    'upcoming_reminders': upcoming_reminders,
                    'state_counts': state_counts,
                    'priority_counts': priority_counts,
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/helpdesk/team/dashboard/kpis', type='jsonrpc', auth='user', methods=['POST'], csrf=False)
    def get_team_kpis(self, date_from=None, date_to=None, team_id=None, **kwargs):
        """Get KPI data for team dashboard"""
        try:
            domain = []
            
            # Date filters
            if date_from:
                domain.append(('create_date', '>=', date_from))
            if date_to:
                domain.append(('create_date', '<=', date_to))
            if team_id:
                domain.append(('team_id', '=', int(team_id)))
            
            tickets = request.env['helpdesk.ticket'].search(domain)
            teams = request.env['helpdesk.team'].search([])
            
            # Calculate Team KPIs
            total_teams = len(teams)
            active_teams = len(teams.filtered(lambda t: t.active))
            
            # Team ticket statistics
            team_tickets = tickets.filtered(lambda t: t.team_id)
            total_team_tickets = len(team_tickets)
            open_team_tickets = len(team_tickets.filtered(lambda t: t.state not in ['closed', 'cancelled']))
            
            # Team performance metrics
            team_performance = []
            for team in teams:
                team_ticket_list = tickets.filtered(lambda t: t.team_id.id == team.id)
                resolved_tickets = team_ticket_list.filtered(lambda t: t.state in ['resolved', 'closed'])
                
                team_performance.append({
                    'team_id': team.id,
                    'team_name': team.name,
                    'total_tickets': len(team_ticket_list),
                    'open_tickets': len(team_ticket_list.filtered(lambda t: t.state not in ['closed', 'cancelled'])),
                    'resolved_tickets': len(resolved_tickets),
                    'team_leader': team.team_leader_id.name if team.team_leader_id else 'N/A',
                    'member_count': len(team.member_ids),
                })
            
            # Today's team tickets
            today = fields.Datetime.now().replace(hour=0, minute=0, second=0)
            tomorrow = today + timedelta(days=1)
            today_team_tickets = len(tickets.filtered(lambda t: t.team_id and t.create_date >= today and t.create_date < tomorrow))
            
            # Team SLA metrics
            team_sla_at_risk = len(team_tickets.filtered(lambda t: t.sla_response_status in ['at_risk', 'breached'] and t.state not in ['closed', 'cancelled']))
            
            return {
                'success': True,
                'kpis': {
                    'total_teams': total_teams,
                    'active_teams': active_teams,
                    'total_team_tickets': total_team_tickets,
                    'open_team_tickets': open_team_tickets,
                    'today_team_tickets': today_team_tickets,
                    'team_sla_at_risk': team_sla_at_risk,
                    'team_performance': team_performance,
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/helpdesk/dashboard/teams', type='jsonrpc', auth='user', methods=['POST'], csrf=False)
    def get_teams(self, **kwargs):
        """Get list of teams for filter"""
        try:
            teams = request.env['helpdesk.team'].search([('active', '=', True)])
            return {
                'success': True,
                'data': [{
                    'id': team.id,
                    'name': team.name
                } for team in teams]
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/helpdesk/team/dashboard/kpis', type='jsonrpc', auth='user', methods=['POST'], csrf=False)
    def get_team_kpis(self, date_from=None, date_to=None, team_id=None, **kwargs):
        """Get KPI data for team dashboard"""
        try:
            domain = []
            
            # Date filters
            if date_from:
                domain.append(('create_date', '>=', date_from))
            if date_to:
                domain.append(('create_date', '<=', date_to))
            if team_id:
                domain.append(('team_id', '=', int(team_id)))
            
            tickets = request.env['helpdesk.ticket'].search(domain)
            teams = request.env['helpdesk.team'].search([])
            
            # Calculate Team KPIs
            total_teams = len(teams)
            active_teams = len(teams.filtered(lambda t: t.active))
            
            # Team ticket statistics
            team_tickets = tickets.filtered(lambda t: t.team_id)
            total_team_tickets = len(team_tickets)
            open_team_tickets = len(team_tickets.filtered(lambda t: t.state not in ['closed', 'cancelled']))
            
            # Team performance metrics
            team_performance = []
            for team in teams:
                team_ticket_list = tickets.filtered(lambda t: t.team_id.id == team.id)
                resolved_tickets = team_ticket_list.filtered(lambda t: t.state in ['resolved', 'closed'])
                
                team_performance.append({
                    'team_id': team.id,
                    'team_name': team.name,
                    'total_tickets': len(team_ticket_list),
                    'open_tickets': len(team_ticket_list.filtered(lambda t: t.state not in ['closed', 'cancelled'])),
                    'resolved_tickets': len(resolved_tickets),
                    'team_leader': team.team_leader_id.name if team.team_leader_id else 'N/A',
                    'member_count': len(team.member_ids),
                })
            
            # Today's team tickets
            today = fields.Datetime.now().replace(hour=0, minute=0, second=0)
            tomorrow = today + timedelta(days=1)
            today_team_tickets = len(tickets.filtered(lambda t: t.team_id and t.create_date >= today and t.create_date < tomorrow))
            
            # Team SLA metrics
            team_sla_at_risk = len(team_tickets.filtered(lambda t: t.sla_response_status in ['at_risk', 'breached'] and t.state not in ['closed', 'cancelled']))
            
            return {
                'success': True,
                'kpis': {
                    'total_teams': total_teams,
                    'active_teams': active_teams,
                    'total_team_tickets': total_team_tickets,
                    'open_team_tickets': open_team_tickets,
                    'today_team_tickets': today_team_tickets,
                    'team_sla_at_risk': team_sla_at_risk,
                    'team_performance': team_performance,
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/helpdesk/dashboard/ticket-trend', type='jsonrpc', auth='user', methods=['POST'], csrf=False)
    def get_ticket_trend(self, months=12, team_id=None, state=None, **kwargs):
        """Get ticket creation trend data for chart"""
        try:
            domain = []
            if team_id:
                domain.append(('team_id', '=', int(team_id)))
            if state:
                domain.append(('state', '=', state))
            
            tickets = request.env['helpdesk.ticket'].search(domain)
            
            # Get tickets created in the last N months
            today = datetime.today().date()
            date_from = today - relativedelta(months=months)
            
            # Filter tickets by create_date
            recent_tickets = tickets.filtered(
                lambda t: t.create_date and t.create_date.date() >= date_from
            )
            
            # Group by month
            monthly_data = {}
            for ticket in recent_tickets:
                if ticket.create_date:
                    month_key = ticket.create_date.strftime('%Y-%m')
                    if month_key not in monthly_data:
                        monthly_data[month_key] = 0
                    monthly_data[month_key] += 1
            
            # Format for chart
            labels = sorted(monthly_data.keys())
            values = [monthly_data[label] for label in labels]
            
            return {
                'success': True,
                'data': {
                    'labels': labels,
                    'values': values
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/helpdesk/team/dashboard/kpis', type='jsonrpc', auth='user', methods=['POST'], csrf=False)
    def get_team_kpis(self, date_from=None, date_to=None, team_id=None, **kwargs):
        """Get KPI data for team dashboard"""
        try:
            domain = []
            
            # Date filters
            if date_from:
                domain.append(('create_date', '>=', date_from))
            if date_to:
                domain.append(('create_date', '<=', date_to))
            if team_id:
                domain.append(('team_id', '=', int(team_id)))
            
            tickets = request.env['helpdesk.ticket'].search(domain)
            teams = request.env['helpdesk.team'].search([])
            
            # Calculate Team KPIs
            total_teams = len(teams)
            active_teams = len(teams.filtered(lambda t: t.active))
            
            # Team ticket statistics
            team_tickets = tickets.filtered(lambda t: t.team_id)
            total_team_tickets = len(team_tickets)
            open_team_tickets = len(team_tickets.filtered(lambda t: t.state not in ['closed', 'cancelled']))
            
            # Team performance metrics
            team_performance = []
            for team in teams:
                team_ticket_list = tickets.filtered(lambda t: t.team_id.id == team.id)
                resolved_tickets = team_ticket_list.filtered(lambda t: t.state in ['resolved', 'closed'])
                
                team_performance.append({
                    'team_id': team.id,
                    'team_name': team.name,
                    'total_tickets': len(team_ticket_list),
                    'open_tickets': len(team_ticket_list.filtered(lambda t: t.state not in ['closed', 'cancelled'])),
                    'resolved_tickets': len(resolved_tickets),
                    'team_leader': team.team_leader_id.name if team.team_leader_id else 'N/A',
                    'member_count': len(team.member_ids),
                })
            
            # Today's team tickets
            today = fields.Datetime.now().replace(hour=0, minute=0, second=0)
            tomorrow = today + timedelta(days=1)
            today_team_tickets = len(tickets.filtered(lambda t: t.team_id and t.create_date >= today and t.create_date < tomorrow))
            
            # Team SLA metrics
            team_sla_at_risk = len(team_tickets.filtered(lambda t: t.sla_response_status in ['at_risk', 'breached'] and t.state not in ['closed', 'cancelled']))
            
            return {
                'success': True,
                'kpis': {
                    'total_teams': total_teams,
                    'active_teams': active_teams,
                    'total_team_tickets': total_team_tickets,
                    'open_team_tickets': open_team_tickets,
                    'today_team_tickets': today_team_tickets,
                    'team_sla_at_risk': team_sla_at_risk,
                    'team_performance': team_performance,
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/helpdesk/dashboard/state-distribution', type='jsonrpc', auth='user', methods=['POST'], csrf=False)
    def get_state_distribution(self, team_id=None, **kwargs):
        """Get ticket state distribution data for chart"""
        try:
            domain = []
            if team_id:
                domain.append(('team_id', '=', int(team_id)))
            
            tickets = request.env['helpdesk.ticket'].search(domain)
            
            # Group by state
            state_data = {}
            ticket_model = request.env['helpdesk.ticket']
            if 'state' in ticket_model._fields:
                state_selection = ticket_model._fields['state'].selection
                if state_selection:
                    for state_value, state_label in state_selection:
                        count = len(tickets.filtered(lambda t: t.state == state_value))
                        if count > 0:
                            state_data[state_label] = count
            
            # Format for chart
            labels = list(state_data.keys())
            values = list(state_data.values())
            
            return {
                'success': True,
                'data': {
                    'labels': labels,
                    'values': values
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/helpdesk/team/dashboard/kpis', type='jsonrpc', auth='user', methods=['POST'], csrf=False)
    def get_team_kpis(self, date_from=None, date_to=None, team_id=None, **kwargs):
        """Get KPI data for team dashboard"""
        try:
            domain = []
            
            # Date filters
            if date_from:
                domain.append(('create_date', '>=', date_from))
            if date_to:
                domain.append(('create_date', '<=', date_to))
            if team_id:
                domain.append(('team_id', '=', int(team_id)))
            
            tickets = request.env['helpdesk.ticket'].search(domain)
            teams = request.env['helpdesk.team'].search([])
            
            # Calculate Team KPIs
            total_teams = len(teams)
            active_teams = len(teams.filtered(lambda t: t.active))
            
            # Team ticket statistics
            team_tickets = tickets.filtered(lambda t: t.team_id)
            total_team_tickets = len(team_tickets)
            open_team_tickets = len(team_tickets.filtered(lambda t: t.state not in ['closed', 'cancelled']))
            
            # Team performance metrics
            team_performance = []
            for team in teams:
                team_ticket_list = tickets.filtered(lambda t: t.team_id.id == team.id)
                resolved_tickets = team_ticket_list.filtered(lambda t: t.state in ['resolved', 'closed'])
                
                team_performance.append({
                    'team_id': team.id,
                    'team_name': team.name,
                    'total_tickets': len(team_ticket_list),
                    'open_tickets': len(team_ticket_list.filtered(lambda t: t.state not in ['closed', 'cancelled'])),
                    'resolved_tickets': len(resolved_tickets),
                    'team_leader': team.team_leader_id.name if team.team_leader_id else 'N/A',
                    'member_count': len(team.member_ids),
                })
            
            # Today's team tickets
            today = fields.Datetime.now().replace(hour=0, minute=0, second=0)
            tomorrow = today + timedelta(days=1)
            today_team_tickets = len(tickets.filtered(lambda t: t.team_id and t.create_date >= today and t.create_date < tomorrow))
            
            # Team SLA metrics
            team_sla_at_risk = len(team_tickets.filtered(lambda t: t.sla_response_status in ['at_risk', 'breached'] and t.state not in ['closed', 'cancelled']))
            
            return {
                'success': True,
                'kpis': {
                    'total_teams': total_teams,
                    'active_teams': active_teams,
                    'total_team_tickets': total_team_tickets,
                    'open_team_tickets': open_team_tickets,
                    'today_team_tickets': today_team_tickets,
                    'team_sla_at_risk': team_sla_at_risk,
                    'team_performance': team_performance,
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/helpdesk/dashboard/priority-distribution', type='jsonrpc', auth='user', methods=['POST'], csrf=False)
    def get_priority_distribution(self, team_id=None, **kwargs):
        """Get ticket priority distribution data for chart"""
        try:
            domain = []
            if team_id:
                domain.append(('team_id', '=', int(team_id)))
            
            tickets = request.env['helpdesk.ticket'].search(domain)
            
            # Group by priority
            priority_data = {}
            ticket_model = request.env['helpdesk.ticket']
            if 'priority' in ticket_model._fields:
                priority_selection = ticket_model._fields['priority'].selection
                if priority_selection:
                    for priority_value, priority_label in priority_selection:
                        count = len(tickets.filtered(lambda t: t.priority == priority_value))
                        if count > 0:
                            priority_data[priority_label] = count
            
            # Format for chart
            labels = list(priority_data.keys())
            values = list(priority_data.values())
            
            return {
                'success': True,
                'data': {
                    'labels': labels,
                    'values': values
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/helpdesk/team/dashboard/kpis', type='jsonrpc', auth='user', methods=['POST'], csrf=False)
    def get_team_kpis(self, date_from=None, date_to=None, team_id=None, **kwargs):
        """Get KPI data for team dashboard"""
        try:
            domain = []
            
            # Date filters
            if date_from:
                domain.append(('create_date', '>=', date_from))
            if date_to:
                domain.append(('create_date', '<=', date_to))
            if team_id:
                domain.append(('team_id', '=', int(team_id)))
            
            tickets = request.env['helpdesk.ticket'].search(domain)
            teams = request.env['helpdesk.team'].search([])
            
            # Calculate Team KPIs
            total_teams = len(teams)
            active_teams = len(teams.filtered(lambda t: t.active))
            
            # Team ticket statistics
            team_tickets = tickets.filtered(lambda t: t.team_id)
            total_team_tickets = len(team_tickets)
            open_team_tickets = len(team_tickets.filtered(lambda t: t.state not in ['closed', 'cancelled']))
            
            # Team performance metrics
            team_performance = []
            for team in teams:
                team_ticket_list = tickets.filtered(lambda t: t.team_id.id == team.id)
                resolved_tickets = team_ticket_list.filtered(lambda t: t.state in ['resolved', 'closed'])
                
                team_performance.append({
                    'team_id': team.id,
                    'team_name': team.name,
                    'total_tickets': len(team_ticket_list),
                    'open_tickets': len(team_ticket_list.filtered(lambda t: t.state not in ['closed', 'cancelled'])),
                    'resolved_tickets': len(resolved_tickets),
                    'team_leader': team.team_leader_id.name if team.team_leader_id else 'N/A',
                    'member_count': len(team.member_ids),
                })
            
            # Today's team tickets
            today = fields.Datetime.now().replace(hour=0, minute=0, second=0)
            tomorrow = today + timedelta(days=1)
            today_team_tickets = len(tickets.filtered(lambda t: t.team_id and t.create_date >= today and t.create_date < tomorrow))
            
            # Team SLA metrics
            team_sla_at_risk = len(team_tickets.filtered(lambda t: t.sla_response_status in ['at_risk', 'breached'] and t.state not in ['closed', 'cancelled']))
            
            return {
                'success': True,
                'kpis': {
                    'total_teams': total_teams,
                    'active_teams': active_teams,
                    'total_team_tickets': total_team_tickets,
                    'open_team_tickets': open_team_tickets,
                    'today_team_tickets': today_team_tickets,
                    'team_sla_at_risk': team_sla_at_risk,
                    'team_performance': team_performance,
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/helpdesk/dashboard/sla-status', type='jsonrpc', auth='user', methods=['POST'], csrf=False)
    def get_sla_status(self, team_id=None, **kwargs):
        """Get SLA status distribution data for chart"""
        try:
            domain = []
            if team_id:
                domain.append(('team_id', '=', int(team_id)))
            
            tickets = request.env['helpdesk.ticket'].search(domain)
            
            # Group by SLA status
            sla_data = {
                'met': 0,
                'at_risk': 0,
                'breached': 0,
                'no_sla': 0
            }
            
            for ticket in tickets:
                if ticket.sla_response_status == 'met':
                    sla_data['met'] += 1
                elif ticket.sla_response_status == 'at_risk':
                    sla_data['at_risk'] += 1
                elif ticket.sla_response_status == 'breached':
                    sla_data['breached'] += 1
                else:
                    sla_data['no_sla'] += 1
            
            # Format for chart
            labels = ['SLA Met', 'At Risk', 'Breached', 'No SLA']
            values = [sla_data['met'], sla_data['at_risk'], sla_data['breached'], sla_data['no_sla']]
            
            return {
                'success': True,
                'data': {
                    'labels': labels,
                    'values': values
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    @http.route('/helpdesk/team/dashboard/kpis', type='jsonrpc', auth='user', methods=['POST'], csrf=False)
    def get_team_kpis(self, date_from=None, date_to=None, team_id=None, **kwargs):
        """Get KPI data for team dashboard"""
        try:
            domain = []
            
            # Date filters
            if date_from:
                domain.append(('create_date', '>=', date_from))
            if date_to:
                domain.append(('create_date', '<=', date_to))
            if team_id:
                domain.append(('team_id', '=', int(team_id)))
            
            tickets = request.env['helpdesk.ticket'].search(domain)
            teams = request.env['helpdesk.team'].search([])
            
            # Calculate Team KPIs
            total_teams = len(teams)
            active_teams = len(teams.filtered(lambda t: t.active))
            
            # Team ticket statistics
            team_tickets = tickets.filtered(lambda t: t.team_id)
            total_team_tickets = len(team_tickets)
            open_team_tickets = len(team_tickets.filtered(lambda t: t.state not in ['closed', 'cancelled']))
            
            # Team performance metrics
            team_performance = []
            for team in teams:
                team_ticket_list = tickets.filtered(lambda t: t.team_id.id == team.id)
                resolved_tickets = team_ticket_list.filtered(lambda t: t.state in ['resolved', 'closed'])
                
                team_performance.append({
                    'team_id': team.id,
                    'team_name': team.name,
                    'total_tickets': len(team_ticket_list),
                    'open_tickets': len(team_ticket_list.filtered(lambda t: t.state not in ['closed', 'cancelled'])),
                    'resolved_tickets': len(resolved_tickets),
                    'team_leader': team.team_leader_id.name if team.team_leader_id else 'N/A',
                    'member_count': len(team.member_ids),
                })
            
            # Today's team tickets
            today = fields.Datetime.now().replace(hour=0, minute=0, second=0)
            tomorrow = today + timedelta(days=1)
            today_team_tickets = len(tickets.filtered(lambda t: t.team_id and t.create_date >= today and t.create_date < tomorrow))
            
            # Team SLA metrics
            team_sla_at_risk = len(team_tickets.filtered(lambda t: t.sla_response_status in ['at_risk', 'breached'] and t.state not in ['closed', 'cancelled']))
            
            return {
                'success': True,
                'kpis': {
                    'total_teams': total_teams,
                    'active_teams': active_teams,
                    'total_team_tickets': total_team_tickets,
                    'open_team_tickets': open_team_tickets,
                    'today_team_tickets': today_team_tickets,
                    'team_sla_at_risk': team_sla_at_risk,
                    'team_performance': team_performance,
                }
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }