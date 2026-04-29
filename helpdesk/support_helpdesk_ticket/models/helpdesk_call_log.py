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
from datetime import datetime, timedelta


class HelpdeskCallLog(models.Model):
    _name = 'helpdesk.call.log'
    _description = 'Helpdesk Call Log'
    _order = 'call_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # ==================== Basic Fields ====================
    name = fields.Char(
        string='Call Reference',
        readonly=True,
        copy=False,
        default=lambda self: _('New'),
        help='Unique reference for the call log'
    )
    call_date = fields.Datetime(
        string='Call Date & Time',
        default=fields.Datetime.now,
        required=True,
        tracking=True,
        help='Date and time when the call started'
    )
    call_end_date = fields.Datetime(
        string='Call End Time',
        tracking=True,
        help='Date and time when the call ended'
    )
    duration = fields.Float(
        string='Duration (minutes)',
        compute='_compute_duration',
        store=True,
        help='Call duration in minutes'
    )
    duration_display = fields.Char(
        string='Duration',
        compute='_compute_duration_display',
        help='Human-readable duration display'
    )

    # ==================== Call Information ====================
    direction = fields.Selection(
        [
            ('inbound', 'Inbound'),
            ('outbound', 'Outbound'),
        ],
        string='Direction',
        required=True,
        default='inbound',
        tracking=True,
        help='Call direction'
    )
    phone_number = fields.Char(
        string='Phone Number',
        required=True,
        tracking=True,
        help='Phone number of the caller or called party'
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Contact',
        tracking=True,
        index=True,
        help='Contact associated with this call'
    )
    contact_name = fields.Char(
        string='Contact Name',
        help='Name of the person called or calling'
    )

    # ==================== Ticket Relationship ====================
    ticket_id = fields.Many2one(
        'helpdesk.ticket',
        string='Related Ticket',
        tracking=True,
        index=True,
        ondelete='set null',
        help='Ticket created from or linked to this call'
    )
    ticket_number = fields.Char(
        string='Ticket Number',
        related='ticket_id.ticket_number',
        readonly=True,
        store=True,
        help='Related ticket number'
    )

    # ==================== Call Details ====================
    subject = fields.Char(
        string='Subject',
        help='Brief summary of the call'
    )
    description = fields.Html(
        string='Call Notes',
        help='Detailed notes about the call'
    )
    call_outcome = fields.Selection(
        [
            ('resolved', 'Resolved'),
            ('escalated', 'Escalated'),
            ('follow_up', 'Follow-up Required'),
            ('no_answer', 'No Answer'),
            ('busy', 'Busy'),
            ('voicemail', 'Voicemail'),
            ('missed', 'Missed Call'),
            ('other', 'Other'),
        ],
        string='Call Outcome',
        tracking=True,
        help='Outcome or result of the call'
    )
    resolution_summary = fields.Text(
        string='Resolution Summary',
        help='Summary of how the issue was resolved (if applicable)'
    )

    # ==================== Agent Information ====================
    agent_id = fields.Many2one(
        'res.users',
        string='Agent',
        default=lambda self: self.env.user,
        required=True,
        tracking=True,
        index=True,
        help='Agent who handled the call'
    )
    team_id = fields.Many2one(
        'helpdesk.team',
        string='Team',
        compute='_compute_team_id',
        store=False,
        help='Team of the agent handling the call'
    )

    @api.depends('agent_id')
    def _compute_team_id(self):
        """Compute team from agent (if agent belongs to a helpdesk team)"""
        for record in self:
            if record.agent_id:
                # Try to find team from user's groups or from tickets
                team = self.env['helpdesk.team'].search([
                    ('member_ids', 'in', [record.agent_id.id])
                ], limit=1)
                record.team_id = team.id if team else False
            else:
                record.team_id = False

    # ==================== Status ====================
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('in_progress', 'In Progress'),
            ('completed', 'Completed'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
        help='Status of the call log'
    )

    # ==================== Computed Fields ====================
    is_long_call = fields.Boolean(
        string='Long Call',
        compute='_compute_is_long_call',
        help='True if call duration exceeds 30 minutes'
    )

    @api.depends('call_date', 'call_end_date')
    def _compute_duration(self):
        """Compute call duration in minutes"""
        for record in self:
            if record.call_date and record.call_end_date:
                if record.call_end_date > record.call_date:
                    delta = record.call_end_date - record.call_date
                    record.duration = delta.total_seconds() / 60.0
                else:
                    record.duration = 0.0
            else:
                record.duration = 0.0

    @api.depends('duration')
    def _compute_duration_display(self):
        """Compute human-readable duration"""
        for record in self:
            if record.duration:
                hours = int(record.duration // 60)
                minutes = int(record.duration % 60)
                if hours > 0:
                    record.duration_display = '%d h %d m' % (hours, minutes)
                else:
                    record.duration_display = '%d m' % minutes
            else:
                record.duration_display = '0 m'

    @api.depends('duration')
    def _compute_is_long_call(self):
        """Mark calls longer than 30 minutes"""
        for record in self:
            record.is_long_call = record.duration > 30.0

    @api.model_create_multi
    def create(self, vals_list):
        """Generate call reference number (batch-friendly)"""
        # Ensure we always work with a list for batch creates
        if not isinstance(vals_list, list):
            vals_list = [vals_list]

        sequence_model = self.env['ir.sequence']

        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                if 'company_id' in vals:
                    vals['name'] = sequence_model.with_company(vals['company_id']).next_by_code('helpdesk.call.log') or _('New')
                else:
                    vals['name'] = sequence_model.next_by_code('helpdesk.call.log') or _('New')

        records = super(HelpdeskCallLog, self).create(vals_list)
        return records

    def action_start_call(self):
        """Mark call as in progress"""
        self.write({
            'state': 'in_progress',
            'call_date': fields.Datetime.now(),
        })

    def action_end_call(self):
        """End the call and compute duration"""
        self.write({
            'state': 'completed',
            'call_end_date': fields.Datetime.now(),
        })

    def action_create_ticket(self):
        """Create a ticket from this call log"""
        self.ensure_one()
        # Create wizard or direct action
        action = {
            'name': _('Create Ticket from Call'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.call.log.create.ticket.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_call_log_id': self.id,
                'default_phone_number': self.phone_number,
                'default_partner_id': self.partner_id.id if self.partner_id else False,
            },
        }
        return action

    def action_link_ticket(self):
        """Link this call to an existing ticket"""
        self.ensure_one()
        action = {
            'name': _('Link Ticket'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket',
            'view_mode': 'tree,form',
            'domain': [('partner_id', '=', self.partner_id.id)] if self.partner_id else [],
            'context': {
                'default_partner_id': self.partner_id.id if self.partner_id else False,
                'default_channel_id': self.env['helpdesk.channel'].search([('code', '=', 'phone')], limit=1).id or False,
                'default_phone_number': self.phone_number,
                'default_call_log_id': self.id,
            },
            'target': 'current',
        }
        return action

    @api.constrains('call_date', 'call_end_date')
    def _check_call_dates(self):
        """Validate call dates"""
        for record in self:
            if record.call_end_date and record.call_date:
                if record.call_end_date < record.call_date:
                    raise ValidationError(_('Call end date cannot be before call start date.'))

    @api.onchange('phone_number')
    def _onchange_phone_number(self):
        """Try to find partner by phone number"""
        if self.phone_number:
            partner = self.env['res.partner'].search([
                '|',
                ('phone', '=', self.phone_number),
                ('mobile', '=', self.phone_number)
            ], limit=1)
            if partner:
                self.partner_id = partner
                self.contact_name = partner.name

    def action_view_ticket(self):
        """Open the related ticket"""
        self.ensure_one()
        if not self.ticket_id:
            return False
        action = {
            'name': _('Ticket'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket',
            'view_mode': 'form',
            'res_id': self.ticket_id.id,
            'target': 'current',
        }
        return action
