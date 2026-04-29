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


class HelpdeskTeam(models.Model):
    _name = 'helpdesk.team'
    _description = 'Helpdesk Team'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Team Name',
        required=True,
        tracking=True,
        help='Name of the helpdesk team'
    )
    description = fields.Text(
        string='Description',
        help='Description of the team'
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help='If unchecked, this team will be hidden'
    )
    
    # Sequence Configuration
    sequence_id = fields.Many2one(
        'ir.sequence',
        string='Ticket Sequence',
        help='Sequence for generating ticket numbers for this team. If not set, default sequence will be used.'
    )
    sequence_code = fields.Char(
        string='Sequence Code',
        help='Code of the sequence to use. If sequence_id is not set, this code will be used to find the sequence.'
    )
    
    # Team Members
    member_ids = fields.Many2many(
        'res.users',
        'helpdesk_team_member_rel',
        'team_id',
        'user_id',
        string='Team Members',
        help='Users who are members of this team'
    )
    team_leader_id = fields.Many2one(
        'res.users',
        string='Team Leader',
        help='Leader of the team'
    )
    
    # Assignment Configuration
    default_assignment_algorithm = fields.Selection(
        [
            ('round_robin', 'Round-Robin'),
            ('workload_based', 'Workload-Based'),
            ('skill_based', 'Skill-Based'),
        ],
        string='Default Assignment Algorithm',
        default='round_robin',
        help='Default algorithm to use for automatic ticket assignment to team members'
    )
    auto_assign_enabled = fields.Boolean(
        string='Enable Auto-Assignment',
        default=False,
        help='If enabled, tickets assigned to this team will be automatically assigned to team members using the selected algorithm'
    )
    
    # Ticket Statistics
    ticket_count = fields.Integer(
        string='Ticket Count',
        compute='_compute_ticket_count',
        help='Number of tickets assigned to this team'
    )
    open_ticket_count = fields.Integer(
        string='Open Tickets',
        compute='_compute_ticket_count',
        help='Number of open tickets'
    )
    
    # Email Configuration
    alias_id = fields.Many2one(
        'mail.alias',
        string='Email Alias',
        ondelete='restrict',
        help='Email alias for this team'
    )
    alias_name = fields.Char(
        string='Alias Name',
        related='alias_id.alias_name',
        readonly=True,
        help='Email alias name'
    )

    @api.depends('member_ids')
    def _compute_ticket_count(self):
        """Compute ticket statistics for the team"""
        for team in self:
            tickets = self.env['helpdesk.ticket'].search([
                ('team_id', '=', team.id)
            ])
            team.ticket_count = len(tickets)
            team.open_ticket_count = len(tickets.filtered(
                lambda t: t.state not in ['closed', 'cancelled']
            ))

    def action_view_tickets(self):
        """Open tickets for this team"""
        self.ensure_one()
        return {
            'name': _('Team Tickets'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket',
            'view_mode': 'kanban,tree,form',
            'domain': [('team_id', '=', self.id)],
            'context': {'default_team_id': self.id},
        }

    def _alias_get_creation_values(self):
        """Get values to create email alias for team"""
        # Build alias creation values (no super() call as parent classes don't have this method)
        model = self.env['ir.model']._get_id('helpdesk.ticket')
        values = {
            'alias_model_id': model,
            'alias_force_thread_id': False,
            'alias_parent_model_id': False,
            'alias_parent_thread_id': False,
            # alias_defaults must be a string representation of a dict
            'alias_defaults': str({
                'team_id': self.id,
                'channel': 'email',
            })
        }
        return values
    
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to ensure email alias is created"""
        teams = super(HelpdeskTeam, self).create(vals_list)
        
        # Create alias for each team if not provided
        for team in teams:
            if not team.alias_id:
                # Generate alias name from team name
                alias_name = team.name.lower().replace(' ', '-').replace('_', '-')
                # Remove special characters
                alias_name = ''.join(c for c in alias_name if c.isalnum() or c == '-')
                # Ensure uniqueness
                existing_alias = self.env['mail.alias'].search([
                    ('alias_name', '=', alias_name)
                ], limit=1)
                if existing_alias:
                    alias_name = f"{alias_name}-{team.id}"
                
                # Create alias
                alias_vals = team._alias_get_creation_values()
                alias_vals['alias_name'] = alias_name
                alias_vals['alias_force_thread_id'] = False
                alias_vals['alias_parent_model_id'] = False
                alias_vals['alias_parent_thread_id'] = False
                
                alias = self.env['mail.alias'].create(alias_vals)
                team.alias_id = alias.id
        
        return teams
    
    def write(self, vals):
        """Override write to update alias if team name changes"""
        result = super(HelpdeskTeam, self).write(vals)
        
        # Update alias name if team name changed
        if 'name' in vals and self.alias_id:
            alias_name = vals['name'].lower().replace(' ', '-').replace('_', '-')
            alias_name = ''.join(c for c in alias_name if c.isalnum() or c == '-')
            
            # Check if alias name is already taken
            existing_alias = self.env['mail.alias'].search([
                ('alias_name', '=', alias_name),
                ('id', '!=', self.alias_id.id)
            ], limit=1)
            
            if not existing_alias:
                self.alias_id.alias_name = alias_name
        
        return result