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
from odoo.exceptions import UserError
from datetime import datetime, timedelta
import logging

_logger = logging.getLogger(__name__)


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # ==================== General Settings ====================
    
    # Default Values
    helpdesk_default_priority = fields.Selection(
        [
            ('0', 'Low'),
            ('1', 'Medium'),
            ('2', 'High'),
            ('3', 'Urgent'),
        ],
        string='Default Priority',
        config_parameter='helpdesk.default_priority',
        default='1',
        help='Default priority for new tickets'
    )
    
    helpdesk_default_state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('new', 'New'),
            ('assigned', 'Assigned'),
        ],
        string='Default State',
        config_parameter='helpdesk.default_state',
        default='new',
        help='Default state for new tickets'
    )
    
    helpdesk_default_channel_id = fields.Many2one(
        'helpdesk.channel',
        string='Default Channel',
        config_parameter='helpdesk.default_channel_id',
        help='Default channel for new tickets'
    )
    
    helpdesk_default_team_id = fields.Many2one(
        'helpdesk.team',
        string='Default Team',
        config_parameter='helpdesk.default_team_id',
        help='Default team for new tickets'
    )
    
    helpdesk_default_category_id = fields.Many2one(
        'helpdesk.category',
        string='Default Category',
        config_parameter='helpdesk.default_category_id',
        help='Default category for new tickets'
    )
    
    helpdesk_default_ticket_type_id = fields.Many2one(
        'helpdesk.ticket.type',
        string='Default Ticket Type',
        config_parameter='helpdesk.default_ticket_type_id',
        help='Default ticket type for new tickets'
    )
    
    # Ticket Numbering
    helpdesk_ticket_prefix = fields.Char(
        string='Ticket Number Prefix',
        config_parameter='helpdesk.ticket_prefix',
        default='TKT',
        help='Prefix for ticket numbers (e.g., TKT-001)'
    )
    
    helpdesk_ticket_number_format = fields.Selection(
        [
            ('sequential', 'Sequential (001, 002, 003)'),
            ('date_based', 'Date-Based (20260129-001)'),
            ('random', 'Random'),
        ],
        string='Ticket Number Format',
        config_parameter='helpdesk.ticket_number_format',
        default='sequential',
        help='Format for generating ticket numbers'
    )
    
    # ==================== Auto-Assignment Settings ====================
    
    helpdesk_auto_assign_tickets = fields.Boolean(
        string='Auto-Assign Tickets',
        config_parameter='helpdesk.auto_assign_tickets',
        default=False,
        help='Automatically assign tickets to available agents'
    )
    
    helpdesk_auto_assignment_method = fields.Selection(
        [
            ('round_robin', 'Round Robin'),
            ('load_based', 'Load-Based (Least Tickets)'),
            ('random', 'Random'),
            ('team_based', 'Team-Based'),
        ],
        string='Auto-Assignment Method',
        config_parameter='helpdesk.auto_assignment_method',
        default='round_robin',
        help='Method used for automatic ticket assignment'
    )
    
    helpdesk_max_tickets_per_agent = fields.Integer(
        string='Max Tickets Per Agent',
        config_parameter='helpdesk.max_tickets_per_agent',
        default=10,
        help='Maximum number of open tickets per agent (for load-based assignment)'
    )
    
    # ==================== SLA Settings ====================
    
    helpdesk_enable_sla_tracking = fields.Boolean(
        string='Enable SLA Tracking',
        config_parameter='helpdesk.enable_sla_tracking',
        default=True,
        help='Enable Service Level Agreement (SLA) tracking for tickets'
    )
    
    helpdesk_default_response_time = fields.Float(
        string='Default Response Time (Hours)',
        config_parameter='helpdesk.default_response_time',
        default=24.0,
        help='Default response time in hours for new tickets'
    )
    
    helpdesk_default_resolution_time = fields.Float(
        string='Default Resolution Time (Hours)',
        config_parameter='helpdesk.default_resolution_time',
        default=72.0,
        help='Default resolution time in hours for new tickets'
    )
    
    helpdesk_default_sla_policy_id = fields.Many2one(
        'helpdesk.sla.policy',
        string='Default SLA Policy',
        config_parameter='helpdesk.default_sla_policy_id',
        help='Default SLA policy to apply to new tickets'
    )
    
    helpdesk_sla_working_hours = fields.Boolean(
        string='Use Working Hours for SLA',
        config_parameter='helpdesk.sla_working_hours',
        default=False,
        help='Calculate SLA based on working hours instead of 24/7'
    )
    
    # ==================== Automation Settings ====================
    
    helpdesk_auto_close_resolved = fields.Boolean(
        string='Auto-Close Resolved Tickets',
        config_parameter='helpdesk.auto_close_resolved',
        default=False,
        help='Automatically close resolved tickets after specified days'
    )
    
    helpdesk_auto_close_days = fields.Integer(
        string='Days Before Auto-Close',
        config_parameter='helpdesk.auto_close_days',
        default=7,
        help='Number of days after resolution before auto-closing tickets'
    )
    
    helpdesk_enable_escalation = fields.Boolean(
        string='Enable Escalation Rules',
        config_parameter='helpdesk.enable_escalation',
        default=True,
        help='Enable automatic escalation of tickets based on rules'
    )
    
    helpdesk_enable_reminders = fields.Boolean(
        string='Enable Reminder System',
        config_parameter='helpdesk.enable_reminders',
        default=True,
        help='Enable reminder system for tickets'
    )
    
    helpdesk_enable_workflow = fields.Boolean(
        string='Enable Workflow Automation',
        config_parameter='helpdesk.enable_workflow',
        default=True,
        help='Enable workflow automation rules'
    )
    
    # ==================== Notification Settings ====================
    
    helpdesk_notify_on_assignment = fields.Boolean(
        string='Notify on Assignment',
        config_parameter='helpdesk.notify_on_assignment',
        default=True,
        help='Send notification when ticket is assigned to an agent'
    )
    
    helpdesk_notify_on_status_change = fields.Boolean(
        string='Notify on Status Change',
        config_parameter='helpdesk.notify_on_status_change',
        default=True,
        help='Send notification when ticket status changes'
    )
    
    helpdesk_notify_customer_on_update = fields.Boolean(
        string='Notify Customer on Update',
        config_parameter='helpdesk.notify_customer_on_update',
        default=True,
        help='Send email notification to customer when ticket is updated'
    )
    
    helpdesk_notify_on_sla_breach = fields.Boolean(
        string='Notify on SLA Breach',
        config_parameter='helpdesk.notify_on_sla_breach',
        default=True,
        help='Send notification when SLA is breached'
    )
    
    # ==================== Field Requirements ====================
    
    helpdesk_require_category = fields.Boolean(
        string='Require Category',
        config_parameter='helpdesk.require_category',
        default=False,
        help='Make category selection mandatory when creating tickets'
    )
    
    helpdesk_require_priority = fields.Boolean(
        string='Require Priority',
        config_parameter='helpdesk.require_priority',
        default=False,
        help='Make priority selection mandatory when creating tickets'
    )
    
    helpdesk_require_ticket_type = fields.Boolean(
        string='Require Ticket Type',
        config_parameter='helpdesk.require_ticket_type',
        default=False,
        help='Make ticket type selection mandatory when creating tickets'
    )
    
    # ==================== Integration Settings ====================
    
    helpdesk_enable_portal = fields.Boolean(
        string='Enable Portal Access',
        config_parameter='helpdesk.enable_portal',
        default=True,
        help='Allow customers to access tickets through portal'
    )
    
    helpdesk_enable_rating = fields.Boolean(
        string='Enable Customer Rating',
        config_parameter='helpdesk.enable_rating',
        default=True,
        help='Enable customer rating and feedback system'
    )
    
    helpdesk_enable_knowledge_base = fields.Boolean(
        string='Enable Knowledge Base',
        config_parameter='helpdesk.enable_knowledge_base',
        default=True,
        help='Enable knowledge base articles'
    )
    
    helpdesk_enable_social_media = fields.Boolean(
        string='Enable Social Media Integration',
        config_parameter='helpdesk.enable_social_media',
        default=False,
        help='Enable social media integration for ticket creation'
    )
    
    helpdesk_enable_call_logging = fields.Boolean(
        string='Enable Call Logging',
        config_parameter='helpdesk.enable_call_logging',
        default=True,
        help='Enable call log tracking and ticket creation from calls'
    )
    
    # ==================== Support Contact Information ====================
    
    helpdesk_support_email = fields.Char(
        string='Support Email',
        config_parameter='helpdesk.support_email',
        help='Support email address for customer inquiries'
    )
    
    helpdesk_support_phone = fields.Char(
        string='Support Phone',
        config_parameter='helpdesk.support_phone',
        help='Support phone number for customer inquiries'
    )
    
    # ==================== Sample Data Import Section ====================
    
    module_helpdesk_sample_data = fields.Boolean(
        string='Sample Data',
        help='Enable sample data import functionality'
    )
    
    helpdesk_sample_data_info = fields.Text(
        string='Sample Data Information',
        readonly=True,
        default='Use the buttons below to import or create sample data for testing and demonstration purposes.'
    )

    def action_import_sample_data(self):
        """Import sample data from demo_data.xml file"""
        self = self.sudo()  # Use sudo for admin operations
        self.ensure_one()
        
        try:
            from odoo.tools import convert_file
            import os
            
            # Get the module path
            module_path = os.path.dirname(os.path.dirname(__file__))
            demo_file = os.path.join(module_path, 'data', 'demo_data.xml')
            
            if not os.path.exists(demo_file):
                raise UserError(_('Demo data file not found: %s') % demo_file)
            
            # Load the demo data XML file using env instead of cr
            convert_file(
                self.env,
                'support_helpdesk_ticket',
                demo_file,
                {},
                mode='init',
                noupdate=False,
                kind='data'
            )
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Sample data imported successfully from demo_data.xml!'),
                    'type': 'success',
                    'sticky': False,
                }
            }
        except Exception as e:
            _logger.error(f"Error importing sample data: {e}")
            raise UserError(_('Error importing sample data: %s') % str(e))

    def action_create_demo_records(self):
        """Create demo records for all models programmatically"""
        self = self.sudo()  # Use sudo for admin operations
        self.ensure_one()
        
        try:
            created_count = 0
            
            # Get current user (ID 2 or current user)
            current_user = self.env.user
            if current_user.id != 2:
                # Try to get user ID 2
                user_2 = self.env['res.users'].browse(2)
                if user_2.exists():
                    current_user = user_2
            
            # Get demo partners (use sudo to bypass access rights)
            partner1 = self.env['res.partner'].sudo().search([('email', '=', 'support@acme.com')], limit=1)
            partner2 = self.env['res.partner'].sudo().search([('email', '=', 'help@techstart.com')], limit=1)
            partner3 = self.env['res.partner'].sudo().search([('email', '=', 'support@globalsolutions.com')], limit=1)
            
            if not partner1:
                partner1 = self.env['res.partner'].sudo().create({
                    'name': 'Acme Corporation',
                    'email': 'support@acme.com',
                    'phone': '+1-555-0101',
                })
            
            if not partner2:
                partner2 = self.env['res.partner'].sudo().create({
                    'name': 'TechStart Inc',
                    'email': 'help@techstart.com',
                    'phone': '+1-555-0102',
                })
            
            if not partner3:
                partner3 = self.env['res.partner'].sudo().create({
                    'name': 'Global Solutions Ltd',
                    'email': 'support@globalsolutions.com',
                    'phone': '+1-555-0103',
                })
            
            # Get or create teams (use sudo to bypass access rights)
            team_technical = self.env['helpdesk.team'].sudo().search([('name', '=', 'Technical Support')], limit=1)
            if not team_technical:
                team_technical = self.env['helpdesk.team'].sudo().create({
                    'name': 'Technical Support',
                    'description': 'Technical issues, bugs, and system problems',
                    'active': True,
                })
            
            # Get or create categories (use sudo to bypass access rights)
            category_software = self.env['helpdesk.category'].sudo().search([('name', '=', 'Software Issues')], limit=1)
            if not category_software:
                category_software = self.env['helpdesk.category'].sudo().create({
                    'name': 'Software Issues',
                    'description': 'Application errors, bugs, and software problems',
                    'color': 2,
                    'sequence': 20,
                    'default_priority': '1',
                })
            
            category_hardware = self.env['helpdesk.category'].sudo().search([('name', '=', 'Hardware Issues')], limit=1)
            if not category_hardware:
                category_hardware = self.env['helpdesk.category'].sudo().create({
                    'name': 'Hardware Issues',
                    'description': 'Computer, printer, and hardware problems',
                    'color': 1,
                    'sequence': 10,
                    'default_priority': '1',
                })
            
            # Get or create ticket types (use sudo to bypass access rights)
            ticket_type_incident = self.env['helpdesk.ticket.type'].sudo().search([('name', '=', 'Technical Support')], limit=1)
            if not ticket_type_incident:
                ticket_type_incident = self.env['helpdesk.ticket.type'].sudo().create({
                    'name': 'Technical Support',
                    'description': 'Issues related to technical problems, system errors, and incidents.',
                    'active': True,
                    'default_priority': '2',
                })
            
            ticket_type_request = self.env['helpdesk.ticket.type'].sudo().search([('name', '=', 'Service Request')], limit=1)
            if not ticket_type_request:
                ticket_type_request = self.env['helpdesk.ticket.type'].sudo().create({
                    'name': 'Service Request',
                    'description': 'Standard request for information or service.',
                    'active': True,
                    'default_priority': '1',
                })
            
            # Create demo tickets for current user (use sudo to bypass access rights)
            ticket_vals_list = [
                {
                    'name': 'Sample Ticket 1: System Performance Issue',
                    'description': 'Customer reports slow system performance. Need to investigate and optimize.',
                    'partner_id': partner1.id,
                    'ticket_type_id': ticket_type_incident.id,
                    'category_id': category_software.id,
                    'priority': '2',
                    'state': 'in_progress',
                    'user_id': current_user.id,
                    'team_id': team_technical.id,
                    'channel': 'email',
                },
                {
                    'name': 'Sample Ticket 2: Hardware Replacement Request',
                    'description': 'Customer needs replacement for faulty keyboard. Warranty claim.',
                    'partner_id': partner2.id,
                    'ticket_type_id': ticket_type_request.id,
                    'category_id': category_hardware.id,
                    'priority': '1',
                    'state': 'assigned',
                    'user_id': current_user.id,
                    'team_id': team_technical.id,
                    'channel': 'web',
                },
                {
                    'name': 'Sample Ticket 3: Account Access Issue',
                    'description': 'Customer cannot access their account. Password reset required.',
                    'partner_id': partner3.id,
                    'ticket_type_id': ticket_type_incident.id,
                    'category_id': category_software.id,
                    'priority': '2',
                    'state': 'new',
                    'team_id': team_technical.id,
                    'channel': 'phone',
                },
                {
                    'name': 'Sample Ticket 4: Feature Request',
                    'description': 'Customer requests new feature for dark mode in the application.',
                    'partner_id': partner1.id,
                    'ticket_type_id': ticket_type_request.id,
                    'category_id': category_software.id,
                    'priority': '0',
                    'state': 'resolved',
                    'user_id': current_user.id,
                    'team_id': team_technical.id,
                    'channel': 'web',
                    'resolved_date': datetime.now() - timedelta(days=1),
                },
                {
                    'name': 'Sample Ticket 5: Urgent Bug Report',
                    'description': 'Critical bug causing data loss. Immediate attention required.',
                    'partner_id': partner2.id,
                    'ticket_type_id': ticket_type_incident.id,
                    'category_id': category_software.id,
                    'priority': '3',
                    'state': 'in_progress',
                    'user_id': current_user.id,
                    'team_id': team_technical.id,
                    'channel': 'email',
                },
                {
                    'name': 'Sample Ticket 6: Network Connectivity Issue',
                    'description': 'Customer experiencing intermittent network disconnections. Affecting productivity.',
                    'partner_id': partner3.id,
                    'ticket_type_id': ticket_type_incident.id,
                    'category_id': category_software.id,
                    'priority': '2',
                    'state': 'assigned',
                    'user_id': current_user.id,
                    'team_id': team_technical.id,
                    'channel': 'phone',
                    'assigned_date': datetime.now() - timedelta(hours=2),
                },
                {
                    'name': 'Sample Ticket 7: Closed Ticket Example',
                    'description': 'This ticket was successfully resolved and closed. Good example of completed work.',
                    'partner_id': partner1.id,
                    'ticket_type_id': ticket_type_request.id,
                    'category_id': category_hardware.id,
                    'priority': '1',
                    'state': 'closed',
                    'user_id': current_user.id,
                    'team_id': team_technical.id,
                    'channel': 'web',
                    'resolved_date': datetime.now() - timedelta(days=3),
                    'closed_date': datetime.now() - timedelta(days=2),
                    'rating': '4',
                },
                {
                    'name': 'Sample Ticket 8: Low Priority Inquiry',
                    'description': 'General question about product features and capabilities.',
                    'partner_id': partner2.id,
                    'ticket_type_id': ticket_type_request.id,
                    'priority': '0',
                    'state': 'new',
                    'team_id': team_technical.id,
                    'channel': 'web',
                },
            ]
            
            # Create tickets and ensure at least 5 are successfully created
            tickets = self.env['helpdesk.ticket'].sudo().create(ticket_vals_list)
            created_count += len(tickets)
            
            # Ensure we have at least 5 tickets for demo purposes
            if len(tickets) < 5:
                # Create additional tickets if needed
                additional_needed = 5 - len(tickets)
                additional_tickets = []
                for i in range(additional_needed):
                    additional_tickets.append({
                        'name': f'Sample Ticket {len(tickets) + i + 1}: Additional Demo Ticket',
                        'description': f'Additional demo ticket #{len(tickets) + i + 1} for demonstration purposes.',
                        'partner_id': partner1.id if i % 2 == 0 else partner2.id,
                        'ticket_type_id': ticket_type_incident.id if i % 2 == 0 else ticket_type_request.id,
                        'priority': str(i % 4),  # Cycle through priorities 0-3
                        'state': ['new', 'assigned', 'in_progress', 'resolved'][i % 4],
                        'team_id': team_technical.id,
                        'channel': ['email', 'web', 'phone'][i % 3],
                    })
                if additional_tickets:
                    additional_created = self.env['helpdesk.ticket'].sudo().create(additional_tickets)
                    tickets |= additional_created
                    created_count += len(additional_created)
            
            # Create demo call logs (use sudo to bypass access rights)
            call_log_vals_list = [
                {
                    'call_date': datetime.now() - timedelta(hours=2),
                    'call_end_date': datetime.now() - timedelta(hours=1, minutes=45),
                    'direction': 'inbound',
                    'phone_number': '+1-555-1001',
                    'partner_id': partner1.id,
                    'contact_name': 'John Doe',
                    'subject': 'Follow-up call',
                    'description': 'Follow-up call regarding ticket status.',
                    'call_outcome': 'resolved',
                    'agent_id': current_user.id,
                    'state': 'completed',
                },
                {
                    'call_date': datetime.now() - timedelta(days=1, hours=3),
                    'call_end_date': datetime.now() - timedelta(days=1, hours=2, minutes=50),
                    'direction': 'outbound',
                    'phone_number': '+1-555-1002',
                    'partner_id': partner2.id,
                    'contact_name': 'Jane Smith',
                    'subject': 'Support call',
                    'description': 'Outbound support call to assist customer.',
                    'call_outcome': 'resolved',
                    'agent_id': current_user.id,
                    'state': 'completed',
                },
            ]
            
            call_logs = self.env['helpdesk.call.log'].sudo().create(call_log_vals_list)
            created_count += len(call_logs)
            
            # Create demo tags (use sudo to bypass access rights)
            tag_urgent = self.env['helpdesk.tag'].sudo().search([('name', '=', 'Urgent')], limit=1)
            if not tag_urgent:
                tag_urgent = self.env['helpdesk.tag'].sudo().create({
                    'name': 'Urgent',
                    'color': 1,
                    'sequence': 1,
                })
            
            tag_bug = self.env['helpdesk.tag'].sudo().search([('name', '=', 'Bug Report')], limit=1)
            if not tag_bug:
                tag_bug = self.env['helpdesk.tag'].sudo().create({
                    'name': 'Bug Report',
                    'color': 2,
                    'sequence': 2,
                })
            
            # Create demo knowledge articles (use sudo to bypass access rights)
            kb_article = self.env['helpdesk.knowledge.article'].sudo().search([('name', '=', 'How to Reset Your Password')], limit=1)
            if not kb_article:
                kb_article = self.env['helpdesk.knowledge.article'].sudo().create({
                    'name': 'How to Reset Your Password',
                    'content': '<h2>Password Reset Guide</h2><p>To reset your password, follow these steps:</p><ol><li>Go to the login page</li><li>Click "Forgot Password"</li><li>Enter your email address</li><li>Check your email for reset instructions</li></ol>',
                    'category_id': category_software.id,
                    'active': True,
                })
                created_count += 1
            
            # Create more categories
            category_network = self.env['helpdesk.category'].sudo().search([('name', '=', 'Network & Connectivity')], limit=1)
            if not category_network:
                category_network = self.env['helpdesk.category'].sudo().create({
                    'name': 'Network & Connectivity',
                    'description': 'Internet, WiFi, and network connectivity issues',
                    'color': 3,
                    'sequence': 30,
                    'default_priority': '1',
                })
                created_count += 1
            
            category_account = self.env['helpdesk.category'].sudo().search([('name', '=', 'Account & Login')], limit=1)
            if not category_account:
                category_account = self.env['helpdesk.category'].sudo().create({
                    'name': 'Account & Login',
                    'description': 'Password resets, account access, and login issues',
                    'color': 4,
                    'sequence': 40,
                    'default_priority': '2',
                })
                created_count += 1
            
            # Create more tags
            tag_feature = self.env['helpdesk.tag'].sudo().search([('name', '=', 'Feature Request')], limit=1)
            if not tag_feature:
                tag_feature = self.env['helpdesk.tag'].sudo().create({
                    'name': 'Feature Request',
                    'color': 3,
                    'sequence': 3,
                })
                created_count += 1
            
            tag_training = self.env['helpdesk.tag'].sudo().search([('name', '=', 'Training Needed')], limit=1)
            if not tag_training:
                tag_training = self.env['helpdesk.tag'].sudo().create({
                    'name': 'Training Needed',
                    'color': 4,
                    'sequence': 4,
                })
                created_count += 1
            
            # Create more teams
            team_sales = self.env['helpdesk.team'].sudo().search([('name', '=', 'Sales Support')], limit=1)
            if not team_sales:
                team_sales = self.env['helpdesk.team'].sudo().create({
                    'name': 'Sales Support',
                    'description': 'Sales inquiries and product information',
                    'active': True,
                })
                created_count += 1
            
            team_billing = self.env['helpdesk.team'].sudo().search([('name', '=', 'Billing & Accounts')], limit=1)
            if not team_billing:
                team_billing = self.env['helpdesk.team'].sudo().create({
                    'name': 'Billing & Accounts',
                    'description': 'Billing questions, invoices, and payment issues',
                    'active': True,
                })
                created_count += 1
            
            # Create more ticket types
            ticket_type_bug = self.env['helpdesk.ticket.type'].sudo().search([('name', '=', 'Bug Report')], limit=1)
            if not ticket_type_bug:
                ticket_type_bug = self.env['helpdesk.ticket.type'].sudo().create({
                    'name': 'Bug Report',
                    'description': 'Reports of software bugs or defects.',
                    'active': True,
                    'default_priority': '2',
                })
                created_count += 1
            
            ticket_type_feature = self.env['helpdesk.ticket.type'].sudo().search([('name', '=', 'Feature Request')], limit=1)
            if not ticket_type_feature:
                ticket_type_feature = self.env['helpdesk.ticket.type'].sudo().create({
                    'name': 'Feature Request',
                    'description': 'Suggestions for new features or improvements.',
                    'active': True,
                    'default_priority': '1',
                })
                created_count += 1
            
            # Create SLA Policies
            sla_standard = self.env['helpdesk.sla.policy'].sudo().search([('name', '=', 'Standard SLA')], limit=1)
            if not sla_standard:
                sla_standard = self.env['helpdesk.sla.policy'].sudo().create({
                    'name': 'Standard SLA',
                    'description': 'Standard SLA policy for normal priority tickets',
                    'response_time': 24.0,
                    'resolution_time': 72.0,
                    'priority_all': True,
                    'active': True,
                })
                created_count += 1
            
            sla_priority = self.env['helpdesk.sla.policy'].sudo().search([('name', '=', 'Priority SLA')], limit=1)
            if not sla_priority:
                sla_priority = self.env['helpdesk.sla.policy'].sudo().create({
                    'name': 'Priority SLA',
                    'description': 'Priority SLA policy for high priority tickets',
                    'response_time': 4.0,
                    'resolution_time': 24.0,
                    'priority_selection': '2',
                    'active': True,
                })
                created_count += 1
            
            # Create SLA Escalation Rules
            sla_escalation = self.env['helpdesk.sla.escalation.rule'].sudo().search([('name', '=', 'Standard Escalation')], limit=1)
            if not sla_escalation:
                sla_escalation = self.env['helpdesk.sla.escalation.rule'].sudo().create({
                    'name': 'Standard Escalation',
                    'sla_policy_id': sla_standard.id,
                    'trigger_type': 'response_time',
                    'trigger_percentage': 80.0,
                    'action_type': 'notify',
                    'notify_team_id': team_technical.id,
                    'active': True,
                })
                created_count += 1
            
            # Create Workflow Rules
            workflow_rule = self.env['helpdesk.workflow.rule'].sudo().search([('name', '=', 'Auto Assign on Create')], limit=1)
            if not workflow_rule:
                workflow_rule = self.env['helpdesk.workflow.rule'].sudo().create({
                    'name': 'Auto Assign on Create',
                    'description': 'Automatically assign tickets to team leader when created',
                    'trigger': 'on_create',
                    'action_type': 'assign',
                    'action_assign_team_id': team_technical.id,
                    'active': True,
                })
                created_count += 1
            
            # Create Ticket Templates
            ticket_template = self.env['helpdesk.ticket.template'].sudo().search([('name', '=', 'Password Reset Template')], limit=1)
            if not ticket_template:
                ticket_template = self.env['helpdesk.ticket.template'].sudo().create({
                    'name': 'Password Reset Template',
                    'description': 'Template for password reset requests',
                    'subject': 'Password Reset Request',
                    'ticket_type_id': ticket_type_request.id,
                    'category_id': category_account.id,
                    'priority': '1',
                    'team_id': team_technical.id,
                    'active': True,
                })
                created_count += 1
            
            # Create Escalation Rules
            escalation_rule = self.env['helpdesk.escalation.rule'].sudo().search([('name', '=', 'Urgent Ticket Escalation')], limit=1)
            if not escalation_rule:
                escalation_rule = self.env['helpdesk.escalation.rule'].sudo().create({
                    'name': 'Urgent Ticket Escalation',
                    'description': 'Escalate urgent tickets after 2 hours',
                    'trigger_type': 'time_based',
                    'time_trigger_type': 'since_creation',
                    'time_trigger_hours': 2.0,
                    'priority_filter': '3',
                    'action_type': 'notify',
                    'action_notify_team_id': team_technical.id,
                    'active': True,
                })
                created_count += 1
            
            # Create Notification Templates
            notif_template = self.env['helpdesk.notification.template'].sudo().search([('name', '=', 'Ticket Created Notification')], limit=1)
            if not notif_template:
                notif_template = self.env['helpdesk.notification.template'].sudo().create({
                    'name': 'Ticket Created Notification',
                    'description': 'Notification sent when ticket is created',
                    'notification_type': 'ticket_created',
                    'notification_channel': 'email',
                    'subject': 'New Ticket Created: {{ticket.name}}',
                    'body_html': '<p>A new ticket has been created. Ticket Number: {{ticket.ticket_number}}</p>',
                    'recipient_type': 'customer',
                    'active': True,
                })
                created_count += 1
            
            # Create Notification Preferences
            notif_pref = self.env['helpdesk.notification.preference'].sudo().search([
                ('user_id', '=', current_user.id),
                ('notification_type', '=', 'ticket_created')
            ], limit=1)
            if not notif_pref:
                notif_pref = self.env['helpdesk.notification.preference'].sudo().create({
                    'user_id': current_user.id,
                    'notification_type': 'ticket_created',
                    'email_enabled': True,
                    'in_app_enabled': True,
                })
                created_count += 1
            
            # Create Reminder Rules
            reminder_rule = self.env['helpdesk.reminder.rule'].sudo().search([('name', '=', 'Follow-up Reminder')], limit=1)
            if not reminder_rule:
                reminder_rule = self.env['helpdesk.reminder.rule'].sudo().create({
                    'name': 'Follow-up Reminder',
                    'description': 'Remind agents to follow up on tickets',
                    'trigger_type': 'time_based',
                    'time_trigger_type': 'since_creation',
                    'time_trigger_hours': 48.0,
                    'reminder_user_type': 'assigned_user',
                    'active': True,
                })
                created_count += 1
            
            # Create Reminders
            if tickets:
                reminder = self.env['helpdesk.reminder'].sudo().search([
                    ('ticket_id', '=', tickets[0].id),
                    ('reminder_rule_id', '=', reminder_rule.id)
                ], limit=1)
                if not reminder:
                    reminder = self.env['helpdesk.reminder'].sudo().create({
                        'ticket_id': tickets[0].id,
                        'reminder_rule_id': reminder_rule.id,
                        'user_id': current_user.id,
                        'reminder_date': datetime.now() + timedelta(days=2),
                        'status': 'pending',
                    })
                    created_count += 1
            
            # Create Social Media Platforms
            social_platform_fb = self.env['helpdesk.social.media.platform'].sudo().search([('name', '=', 'Facebook Demo')], limit=1)
            if not social_platform_fb:
                social_platform_fb = self.env['helpdesk.social.media.platform'].sudo().create({
                    'name': 'Facebook Demo',
                    'platform_type': 'facebook',
                    'page_id': 'demo_facebook_page',
                    'active': True,
                    'monitor_posts': True,
                    'monitor_messages': True,
                    'monitor_comments': True,
                    'default_team_id': team_sales.id,
                    'default_priority': '1',
                })
                created_count += 1
            
            social_platform_tw = self.env['helpdesk.social.media.platform'].sudo().search([('name', '=', 'Twitter Demo')], limit=1)
            if not social_platform_tw:
                social_platform_tw = self.env['helpdesk.social.media.platform'].sudo().create({
                    'name': 'Twitter Demo',
                    'platform_type': 'twitter',
                    'page_id': '@demo_twitter',
                    'active': True,
                    'monitor_posts': True,
                    'monitor_messages': False,
                    'monitor_comments': True,
                    'default_team_id': team_sales.id,
                    'default_priority': '0',
                })
                created_count += 1
            
            # Create Social Media Posts
            social_post1 = self.env['helpdesk.social.media.post'].sudo().search([
                ('platform_id', '=', social_platform_fb.id),
                ('post_id', '=', 'fb_demo_001')
            ], limit=1)
            if not social_post1:
                social_post1 = self.env['helpdesk.social.media.post'].sudo().create({
                    'platform_id': social_platform_fb.id,
                    'platform_type': 'facebook',
                    'post_type': 'post',
                    'post_id': 'fb_demo_001',
                    'content': 'Having trouble accessing our online portal. Can someone help?',
                    'post_date': datetime.now() - timedelta(hours=2),
                    'author_name': 'Demo Customer',
                    'author_username': 'demo.customer',
                    'state': 'new',
                })
                created_count += 1
            
            # Create Ticket Model Links
            if tickets and partner1:
                model_link = self.env['helpdesk.ticket.model.link'].sudo().search([
                    ('ticket_id', '=', tickets[0].id),
                    ('model_name', '=', 'res.partner'),
                    ('res_id', '=', partner1.id)
                ], limit=1)
                if not model_link:
                    model_link = self.env['helpdesk.ticket.model.link'].sudo().create({
                        'ticket_id': tickets[0].id,
                        'model_name': 'res.partner',
                        'res_id': partner1.id,
                    })
                    created_count += 1
            
            # Create Auto Link Rules
            auto_link_rule = self.env['helpdesk.auto.link.rule'].sudo().search([('name', '=', 'Auto Link Partner')], limit=1)
            if not auto_link_rule:
                auto_link_rule = self.env['helpdesk.auto.link.rule'].sudo().create({
                    'name': 'Auto Link Partner',
                    'description': 'Automatically link tickets to partner records by email',
                    'target_model': 'res.partner',
                    'pattern_type': 'contains',
                    'pattern': '@',
                    'search_field': 'email',
                    'active': True,
                })
                created_count += 1
            
            # Create Ticket Status History
            if tickets:
                status_history = self.env['helpdesk.ticket.status.history'].sudo().search([
                    ('ticket_id', '=', tickets[0].id)
                ], limit=1)
                if not status_history:
                    status_history = self.env['helpdesk.ticket.status.history'].sudo().create({
                        'ticket_id': tickets[0].id,
                        'old_state': 'new',
                        'new_state': tickets[0].state,
                        'user_id': current_user.id,
                        'change_date': datetime.now(),
                    })
                    created_count += 1
            
            # Create Ticket Assignment History
            if tickets:
                assign_history = self.env['helpdesk.ticket.assignment.history'].sudo().search([
                    ('ticket_id', '=', tickets[0].id)
                ], limit=1)
                if not assign_history:
                    assign_history = self.env['helpdesk.ticket.assignment.history'].sudo().create({
                        'ticket_id': tickets[0].id,
                        'old_user_id': False,
                        'new_user_id': current_user.id,
                        'assigned_by_id': current_user.id,
                        'assignment_date': datetime.now(),
                        'assignment_method': 'manual',
                    })
                    created_count += 1
            
            # Create Escalation Logs
            if tickets and escalation_rule:
                escalation_log = self.env['helpdesk.escalation.log'].sudo().search([
                    ('ticket_id', '=', tickets[0].id),
                    ('rule_id', '=', escalation_rule.id)
                ], limit=1)
                if not escalation_log:
                    escalation_log = self.env['helpdesk.escalation.log'].sudo().create({
                        'ticket_id': tickets[0].id,
                        'rule_id': escalation_rule.id,
                        'escalation_level': 1,
                        'escalation_date': datetime.now(),
                    })
                    created_count += 1
            
            # Create Notification History
            if tickets and notif_template:
                notif_history = self.env['helpdesk.notification.history'].sudo().search([
                    ('ticket_id', '=', tickets[0].id),
                    ('template_id', '=', notif_template.id)
                ], limit=1)
                if not notif_history:
                    notif_history = self.env['helpdesk.notification.history'].sudo().create({
                        'ticket_id': tickets[0].id,
                        'template_id': notif_template.id,
                        'notification_type': 'ticket_created',
                        'notification_channel': 'email',
                        'recipient_count': 1,
                        'sent_date': datetime.now(),
                        'status': 'sent',
                    })
                    created_count += 1
            
            # Create Notification Schedules
            if tickets:
                notif_schedule = self.env['helpdesk.notification.schedule'].sudo().search([
                    ('ticket_id', '=', tickets[0].id)
                ], limit=1)
                if not notif_schedule:
                    notif_schedule = self.env['helpdesk.notification.schedule'].sudo().create({
                        'ticket_id': tickets[0].id,
                        'template_id': notif_template.id,
                        'scheduled_date': datetime.now() + timedelta(hours=24),
                        'status': 'pending',
                    })
                    created_count += 1
            
            # Create Workflow Execution Logs
            if tickets and workflow_rule:
                workflow_log = self.env['helpdesk.workflow.execution.log'].sudo().search([
                    ('ticket_id', '=', tickets[0].id),
                    ('rule_id', '=', workflow_rule.id)
                ], limit=1)
                if not workflow_log:
                    # Map workflow rule trigger to execution log trigger_type
                    trigger_map = {
                        'on_create': 'create',
                        'on_update': 'write',
                        'on_status_change': 'state_change',
                        'on_field_change': 'field_change',
                    }
                    trigger_type = trigger_map.get(workflow_rule.trigger, 'create')
                    workflow_log = self.env['helpdesk.workflow.execution.log'].sudo().create({
                        'ticket_id': tickets[0].id,
                        'rule_id': workflow_rule.id,
                        'trigger_type': trigger_type,
                        'execution_date': datetime.now(),
                        'status': 'success',
                    })
                    created_count += 1
            
            # Create Model Link Access Logs
            if model_link:
                access_log = self.env['helpdesk.model.link.access.log'].sudo().search([
                    ('link_id', '=', model_link.id),
                    ('user_id', '=', current_user.id)
                ], limit=1)
                if not access_log:
                    access_log = self.env['helpdesk.model.link.access.log'].sudo().create({
                        'link_id': model_link.id,
                        'user_id': current_user.id,
                        'access_date': datetime.now(),
                        'access_type': 'view',
                    })
                    created_count += 1
            
            # Create Knowledge Article Feedback
            if kb_article:
                kb_feedback = self.env['helpdesk.knowledge.article.feedback'].sudo().search([
                    ('article_id', '=', kb_article.id)
                ], limit=1)
                if not kb_feedback:
                    kb_feedback = self.env['helpdesk.knowledge.article.feedback'].sudo().create({
                        'article_id': kb_article.id,
                        'rating': '4',
                        'feedback': 'Very helpful article!',
                        'partner_id': partner1.id,
                    })
                    created_count += 1
            
            # Create more knowledge articles
            kb_article2 = self.env['helpdesk.knowledge.article'].sudo().search([('name', '=', 'Printer Troubleshooting Guide')], limit=1)
            if not kb_article2:
                kb_article2 = self.env['helpdesk.knowledge.article'].sudo().create({
                    'name': 'Printer Troubleshooting Guide',
                    'content': '<h2>Common Printer Issues</h2><p>Check connections, restart printer, check ink levels.</p>',
                    'category_id': category_hardware.id,
                    'active': True,
                })
                created_count += 1
            
            # Create more report templates
            report_template2 = self.env['helpdesk.report.template'].sudo().search([('name', '=', 'Tickets by Priority & Agent')], limit=1)
            if not report_template2:
                report_template2 = self.env['helpdesk.report.template'].sudo().create({
                    'name': 'Tickets by Priority & Agent',
                    'view_type': 'graph',
                    'graph_type': 'priority',
                    'group_by_field': 'priority',
                    'secondary_group_by_field': 'user_id',
                    'measure_field': 'id',
                })
                created_count += 1
            
            # Create more call logs
            call_log3 = self.env['helpdesk.call.log'].sudo().create({
                'call_date': datetime.now() - timedelta(hours=6),
                'call_end_date': datetime.now() - timedelta(hours=5, minutes=30),
                'direction': 'inbound',
                'phone_number': '+1-555-1003',
                'partner_id': partner3.id,
                'contact_name': 'Bob Johnson',
                'subject': 'Technical support',
                'description': 'Customer calling for technical assistance.',
                'call_outcome': 'escalated',
                'agent_id': current_user.id,
                'state': 'completed',
            })
            created_count += 1
            
            # Create more tickets
            ticket6 = self.env['helpdesk.ticket'].sudo().create({
                'name': 'Sample Ticket 6: Network Connectivity Issue',
                'description': 'Customer reports intermittent network disconnections.',
                'partner_id': partner3.id,
                'ticket_type_id': ticket_type_incident.id,
                'category_id': category_network.id,
                'priority': '1',
                'state': 'assigned',
                'user_id': current_user.id,
                'team_id': team_technical.id,
                'channel': 'phone',
                'tag_ids': [(6, 0, [tag_urgent.id])],
            })
            created_count += 1
            
            ticket7 = self.env['helpdesk.ticket'].sudo().create({
                'name': 'Sample Ticket 7: Feature Request - Dark Mode',
                'description': 'Customer requests dark mode feature for the application.',
                'partner_id': partner1.id,
                'ticket_type_id': ticket_type_feature.id,
                'category_id': category_software.id,
                'priority': '0',
                'state': 'new',
                'team_id': team_technical.id,
                'channel': 'web',
                'tag_ids': [(6, 0, [tag_feature.id])],
            })
            created_count += 1
            
            # Create Ticket Merge History (if we have multiple tickets)
            if len(tickets) >= 2:
                merge_history = self.env['helpdesk.ticket.merge.history'].sudo().search([
                    ('master_ticket_id', '=', tickets[0].id),
                    ('merged_ticket_ids', 'in', [tickets[1].id])
                ], limit=1)
                if not merge_history:
                    merge_history = self.env['helpdesk.ticket.merge.history'].sudo().create({
                        'master_ticket_id': tickets[0].id,
                        'merged_ticket_ids': [(6, 0, [tickets[1].id])],
                        'user_id': current_user.id,
                        'merge_date': datetime.now(),
                    })
                    created_count += 1
            
            # Create Ticket Split History
            if tickets:
                split_history = self.env['helpdesk.ticket.split.history'].sudo().search([
                    ('source_ticket_id', '=', tickets[0].id)
                ], limit=1)
                if not split_history:
                    # Create a child ticket first
                    child_ticket = self.env['helpdesk.ticket'].sudo().create({
                        'name': 'Split Ticket: Sub-issue 1',
                        'description': 'This is a split ticket from the main issue.',
                        'partner_id': tickets[0].partner_id.id,
                        'parent_ticket_id': tickets[0].id,
                        'priority': tickets[0].priority,
                        'state': 'new',
                        'team_id': tickets[0].team_id.id,
                    })
                    split_history = self.env['helpdesk.ticket.split.history'].sudo().create({
                        'source_ticket_id': tickets[0].id,
                        'new_ticket_id': child_ticket.id,
                        'user_id': current_user.id,
                        'split_date': datetime.now(),
                    })
                    created_count += 2  # Child ticket + history
            
            # Create additional Knowledge Article Feedback
            if kb_article2:
                kb_feedback2 = self.env['helpdesk.knowledge.article.feedback'].sudo().search([
                    ('article_id', '=', kb_article2.id),
                    ('partner_id', '=', partner2.id)
                ], limit=1)
                if not kb_feedback2:
                    kb_feedback2 = self.env['helpdesk.knowledge.article.feedback'].sudo().create({
                        'article_id': kb_article2.id,
                        'rating': '5',
                        'feedback': 'Excellent troubleshooting guide!',
                        'partner_id': partner2.id,
                        'helpful': True,
                    })
                    created_count += 1
            
            # Create additional Report Templates
            report_template3 = self.env['helpdesk.report.template'].sudo().search([('name', '=', 'Tickets by Status & Team')], limit=1)
            if not report_template3:
                report_template3 = self.env['helpdesk.report.template'].sudo().create({
                    'name': 'Tickets by Status & Team',
                    'view_type': 'pivot',
                    'group_by_field': 'state',
                    'secondary_group_by_field': 'team_id',
                    'measure_field': 'id',
                })
                created_count += 1
            
            report_template4 = self.env['helpdesk.report.template'].sudo().search([('name', '=', 'Tickets by Channel')], limit=1)
            if not report_template4:
                report_template4 = self.env['helpdesk.report.template'].sudo().create({
                    'name': 'Tickets by Channel',
                    'view_type': 'graph',
                    'graph_type': 'channel',
                    'group_by_field': 'channel',
                    'measure_field': 'id',
                })
                created_count += 1
            
            # Create additional Social Media Posts
            if social_platform_tw:
                social_post2 = self.env['helpdesk.social.media.post'].sudo().search([
                    ('platform_id', '=', social_platform_tw.id),
                    ('post_id', '=', 'tw_demo_001')
                ], limit=1)
                if not social_post2:
                    social_post2 = self.env['helpdesk.social.media.post'].sudo().create({
                        'platform_id': social_platform_tw.id,
                        'platform_type': 'twitter',
                        'post_type': 'mention',
                        'post_id': 'tw_demo_001',
                        'content': 'Need help with account access. @support',
                        'post_date': datetime.now() - timedelta(hours=1),
                        'author_name': 'Twitter User',
                        'author_username': '@twitteruser',
                        'state': 'new',
                    })
                    created_count += 1
            
            # Create additional Notification Templates
            notif_template2 = self.env['helpdesk.notification.template'].sudo().search([('name', '=', 'Ticket Resolved Notification')], limit=1)
            if not notif_template2:
                notif_template2 = self.env['helpdesk.notification.template'].sudo().create({
                    'name': 'Ticket Resolved Notification',
                    'description': 'Notification sent when ticket is resolved',
                    'notification_type': 'ticket_resolved',
                    'notification_channel': 'email',
                    'subject': 'Ticket Resolved: {{ticket.ticket_number}}',
                    'body_html': '<p>Your ticket has been resolved. Ticket Number: {{ticket.ticket_number}}</p>',
                    'recipient_type': 'customer',
                    'active': True,
                })
                created_count += 1
            
            # Create additional Notification Preferences
            notif_pref2 = self.env['helpdesk.notification.preference'].sudo().search([
                ('user_id', '=', current_user.id),
                ('notification_type', '=', 'ticket_resolved')
            ], limit=1)
            if not notif_pref2:
                notif_pref2 = self.env['helpdesk.notification.preference'].sudo().create({
                    'user_id': current_user.id,
                    'notification_type': 'ticket_resolved',
                    'email_enabled': True,
                    'in_app_enabled': True,
                })
                created_count += 1
            
            # Create additional Reminder Rules
            reminder_rule2 = self.env['helpdesk.reminder.rule'].sudo().search([('name', '=', 'Overdue Ticket Reminder')], limit=1)
            if not reminder_rule2:
                reminder_rule2 = self.env['helpdesk.reminder.rule'].sudo().create({
                    'name': 'Overdue Ticket Reminder',
                    'description': 'Remind agents about overdue tickets',
                    'trigger_type': 'time_based',
                    'time_trigger_type': 'since_update',
                    'time_trigger_hours': 72.0,
                    'reminder_user_type': 'assigned_user',
                    'active': True,
                })
                created_count += 1
            
            # Create additional Escalation Rules
            escalation_rule2 = self.env['helpdesk.escalation.rule'].sudo().search([('name', '=', 'High Priority Escalation')], limit=1)
            if not escalation_rule2:
                escalation_rule2 = self.env['helpdesk.escalation.rule'].sudo().create({
                    'name': 'High Priority Escalation',
                    'description': 'Escalate high priority tickets after 4 hours',
                    'trigger_type': 'time_based',
                    'time_trigger_type': 'since_creation',
                    'time_trigger_hours': 4.0,
                    'priority_filter': '2',
                    'action_type': 'notify',
                    'action_notify_team_id': team_technical.id,
                    'active': True,
                })
                created_count += 1
            
            # Create additional Workflow Rules
            workflow_rule2 = self.env['helpdesk.workflow.rule'].sudo().search([('name', '=', 'Auto Assign High Priority')], limit=1)
            if not workflow_rule2:
                workflow_rule2 = self.env['helpdesk.workflow.rule'].sudo().create({
                    'name': 'Auto Assign High Priority',
                    'description': 'Automatically assign high priority tickets to team leader',
                    'trigger': 'on_create',
                    'action_type': 'assign',
                    'action_assign_team_id': team_technical.id,
                    'active': True,
                })
                created_count += 1
            
            # Create additional Ticket Templates
            ticket_template2 = self.env['helpdesk.ticket.template'].sudo().search([('name', '=', 'Bug Report Template')], limit=1)
            if not ticket_template2:
                ticket_template2 = self.env['helpdesk.ticket.template'].sudo().create({
                    'name': 'Bug Report Template',
                    'description': 'Template for bug reports',
                    'subject': 'Bug Report',
                    'ticket_type_id': ticket_type_bug.id,
                    'category_id': category_software.id,
                    'priority': '2',
                    'team_id': team_technical.id,
                    'active': True,
                })
                created_count += 1
            
            # Create additional SLA Policies
            sla_urgent = self.env['helpdesk.sla.policy'].sudo().search([('name', '=', 'Urgent SLA')], limit=1)
            if not sla_urgent:
                sla_urgent = self.env['helpdesk.sla.policy'].sudo().create({
                    'name': 'Urgent SLA',
                    'description': 'SLA policy for urgent priority tickets',
                    'response_time': 1.0,
                    'resolution_time': 4.0,
                    'priority_selection': '3',
                    'active': True,
                })
                created_count += 1
            
            # Create additional SLA Escalation Rules
            sla_escalation2 = self.env['helpdesk.sla.escalation.rule'].sudo().search([('name', '=', 'Urgent Escalation')], limit=1)
            if not sla_escalation2:
                sla_escalation2 = self.env['helpdesk.sla.escalation.rule'].sudo().create({
                    'name': 'Urgent Escalation',
                    'sla_policy_id': sla_urgent.id,
                    'trigger_type': 'resolution_time',
                    'trigger_percentage': 75.0,
                    'action_type': 'notify',
                    'notify_team_id': team_technical.id,
                    'active': True,
                })
                created_count += 1
            
            # Create additional Auto Link Rules
            auto_link_rule2 = self.env['helpdesk.auto.link.rule'].sudo().search([('name', '=', 'Auto Link by Name')], limit=1)
            if not auto_link_rule2:
                auto_link_rule2 = self.env['helpdesk.auto.link.rule'].sudo().create({
                    'name': 'Auto Link by Name',
                    'description': 'Automatically link tickets to partner records by name',
                    'target_model': 'res.partner',
                    'pattern_type': 'contains',
                    'pattern': 'Acme Corporation',
                    'search_field': 'name',
                    'active': True,
                })
                created_count += 1
            
            # Create additional Notification Schedules
            if tickets and notif_template2:
                notif_schedule2 = self.env['helpdesk.notification.schedule'].sudo().search([
                    ('ticket_id', '=', tickets[0].id),
                    ('template_id', '=', notif_template2.id)
                ], limit=1)
                if not notif_schedule2:
                    notif_schedule2 = self.env['helpdesk.notification.schedule'].sudo().create({
                        'ticket_id': tickets[0].id,
                        'template_id': notif_template2.id,
                        'scheduled_date': datetime.now() + timedelta(hours=48),
                        'status': 'pending',
                    })
                    created_count += 1
            
            # Create additional Notification History
            if tickets and notif_template2:
                notif_history2 = self.env['helpdesk.notification.history'].sudo().search([
                    ('ticket_id', '=', tickets[0].id),
                    ('template_id', '=', notif_template2.id)
                ], limit=1)
                if not notif_history2:
                    notif_history2 = self.env['helpdesk.notification.history'].sudo().create({
                        'ticket_id': tickets[0].id,
                        'template_id': notif_template2.id,
                        'notification_type': 'ticket_resolved',
                        'notification_channel': 'email',
                        'recipient_count': 1,
                        'sent_date': datetime.now() - timedelta(hours=1),
                        'status': 'sent',
                    })
                    created_count += 1
            
            # Create additional Model Links
            if tickets and partner2:
                model_link2 = self.env['helpdesk.ticket.model.link'].sudo().search([
                    ('ticket_id', '=', tickets[1].id if len(tickets) > 1 else tickets[0].id),
                    ('model_name', '=', 'res.partner'),
                    ('res_id', '=', partner2.id)
                ], limit=1)
                if not model_link2:
                    model_link2 = self.env['helpdesk.ticket.model.link'].sudo().create({
                        'ticket_id': tickets[1].id if len(tickets) > 1 else tickets[0].id,
                        'model_name': 'res.partner',
                        'res_id': partner2.id,
                    })
                    created_count += 1
            
            # Create additional Model Link Access Logs
            if model_link2:
                access_log2 = self.env['helpdesk.model.link.access.log'].sudo().search([
                    ('link_id', '=', model_link2.id),
                    ('user_id', '=', current_user.id)
                ], limit=1)
                if not access_log2:
                    access_log2 = self.env['helpdesk.model.link.access.log'].sudo().create({
                        'link_id': model_link2.id,
                        'user_id': current_user.id,
                        'access_date': datetime.now() - timedelta(hours=1),
                        'access_type': 'edit',
                    })
                    created_count += 1
            
            # Create additional Escalation Logs
            if tickets and escalation_rule2:
                escalation_log2 = self.env['helpdesk.escalation.log'].sudo().search([
                    ('ticket_id', '=', tickets[1].id if len(tickets) > 1 else tickets[0].id),
                    ('rule_id', '=', escalation_rule2.id)
                ], limit=1)
                if not escalation_log2:
                    escalation_log2 = self.env['helpdesk.escalation.log'].sudo().create({
                        'ticket_id': tickets[1].id if len(tickets) > 1 else tickets[0].id,
                        'rule_id': escalation_rule2.id,
                        'escalation_level': 1,
                        'escalation_date': datetime.now() - timedelta(hours=1),
                    })
                    created_count += 1
            
            # Create additional Workflow Execution Logs
            if tickets and workflow_rule2:
                workflow_log2 = self.env['helpdesk.workflow.execution.log'].sudo().search([
                    ('ticket_id', '=', tickets[1].id if len(tickets) > 1 else tickets[0].id),
                    ('rule_id', '=', workflow_rule2.id)
                ], limit=1)
                if not workflow_log2:
                    trigger_map = {
                        'on_create': 'create',
                        'on_update': 'write',
                        'on_status_change': 'state_change',
                        'on_field_change': 'field_change',
                    }
                    trigger_type = trigger_map.get(workflow_rule2.trigger, 'create')
                    workflow_log2 = self.env['helpdesk.workflow.execution.log'].sudo().create({
                        'ticket_id': tickets[1].id if len(tickets) > 1 else tickets[0].id,
                        'rule_id': workflow_rule2.id,
                        'trigger_type': trigger_type,
                        'execution_date': datetime.now() - timedelta(hours=1),
                        'status': 'success',
                    })
                    created_count += 1
            
            # Create additional Reminders
            if tickets and reminder_rule2:
                reminder2 = self.env['helpdesk.reminder'].sudo().search([
                    ('ticket_id', '=', tickets[1].id if len(tickets) > 1 else tickets[0].id),
                    ('reminder_rule_id', '=', reminder_rule2.id)
                ], limit=1)
                if not reminder2:
                    reminder2 = self.env['helpdesk.reminder'].sudo().create({
                        'ticket_id': tickets[1].id if len(tickets) > 1 else tickets[0].id,
                        'reminder_rule_id': reminder_rule2.id,
                        'user_id': current_user.id,
                        'reminder_date': datetime.now() + timedelta(days=3),
                        'status': 'pending',
                    })
                    created_count += 1
            
            # Create additional Ticket Status History
            if tickets and len(tickets) > 1:
                status_history2 = self.env['helpdesk.ticket.status.history'].sudo().search([
                    ('ticket_id', '=', tickets[1].id)
                ], limit=1)
                if not status_history2:
                    status_history2 = self.env['helpdesk.ticket.status.history'].sudo().create({
                        'ticket_id': tickets[1].id,
                        'old_state': 'new',
                        'new_state': tickets[1].state,
                        'user_id': current_user.id,
                        'change_date': datetime.now() - timedelta(hours=2),
                    })
                    created_count += 1
            
            # Create additional Ticket Assignment History
            if tickets and len(tickets) > 1:
                assign_history2 = self.env['helpdesk.ticket.assignment.history'].sudo().search([
                    ('ticket_id', '=', tickets[1].id)
                ], limit=1)
                if not assign_history2:
                    assign_history2 = self.env['helpdesk.ticket.assignment.history'].sudo().create({
                        'ticket_id': tickets[1].id,
                        'old_user_id': False,
                        'new_user_id': current_user.id,
                        'assigned_by_id': current_user.id,
                        'assignment_date': datetime.now() - timedelta(hours=2),
                        'assignment_method': 'manual',
                    })
                    created_count += 1
            
            # ==================== Ensure Minimum 5 Records Per Model ====================
            
            # Add more Partners (currently 3, need 2 more to reach 5)
            partner4 = self.env['res.partner'].sudo().search([('email', '=', 'support@innovatecorp.com')], limit=1)
            if not partner4:
                partner4 = self.env['res.partner'].sudo().create({
                    'name': 'Innovate Corp',
                    'email': 'support@innovatecorp.com',
                    'phone': '+1-555-0104',
                })
                created_count += 1
            
            partner5 = self.env['res.partner'].sudo().search([('email', '=', 'help@megatech.com')], limit=1)
            if not partner5:
                partner5 = self.env['res.partner'].sudo().create({
                    'name': 'MegaTech Solutions',
                    'email': 'help@megatech.com',
                    'phone': '+1-555-0105',
                })
                created_count += 1
            
            # Add more Teams (currently 3, need 2 more to reach 5)
            team_quality = self.env['helpdesk.team'].sudo().search([('name', '=', 'Quality Assurance')], limit=1)
            if not team_quality:
                team_quality = self.env['helpdesk.team'].sudo().create({
                    'name': 'Quality Assurance',
                    'description': 'QA testing and quality control',
                    'active': True,
                })
                created_count += 1
            
            team_marketing = self.env['helpdesk.team'].sudo().search([('name', '=', 'Marketing Support')], limit=1)
            if not team_marketing:
                team_marketing = self.env['helpdesk.team'].sudo().create({
                    'name': 'Marketing Support',
                    'description': 'Marketing inquiries and campaign support',
                    'active': True,
                })
                created_count += 1
            
            # Add more Categories (currently 4, need 1 more to reach 5)
            category_security = self.env['helpdesk.category'].sudo().search([('name', '=', 'Security & Access')], limit=1)
            if not category_security:
                category_security = self.env['helpdesk.category'].sudo().create({
                    'name': 'Security & Access',
                    'description': 'Security issues, access control, and permissions',
                    'color': 5,
                    'sequence': 50,
                    'default_priority': '2',
                })
                created_count += 1
            
            # Add more Tags (currently 4, need 1 more to reach 5)
            tag_security = self.env['helpdesk.tag'].sudo().search([('name', '=', 'Security')], limit=1)
            if not tag_security:
                tag_security = self.env['helpdesk.tag'].sudo().create({
                    'name': 'Security',
                    'color': 5,
                    'sequence': 5,
                })
                created_count += 1
            
            # Add more Ticket Types (currently 4, need 1 more to reach 5)
            ticket_type_security = self.env['helpdesk.ticket.type'].sudo().search([('name', '=', 'Security Incident')], limit=1)
            if not ticket_type_security:
                ticket_type_security = self.env['helpdesk.ticket.type'].sudo().create({
                    'name': 'Security Incident',
                    'description': 'Security-related incidents and breaches.',
                    'active': True,
                    'default_priority': '3',
                })
                created_count += 1
            
            # Add more Knowledge Articles (currently 2, need 3 more to reach 5)
            kb_article3 = self.env['helpdesk.knowledge.article'].sudo().search([('name', '=', 'Network Configuration Guide')], limit=1)
            if not kb_article3:
                kb_article3 = self.env['helpdesk.knowledge.article'].sudo().create({
                    'name': 'Network Configuration Guide',
                    'content': '<h2>Network Setup</h2><p>Configure your network settings, check firewall rules, and verify connectivity.</p>',
                    'category_id': category_network.id,
                    'active': True,
                })
                created_count += 1
            
            kb_article4 = self.env['helpdesk.knowledge.article'].sudo().search([('name', '=', 'Account Security Best Practices')], limit=1)
            if not kb_article4:
                kb_article4 = self.env['helpdesk.knowledge.article'].sudo().create({
                    'name': 'Account Security Best Practices',
                    'content': '<h2>Security Tips</h2><p>Use strong passwords, enable two-factor authentication, and review account access regularly.</p>',
                    'category_id': category_security.id,
                    'active': True,
                })
                created_count += 1
            
            kb_article5 = self.env['helpdesk.knowledge.article'].sudo().search([('name', '=', 'Software Installation Guide')], limit=1)
            if not kb_article5:
                kb_article5 = self.env['helpdesk.knowledge.article'].sudo().create({
                    'name': 'Software Installation Guide',
                    'content': '<h2>Installation Steps</h2><p>Download the installer, run as administrator, follow the setup wizard, and restart your computer.</p>',
                    'category_id': category_software.id,
                    'active': True,
                })
                created_count += 1
            
            # Add more Call Logs (currently 3, need 2 more to reach 5)
            call_log4 = self.env['helpdesk.call.log'].sudo().create({
                'call_date': datetime.now() - timedelta(hours=12),
                'call_end_date': datetime.now() - timedelta(hours=11, minutes=45),
                'direction': 'inbound',
                'phone_number': '+1-555-1004',
                'partner_id': partner4.id,
                'contact_name': 'Alice Brown',
                'subject': 'Product inquiry',
                'description': 'Customer calling about product features.',
                'call_outcome': 'resolved',
                'agent_id': current_user.id,
                'state': 'completed',
            })
            created_count += 1
            
            call_log5 = self.env['helpdesk.call.log'].sudo().create({
                'call_date': datetime.now() - timedelta(days=2),
                'call_end_date': (datetime.now() - timedelta(days=2)) + timedelta(minutes=15),
                'direction': 'outbound',
                'phone_number': '+1-555-1005',
                'partner_id': partner5.id,
                'contact_name': 'Charlie Davis',
                'subject': 'Follow-up call',
                'description': 'Follow-up on previous ticket resolution.',
                'call_outcome': 'resolved',
                'agent_id': current_user.id,
                'state': 'completed',
            })
            created_count += 1
            
            # Add more SLA Policies (currently 3, need 2 more to reach 5)
            sla_low = self.env['helpdesk.sla.policy'].sudo().search([('name', '=', 'Low Priority SLA')], limit=1)
            if not sla_low:
                sla_low = self.env['helpdesk.sla.policy'].sudo().create({
                    'name': 'Low Priority SLA',
                    'description': 'SLA policy for low priority tickets',
                    'response_time': 48.0,
                    'resolution_time': 120.0,
                    'priority_selection': '0',
                    'active': True,
                })
                created_count += 1
            
            sla_medium = self.env['helpdesk.sla.policy'].sudo().search([('name', '=', 'Medium Priority SLA')], limit=1)
            if not sla_medium:
                sla_medium = self.env['helpdesk.sla.policy'].sudo().create({
                    'name': 'Medium Priority SLA',
                    'description': 'SLA policy for medium priority tickets',
                    'response_time': 12.0,
                    'resolution_time': 48.0,
                    'priority_selection': '1',
                    'active': True,
                })
                created_count += 1
            
            # Add more SLA Escalation Rules (currently 2, need 3 more to reach 5)
            sla_escalation3 = self.env['helpdesk.sla.escalation.rule'].sudo().search([('name', '=', 'Low Priority Escalation')], limit=1)
            if not sla_escalation3:
                sla_escalation3 = self.env['helpdesk.sla.escalation.rule'].sudo().create({
                    'name': 'Low Priority Escalation',
                    'sla_policy_id': sla_low.id,
                    'trigger_type': 'resolution_time',
                    'trigger_percentage': 90.0,
                    'action_type': 'notify',
                    'notify_team_id': team_technical.id,
                    'active': True,
                })
                created_count += 1
            
            sla_escalation4 = self.env['helpdesk.sla.escalation.rule'].sudo().search([('name', '=', 'Medium Priority Escalation')], limit=1)
            if not sla_escalation4:
                sla_escalation4 = self.env['helpdesk.sla.escalation.rule'].sudo().create({
                    'name': 'Medium Priority Escalation',
                    'sla_policy_id': sla_medium.id,
                    'trigger_type': 'both',
                    'trigger_percentage': 85.0,
                    'action_type': 'notify',
                    'notify_team_id': team_technical.id,
                    'active': True,
                })
                created_count += 1
            
            sla_escalation5 = self.env['helpdesk.sla.escalation.rule'].sudo().search([('name', '=', 'Priority Escalation')], limit=1)
            if not sla_escalation5:
                sla_escalation5 = self.env['helpdesk.sla.escalation.rule'].sudo().create({
                    'name': 'Priority Escalation',
                    'sla_policy_id': sla_priority.id,
                    'trigger_type': 'response_time',
                    'trigger_percentage': 70.0,
                    'action_type': 'notify',
                    'notify_team_id': team_technical.id,
                    'active': True,
                })
                created_count += 1
            
            # Add more Workflow Rules (currently 2, need 3 more to reach 5)
            workflow_rule3 = self.env['helpdesk.workflow.rule'].sudo().search([('name', '=', 'Auto Assign on Status Change')], limit=1)
            if not workflow_rule3:
                workflow_rule3 = self.env['helpdesk.workflow.rule'].sudo().create({
                    'name': 'Auto Assign on Status Change',
                    'description': 'Automatically assign tickets when status changes to in_progress',
                    'trigger': 'on_status_change',
                    'action_type': 'assign',
                    'action_assign_team_id': team_technical.id,
                    'active': True,
                })
                created_count += 1
            
            workflow_rule4 = self.env['helpdesk.workflow.rule'].sudo().search([('name', '=', 'Notify on Update')], limit=1)
            if not workflow_rule4:
                workflow_rule4 = self.env['helpdesk.workflow.rule'].sudo().create({
                    'name': 'Notify on Update',
                    'description': 'Send notification when ticket is updated',
                    'trigger': 'on_update',
                    'action_type': 'notify',
                    'active': True,
                })
                created_count += 1
            
            workflow_rule5 = self.env['helpdesk.workflow.rule'].sudo().search([('name', '=', 'Set Priority on Create')], limit=1)
            if not workflow_rule5:
                workflow_rule5 = self.env['helpdesk.workflow.rule'].sudo().create({
                    'name': 'Set Priority on Create',
                    'description': 'Set default priority based on category',
                    'trigger': 'on_create',
                    'action_type': 'set_field',
                    'action_set_field_name': 'priority',
                    'action_set_field_value': '1',
                    'active': True,
                })
                created_count += 1
            
            # Add more Ticket Templates (currently 2, need 3 more to reach 5)
            ticket_template3 = self.env['helpdesk.ticket.template'].sudo().search([('name', '=', 'Network Issue Template')], limit=1)
            if not ticket_template3:
                ticket_template3 = self.env['helpdesk.ticket.template'].sudo().create({
                    'name': 'Network Issue Template',
                    'description': 'Template for network connectivity issues',
                    'subject': 'Network Connectivity Issue',
                    'ticket_type_id': ticket_type_incident.id,
                    'category_id': category_network.id,
                    'priority': '2',
                    'team_id': team_technical.id,
                    'active': True,
                })
                created_count += 1
            
            ticket_template4 = self.env['helpdesk.ticket.template'].sudo().search([('name', '=', 'Security Incident Template')], limit=1)
            if not ticket_template4:
                ticket_template4 = self.env['helpdesk.ticket.template'].sudo().create({
                    'name': 'Security Incident Template',
                    'description': 'Template for security incidents',
                    'subject': 'Security Incident Report',
                    'ticket_type_id': ticket_type_security.id,
                    'category_id': category_security.id,
                    'priority': '3',
                    'team_id': team_technical.id,
                    'active': True,
                })
                created_count += 1
            
            ticket_template5 = self.env['helpdesk.ticket.template'].sudo().search([('name', '=', 'General Inquiry Template')], limit=1)
            if not ticket_template5:
                ticket_template5 = self.env['helpdesk.ticket.template'].sudo().create({
                    'name': 'General Inquiry Template',
                    'description': 'Template for general inquiries',
                    'subject': 'General Inquiry',
                    'ticket_type_id': ticket_type_request.id,
                    'priority': '1',
                    'team_id': team_sales.id,
                    'active': True,
                })
                created_count += 1
            
            # Add more Escalation Rules (currently 2, need 3 more to reach 5)
            escalation_rule3 = self.env['helpdesk.escalation.rule'].sudo().search([('name', '=', 'Medium Priority Escalation')], limit=1)
            if not escalation_rule3:
                escalation_rule3 = self.env['helpdesk.escalation.rule'].sudo().create({
                    'name': 'Medium Priority Escalation',
                    'description': 'Escalate medium priority tickets after 6 hours',
                    'trigger_type': 'time_based',
                    'time_trigger_type': 'since_creation',
                    'time_trigger_hours': 6.0,
                    'priority_filter': '1',
                    'action_type': 'notify',
                    'action_notify_team_id': team_technical.id,
                    'active': True,
                })
                created_count += 1
            
            escalation_rule4 = self.env['helpdesk.escalation.rule'].sudo().search([('name', '=', 'Low Priority Escalation')], limit=1)
            if not escalation_rule4:
                escalation_rule4 = self.env['helpdesk.escalation.rule'].sudo().create({
                    'name': 'Low Priority Escalation',
                    'description': 'Escalate low priority tickets after 24 hours',
                    'trigger_type': 'time_based',
                    'time_trigger_type': 'since_creation',
                    'time_trigger_hours': 24.0,
                    'priority_filter': '0',
                    'action_type': 'notify',
                    'action_notify_team_id': team_technical.id,
                    'active': True,
                })
                created_count += 1
            
            escalation_rule5 = self.env['helpdesk.escalation.rule'].sudo().search([('name', '=', 'No Response Escalation')], limit=1)
            if not escalation_rule5:
                escalation_rule5 = self.env['helpdesk.escalation.rule'].sudo().create({
                    'name': 'No Response Escalation',
                    'description': 'Escalate tickets with no response after 12 hours',
                    'trigger_type': 'time_based',
                    'time_trigger_type': 'since_update',
                    'time_trigger_hours': 12.0,
                    'action_type': 'notify',
                    'action_notify_team_id': team_technical.id,
                    'active': True,
                })
                created_count += 1
            
            # Add more Notification Templates (currently 2, need 3 more to reach 5)
            notif_template3 = self.env['helpdesk.notification.template'].sudo().search([('name', '=', 'Ticket Assigned Notification')], limit=1)
            if not notif_template3:
                notif_template3 = self.env['helpdesk.notification.template'].sudo().create({
                    'name': 'Ticket Assigned Notification',
                    'description': 'Notification sent when ticket is assigned',
                    'notification_type': 'ticket_assigned',
                    'notification_channel': 'email',
                    'subject': 'Ticket Assigned: {{ticket.ticket_number}}',
                    'body_html': '<p>You have been assigned a ticket. Ticket Number: {{ticket.ticket_number}}</p>',
                    'recipient_type': 'assigned_user',
                    'active': True,
                })
                created_count += 1
            
            notif_template4 = self.env['helpdesk.notification.template'].sudo().search([('name', '=', 'Ticket Updated Notification')], limit=1)
            if not notif_template4:
                notif_template4 = self.env['helpdesk.notification.template'].sudo().create({
                    'name': 'Ticket Updated Notification',
                    'description': 'Notification sent when ticket is updated',
                    'notification_type': 'ticket_updated',
                    'notification_channel': 'email',
                    'subject': 'Ticket Updated: {{ticket.ticket_number}}',
                    'body_html': '<p>Your ticket has been updated. Ticket Number: {{ticket.ticket_number}}</p>',
                    'recipient_type': 'customer',
                    'active': True,
                })
                created_count += 1
            
            notif_template5 = self.env['helpdesk.notification.template'].sudo().search([('name', '=', 'Ticket Closed Notification')], limit=1)
            if not notif_template5:
                notif_template5 = self.env['helpdesk.notification.template'].sudo().create({
                    'name': 'Ticket Closed Notification',
                    'description': 'Notification sent when ticket is closed',
                    'notification_type': 'ticket_closed',
                    'notification_channel': 'email',
                    'subject': 'Ticket Closed: {{ticket.ticket_number}}',
                    'body_html': '<p>Your ticket has been closed. Ticket Number: {{ticket.ticket_number}}</p>',
                    'recipient_type': 'customer',
                    'active': True,
                })
                created_count += 1
            
            # Add more Notification Preferences (currently 2, need 3 more to reach 5)
            notif_pref3 = self.env['helpdesk.notification.preference'].sudo().search([
                ('user_id', '=', current_user.id),
                ('notification_type', '=', 'ticket_assigned')
            ], limit=1)
            if not notif_pref3:
                notif_pref3 = self.env['helpdesk.notification.preference'].sudo().create({
                    'user_id': current_user.id,
                    'notification_type': 'ticket_assigned',
                    'email_enabled': True,
                    'in_app_enabled': True,
                })
                created_count += 1
            
            notif_pref4 = self.env['helpdesk.notification.preference'].sudo().search([
                ('user_id', '=', current_user.id),
                ('notification_type', '=', 'ticket_updated')
            ], limit=1)
            if not notif_pref4:
                notif_pref4 = self.env['helpdesk.notification.preference'].sudo().create({
                    'user_id': current_user.id,
                    'notification_type': 'ticket_updated',
                    'email_enabled': False,
                    'in_app_enabled': True,
                })
                created_count += 1
            
            notif_pref5 = self.env['helpdesk.notification.preference'].sudo().search([
                ('user_id', '=', current_user.id),
                ('notification_type', '=', 'ticket_closed')
            ], limit=1)
            if not notif_pref5:
                notif_pref5 = self.env['helpdesk.notification.preference'].sudo().create({
                    'user_id': current_user.id,
                    'notification_type': 'ticket_closed',
                    'email_enabled': True,
                    'in_app_enabled': False,
                })
                created_count += 1
            
            # Add more Reminder Rules (currently 2, need 3 more to reach 5)
            reminder_rule3 = self.env['helpdesk.reminder.rule'].sudo().search([('name', '=', 'Response Reminder')], limit=1)
            if not reminder_rule3:
                reminder_rule3 = self.env['helpdesk.reminder.rule'].sudo().create({
                    'name': 'Response Reminder',
                    'description': 'Remind agents to respond to tickets',
                    'trigger_type': 'time_based',
                    'time_trigger_type': 'since_update',
                    'time_trigger_hours': 24.0,
                    'reminder_user_type': 'assigned_user',
                    'active': True,
                })
                created_count += 1
            
            reminder_rule4 = self.env['helpdesk.reminder.rule'].sudo().search([('name', '=', 'SLA Reminder')], limit=1)
            if not reminder_rule4:
                reminder_rule4 = self.env['helpdesk.reminder.rule'].sudo().create({
                    'name': 'SLA Reminder',
                    'description': 'Remind agents about approaching SLA deadlines',
                    'trigger_type': 'time_based',
                    'time_trigger_type': 'since_creation',
                    'time_trigger_hours': 20.0,
                    'reminder_user_type': 'assigned_user',
                    'active': True,
                })
                created_count += 1
            
            reminder_rule5 = self.env['helpdesk.reminder.rule'].sudo().search([('name', '=', 'Weekly Review Reminder')], limit=1)
            if not reminder_rule5:
                reminder_rule5 = self.env['helpdesk.reminder.rule'].sudo().create({
                    'name': 'Weekly Review Reminder',
                    'description': 'Weekly reminder to review open tickets',
                    'trigger_type': 'time_based',
                    'time_trigger_type': 'since_creation',
                    'time_trigger_hours': 168.0,  # 7 days
                    'reminder_user_type': 'team_leader',
                    'active': True,
                })
                created_count += 1
            
            # Add more Reminders (currently 2, need 3 more to reach 5)
            if tickets and len(tickets) > 2 and reminder_rule3:
                reminder3 = self.env['helpdesk.reminder'].sudo().search([
                    ('ticket_id', '=', tickets[2].id if len(tickets) > 2 else tickets[0].id),
                    ('reminder_rule_id', '=', reminder_rule3.id)
                ], limit=1)
                if not reminder3:
                    reminder3 = self.env['helpdesk.reminder'].sudo().create({
                        'ticket_id': tickets[2].id if len(tickets) > 2 else tickets[0].id,
                        'reminder_rule_id': reminder_rule3.id,
                        'user_id': current_user.id,
                        'reminder_date': datetime.now() + timedelta(hours=24),
                        'status': 'pending',
                    })
                    created_count += 1
            
            if tickets and len(tickets) > 3 and reminder_rule4:
                reminder4 = self.env['helpdesk.reminder'].sudo().search([
                    ('ticket_id', '=', tickets[3].id if len(tickets) > 3 else tickets[0].id),
                    ('reminder_rule_id', '=', reminder_rule4.id)
                ], limit=1)
                if not reminder4:
                    reminder4 = self.env['helpdesk.reminder'].sudo().create({
                        'ticket_id': tickets[3].id if len(tickets) > 3 else tickets[0].id,
                        'reminder_rule_id': reminder_rule4.id,
                        'user_id': current_user.id,
                        'reminder_date': datetime.now() + timedelta(hours=20),
                        'status': 'pending',
                    })
                    created_count += 1
            
            if tickets and reminder_rule5:
                reminder5 = self.env['helpdesk.reminder'].sudo().search([
                    ('ticket_id', '=', tickets[0].id),
                    ('reminder_rule_id', '=', reminder_rule5.id)
                ], limit=1)
                if not reminder5:
                    reminder5 = self.env['helpdesk.reminder'].sudo().create({
                        'ticket_id': tickets[0].id,
                        'reminder_rule_id': reminder_rule5.id,
                        'user_id': current_user.id,
                        'reminder_date': datetime.now() + timedelta(days=7),
                        'status': 'pending',
                    })
                    created_count += 1
            
            # Add more Social Media Platforms (currently 2, need 3 more to reach 5)
            social_platform_ig = self.env['helpdesk.social.media.platform'].sudo().search([('name', '=', 'Instagram Demo')], limit=1)
            if not social_platform_ig:
                social_platform_ig = self.env['helpdesk.social.media.platform'].sudo().create({
                    'name': 'Instagram Demo',
                    'platform_type': 'instagram',
                    'page_id': '@demo_instagram',
                    'active': True,
                    'monitor_posts': True,
                    'monitor_messages': True,
                    'monitor_comments': True,
                    'default_team_id': team_marketing.id,
                    'default_priority': '1',
                })
                created_count += 1
            
            social_platform_li = self.env['helpdesk.social.media.platform'].sudo().search([('name', '=', 'LinkedIn Demo')], limit=1)
            if not social_platform_li:
                social_platform_li = self.env['helpdesk.social.media.platform'].sudo().create({
                    'name': 'LinkedIn Demo',
                    'platform_type': 'linkedin',
                    'page_id': 'demo_linkedin_company',
                    'active': True,
                    'monitor_posts': True,
                    'monitor_messages': False,
                    'monitor_comments': True,
                    'default_team_id': team_sales.id,
                    'default_priority': '1',
                })
                created_count += 1
            
            social_platform_other = self.env['helpdesk.social.media.platform'].sudo().search([('name', '=', 'Other Platform Demo')], limit=1)
            if not social_platform_other:
                social_platform_other = self.env['helpdesk.social.media.platform'].sudo().create({
                    'name': 'Other Platform Demo',
                    'platform_type': 'other',
                    'page_id': 'demo_other_platform',
                    'active': True,
                    'monitor_posts': False,
                    'monitor_messages': True,
                    'monitor_comments': False,
                    'default_team_id': team_sales.id,
                    'default_priority': '0',
                })
                created_count += 1
            
            # Add more Social Media Posts (currently 2, need 3 more to reach 5)
            if social_platform_ig:
                social_post3 = self.env['helpdesk.social.media.post'].sudo().search([
                    ('platform_id', '=', social_platform_ig.id),
                    ('post_id', '=', 'ig_demo_001')
                ], limit=1)
                if not social_post3:
                    social_post3 = self.env['helpdesk.social.media.post'].sudo().create({
                        'platform_id': social_platform_ig.id,
                        'platform_type': 'instagram',
                        'post_type': 'comment',
                        'post_id': 'ig_demo_001',
                        'content': 'Love your product! Need help with setup.',
                        'post_date': datetime.now() - timedelta(hours=3),
                        'author_name': 'Instagram User',
                        'author_username': '@instauser',
                        'state': 'new',
                    })
                    created_count += 1
            
            if social_platform_li:
                social_post4 = self.env['helpdesk.social.media.post'].sudo().search([
                    ('platform_id', '=', social_platform_li.id),
                    ('post_id', '=', 'li_demo_001')
                ], limit=1)
                if not social_post4:
                    social_post4 = self.env['helpdesk.social.media.post'].sudo().create({
                        'platform_id': social_platform_li.id,
                        'platform_type': 'linkedin',
                        'post_type': 'message',
                        'post_id': 'li_demo_001',
                        'content': 'Interested in your enterprise solution. Can we schedule a demo?',
                        'post_date': datetime.now() - timedelta(hours=4),
                        'author_name': 'LinkedIn Professional',
                        'author_username': 'linkedin.professional',
                        'state': 'new',
                    })
                    created_count += 1
            
            if social_platform_other:
                social_post5 = self.env['helpdesk.social.media.post'].sudo().search([
                    ('platform_id', '=', social_platform_other.id),
                    ('post_id', '=', 'other_demo_001')
                ], limit=1)
                if not social_post5:
                    social_post5 = self.env['helpdesk.social.media.post'].sudo().create({
                        'platform_id': social_platform_other.id,
                        'platform_type': 'other',
                        'post_type': 'message',
                        'post_id': 'other_demo_001',
                        'content': 'General inquiry about services.',
                        'post_date': datetime.now() - timedelta(hours=5),
                        'author_name': 'Platform User',
                        'author_username': 'platform.user',
                        'state': 'new',
                    })
                    created_count += 1
            
            # Add more Ticket Model Links (currently 2, need 3 more to reach 5)
            if tickets and len(tickets) > 2 and partner3:
                model_link3 = self.env['helpdesk.ticket.model.link'].sudo().search([
                    ('ticket_id', '=', tickets[2].id if len(tickets) > 2 else tickets[0].id),
                    ('model_name', '=', 'res.partner'),
                    ('res_id', '=', partner3.id)
                ], limit=1)
                if not model_link3:
                    model_link3 = self.env['helpdesk.ticket.model.link'].sudo().create({
                        'ticket_id': tickets[2].id if len(tickets) > 2 else tickets[0].id,
                        'model_name': 'res.partner',
                        'res_id': partner3.id,
                    })
                    created_count += 1
            
            if tickets and len(tickets) > 3 and partner4:
                model_link4 = self.env['helpdesk.ticket.model.link'].sudo().search([
                    ('ticket_id', '=', tickets[3].id if len(tickets) > 3 else tickets[0].id),
                    ('model_name', '=', 'res.partner'),
                    ('res_id', '=', partner4.id)
                ], limit=1)
                if not model_link4:
                    model_link4 = self.env['helpdesk.ticket.model.link'].sudo().create({
                        'ticket_id': tickets[3].id if len(tickets) > 3 else tickets[0].id,
                        'model_name': 'res.partner',
                        'res_id': partner4.id,
                    })
                    created_count += 1
            
            if tickets and len(tickets) > 4 and partner5:
                model_link5 = self.env['helpdesk.ticket.model.link'].sudo().search([
                    ('ticket_id', '=', tickets[4].id if len(tickets) > 4 else tickets[0].id),
                    ('model_name', '=', 'res.partner'),
                    ('res_id', '=', partner5.id)
                ], limit=1)
                if not model_link5:
                    model_link5 = self.env['helpdesk.ticket.model.link'].sudo().create({
                        'ticket_id': tickets[4].id if len(tickets) > 4 else tickets[0].id,
                        'model_name': 'res.partner',
                        'res_id': partner5.id,
                    })
                    created_count += 1
            
            # Add more Auto Link Rules (currently 2, need 3 more to reach 5)
            auto_link_rule3 = self.env['helpdesk.auto.link.rule'].sudo().search([('name', '=', 'Auto Link by Phone')], limit=1)
            if not auto_link_rule3:
                auto_link_rule3 = self.env['helpdesk.auto.link.rule'].sudo().create({
                    'name': 'Auto Link by Phone',
                    'description': 'Automatically link tickets to partner records by phone number',
                    'target_model': 'res.partner',
                    'pattern_type': 'prefix',
                    'pattern': '+1-555',
                    'search_field': 'phone',
                    'active': True,
                })
                created_count += 1
            
            auto_link_rule4 = self.env['helpdesk.auto.link.rule'].sudo().search([('name', '=', 'Auto Link by Company Name')], limit=1)
            if not auto_link_rule4:
                auto_link_rule4 = self.env['helpdesk.auto.link.rule'].sudo().create({
                    'name': 'Auto Link by Company Name',
                    'description': 'Automatically link tickets to partner records by company name',
                    'target_model': 'res.partner',
                    'pattern_type': 'contains',
                    'pattern': 'Corp',
                    'search_field': 'name',
                    'active': True,
                })
                created_count += 1
            
            auto_link_rule5 = self.env['helpdesk.auto.link.rule'].sudo().search([('name', '=', 'Auto Link by Domain')], limit=1)
            if not auto_link_rule5:
                auto_link_rule5 = self.env['helpdesk.auto.link.rule'].sudo().create({
                    'name': 'Auto Link by Domain',
                    'description': 'Automatically link tickets to partner records by email domain',
                    'target_model': 'res.partner',
                    'pattern_type': 'contains',
                    'pattern': '@',
                    'search_field': 'email',
                    'active': True,
                })
                created_count += 1
            
            # Add more Ticket Status History (currently 2, need 3 more to reach 5)
            if tickets and len(tickets) > 2:
                status_history3 = self.env['helpdesk.ticket.status.history'].sudo().search([
                    ('ticket_id', '=', tickets[2].id)
                ], limit=1)
                if not status_history3:
                    status_history3 = self.env['helpdesk.ticket.status.history'].sudo().create({
                        'ticket_id': tickets[2].id,
                        'old_state': 'new',
                        'new_state': tickets[2].state if tickets[2].state else 'assigned',
                        'user_id': current_user.id,
                        'change_date': datetime.now() - timedelta(hours=3),
                    })
                    created_count += 1
            
            if tickets and len(tickets) > 3:
                status_history4 = self.env['helpdesk.ticket.status.history'].sudo().search([
                    ('ticket_id', '=', tickets[3].id)
                ], limit=1)
                if not status_history4:
                    status_history4 = self.env['helpdesk.ticket.status.history'].sudo().create({
                        'ticket_id': tickets[3].id,
                        'old_state': 'new',
                        'new_state': tickets[3].state if tickets[3].state else 'in_progress',
                        'user_id': current_user.id,
                        'change_date': datetime.now() - timedelta(hours=4),
                    })
                    created_count += 1
            
            if tickets and len(tickets) > 4:
                status_history5 = self.env['helpdesk.ticket.status.history'].sudo().search([
                    ('ticket_id', '=', tickets[4].id)
                ], limit=1)
                if not status_history5:
                    status_history5 = self.env['helpdesk.ticket.status.history'].sudo().create({
                        'ticket_id': tickets[4].id,
                        'old_state': 'new',
                        'new_state': tickets[4].state if tickets[4].state else 'resolved',
                        'user_id': current_user.id,
                        'change_date': datetime.now() - timedelta(hours=5),
                    })
                    created_count += 1
            
            # Add more Ticket Assignment History (currently 2, need 3 more to reach 5)
            if tickets and len(tickets) > 2:
                assign_history3 = self.env['helpdesk.ticket.assignment.history'].sudo().search([
                    ('ticket_id', '=', tickets[2].id)
                ], limit=1)
                if not assign_history3:
                    assign_history3 = self.env['helpdesk.ticket.assignment.history'].sudo().create({
                        'ticket_id': tickets[2].id,
                        'old_user_id': False,
                        'new_user_id': current_user.id,
                        'assigned_by_id': current_user.id,
                        'assignment_date': datetime.now() - timedelta(hours=3),
                        'assignment_method': 'manual',
                    })
                    created_count += 1
            
            if tickets and len(tickets) > 3:
                assign_history4 = self.env['helpdesk.ticket.assignment.history'].sudo().search([
                    ('ticket_id', '=', tickets[3].id)
                ], limit=1)
                if not assign_history4:
                    assign_history4 = self.env['helpdesk.ticket.assignment.history'].sudo().create({
                        'ticket_id': tickets[3].id,
                        'old_user_id': False,
                        'new_user_id': current_user.id,
                        'assigned_by_id': current_user.id,
                        'assignment_date': datetime.now() - timedelta(hours=4),
                        'assignment_method': 'workflow',
                    })
                    created_count += 1
            
            if tickets and len(tickets) > 4:
                assign_history5 = self.env['helpdesk.ticket.assignment.history'].sudo().search([
                    ('ticket_id', '=', tickets[4].id)
                ], limit=1)
                if not assign_history5:
                    assign_history5 = self.env['helpdesk.ticket.assignment.history'].sudo().create({
                        'ticket_id': tickets[4].id,
                        'old_user_id': False,
                        'new_user_id': current_user.id,
                        'assigned_by_id': current_user.id,
                        'assignment_date': datetime.now() - timedelta(hours=5),
                        'assignment_method': 'round_robin',
                    })
                    created_count += 1
            
            # Add more Escalation Logs (currently 2, need 3 more to reach 5)
            if tickets and len(tickets) > 2 and escalation_rule3:
                escalation_log3 = self.env['helpdesk.escalation.log'].sudo().search([
                    ('ticket_id', '=', tickets[2].id if len(tickets) > 2 else tickets[0].id),
                    ('rule_id', '=', escalation_rule3.id)
                ], limit=1)
                if not escalation_log3:
                    escalation_log3 = self.env['helpdesk.escalation.log'].sudo().create({
                        'ticket_id': tickets[2].id if len(tickets) > 2 else tickets[0].id,
                        'rule_id': escalation_rule3.id,
                        'escalation_level': 1,
                        'escalation_date': datetime.now() - timedelta(hours=3),
                    })
                    created_count += 1
            
            if tickets and len(tickets) > 3 and escalation_rule4:
                escalation_log4 = self.env['helpdesk.escalation.log'].sudo().search([
                    ('ticket_id', '=', tickets[3].id if len(tickets) > 3 else tickets[0].id),
                    ('rule_id', '=', escalation_rule4.id)
                ], limit=1)
                if not escalation_log4:
                    escalation_log4 = self.env['helpdesk.escalation.log'].sudo().create({
                        'ticket_id': tickets[3].id if len(tickets) > 3 else tickets[0].id,
                        'rule_id': escalation_rule4.id,
                        'escalation_level': 1,
                        'escalation_date': datetime.now() - timedelta(hours=4),
                    })
                    created_count += 1
            
            if tickets and escalation_rule5:
                escalation_log5 = self.env['helpdesk.escalation.log'].sudo().search([
                    ('ticket_id', '=', tickets[0].id),
                    ('rule_id', '=', escalation_rule5.id)
                ], limit=1)
                if not escalation_log5:
                    escalation_log5 = self.env['helpdesk.escalation.log'].sudo().create({
                        'ticket_id': tickets[0].id,
                        'rule_id': escalation_rule5.id,
                        'escalation_level': 1,
                        'escalation_date': datetime.now() - timedelta(hours=5),
                    })
                    created_count += 1
            
            # Add more Notification History (currently 2, need 3 more to reach 5)
            if tickets and notif_template3:
                notif_history3 = self.env['helpdesk.notification.history'].sudo().search([
                    ('ticket_id', '=', tickets[0].id),
                    ('template_id', '=', notif_template3.id)
                ], limit=1)
                if not notif_history3:
                    notif_history3 = self.env['helpdesk.notification.history'].sudo().create({
                        'ticket_id': tickets[0].id,
                        'template_id': notif_template3.id,
                        'notification_type': 'ticket_assigned',
                        'notification_channel': 'email',
                        'recipient_count': 1,
                        'sent_date': datetime.now() - timedelta(hours=2),
                        'status': 'sent',
                    })
                    created_count += 1
            
            if tickets and notif_template4:
                notif_history4 = self.env['helpdesk.notification.history'].sudo().search([
                    ('ticket_id', '=', tickets[0].id),
                    ('template_id', '=', notif_template4.id)
                ], limit=1)
                if not notif_history4:
                    notif_history4 = self.env['helpdesk.notification.history'].sudo().create({
                        'ticket_id': tickets[0].id,
                        'template_id': notif_template4.id,
                        'notification_type': 'ticket_updated',
                        'notification_channel': 'email',
                        'recipient_count': 1,
                        'sent_date': datetime.now() - timedelta(hours=3),
                        'status': 'sent',
                    })
                    created_count += 1
            
            if tickets and notif_template5:
                notif_history5 = self.env['helpdesk.notification.history'].sudo().search([
                    ('ticket_id', '=', tickets[0].id),
                    ('template_id', '=', notif_template5.id)
                ], limit=1)
                if not notif_history5:
                    notif_history5 = self.env['helpdesk.notification.history'].sudo().create({
                        'ticket_id': tickets[0].id,
                        'template_id': notif_template5.id,
                        'notification_type': 'ticket_closed',
                        'notification_channel': 'email',
                        'recipient_count': 1,
                        'sent_date': datetime.now() - timedelta(hours=4),
                        'status': 'sent',
                    })
                    created_count += 1
            
            # Add more Notification Schedules (currently 2, need 3 more to reach 5)
            if tickets and notif_template3:
                notif_schedule3 = self.env['helpdesk.notification.schedule'].sudo().search([
                    ('ticket_id', '=', tickets[0].id),
                    ('template_id', '=', notif_template3.id)
                ], limit=1)
                if not notif_schedule3:
                    notif_schedule3 = self.env['helpdesk.notification.schedule'].sudo().create({
                        'ticket_id': tickets[0].id,
                        'template_id': notif_template3.id,
                        'scheduled_date': datetime.now() + timedelta(hours=12),
                        'status': 'pending',
                    })
                    created_count += 1
            
            if tickets and notif_template4:
                notif_schedule4 = self.env['helpdesk.notification.schedule'].sudo().search([
                    ('ticket_id', '=', tickets[0].id),
                    ('template_id', '=', notif_template4.id)
                ], limit=1)
                if not notif_schedule4:
                    notif_schedule4 = self.env['helpdesk.notification.schedule'].sudo().create({
                        'ticket_id': tickets[0].id,
                        'template_id': notif_template4.id,
                        'scheduled_date': datetime.now() + timedelta(hours=36),
                        'status': 'pending',
                    })
                    created_count += 1
            
            if tickets and notif_template5:
                notif_schedule5 = self.env['helpdesk.notification.schedule'].sudo().search([
                    ('ticket_id', '=', tickets[0].id),
                    ('template_id', '=', notif_template5.id)
                ], limit=1)
                if not notif_schedule5:
                    notif_schedule5 = self.env['helpdesk.notification.schedule'].sudo().create({
                        'ticket_id': tickets[0].id,
                        'template_id': notif_template5.id,
                        'scheduled_date': datetime.now() + timedelta(hours=72),
                        'status': 'pending',
                    })
                    created_count += 1
            
            # Add more Workflow Execution Logs (currently 2, need 3 more to reach 5)
            if tickets and workflow_rule3:
                workflow_log3 = self.env['helpdesk.workflow.execution.log'].sudo().search([
                    ('ticket_id', '=', tickets[0].id),
                    ('rule_id', '=', workflow_rule3.id)
                ], limit=1)
                if not workflow_log3:
                    trigger_map = {
                        'on_create': 'create',
                        'on_update': 'write',
                        'on_status_change': 'state_change',
                        'on_field_change': 'field_change',
                    }
                    trigger_type = trigger_map.get(workflow_rule3.trigger, 'state_change')
                    workflow_log3 = self.env['helpdesk.workflow.execution.log'].sudo().create({
                        'ticket_id': tickets[0].id,
                        'rule_id': workflow_rule3.id,
                        'trigger_type': trigger_type,
                        'execution_date': datetime.now() - timedelta(hours=2),
                        'status': 'success',
                    })
                    created_count += 1
            
            if tickets and workflow_rule4:
                workflow_log4 = self.env['helpdesk.workflow.execution.log'].sudo().search([
                    ('ticket_id', '=', tickets[0].id),
                    ('rule_id', '=', workflow_rule4.id)
                ], limit=1)
                if not workflow_log4:
                    trigger_map = {
                        'on_create': 'create',
                        'on_update': 'write',
                        'on_status_change': 'state_change',
                        'on_field_change': 'field_change',
                    }
                    trigger_type = trigger_map.get(workflow_rule4.trigger, 'write')
                    workflow_log4 = self.env['helpdesk.workflow.execution.log'].sudo().create({
                        'ticket_id': tickets[0].id,
                        'rule_id': workflow_rule4.id,
                        'trigger_type': trigger_type,
                        'execution_date': datetime.now() - timedelta(hours=3),
                        'status': 'success',
                    })
                    created_count += 1
            
            if tickets and workflow_rule5:
                workflow_log5 = self.env['helpdesk.workflow.execution.log'].sudo().search([
                    ('ticket_id', '=', tickets[0].id),
                    ('rule_id', '=', workflow_rule5.id)
                ], limit=1)
                if not workflow_log5:
                    trigger_map = {
                        'on_create': 'create',
                        'on_update': 'write',
                        'on_status_change': 'state_change',
                        'on_field_change': 'field_change',
                    }
                    trigger_type = trigger_map.get(workflow_rule5.trigger, 'create')
                    workflow_log5 = self.env['helpdesk.workflow.execution.log'].sudo().create({
                        'ticket_id': tickets[0].id,
                        'rule_id': workflow_rule5.id,
                        'trigger_type': trigger_type,
                        'execution_date': datetime.now() - timedelta(hours=4),
                        'status': 'success',
                    })
                    created_count += 1
            
            # Add more Model Link Access Logs (currently 2, need 3 more to reach 5)
            if model_link3:
                access_log3 = self.env['helpdesk.model.link.access.log'].sudo().search([
                    ('link_id', '=', model_link3.id),
                    ('user_id', '=', current_user.id)
                ], limit=1)
                if not access_log3:
                    access_log3 = self.env['helpdesk.model.link.access.log'].sudo().create({
                        'link_id': model_link3.id,
                        'user_id': current_user.id,
                        'access_date': datetime.now() - timedelta(hours=2),
                        'access_type': 'view',
                    })
                    created_count += 1
            
            if model_link4:
                access_log4 = self.env['helpdesk.model.link.access.log'].sudo().search([
                    ('link_id', '=', model_link4.id),
                    ('user_id', '=', current_user.id)
                ], limit=1)
                if not access_log4:
                    access_log4 = self.env['helpdesk.model.link.access.log'].sudo().create({
                        'link_id': model_link4.id,
                        'user_id': current_user.id,
                        'access_date': datetime.now() - timedelta(hours=3),
                        'access_type': 'edit',
                    })
                    created_count += 1
            
            if model_link5:
                access_log5 = self.env['helpdesk.model.link.access.log'].sudo().search([
                    ('link_id', '=', model_link5.id),
                    ('user_id', '=', current_user.id)
                ], limit=1)
                if not access_log5:
                    access_log5 = self.env['helpdesk.model.link.access.log'].sudo().create({
                        'link_id': model_link5.id,
                        'user_id': current_user.id,
                        'access_date': datetime.now() - timedelta(hours=4),
                        'access_type': 'view',
                    })
                    created_count += 1
            
            # Add more Knowledge Article Feedback (currently 2, need 3 more to reach 5)
            if kb_article3:
                kb_feedback3 = self.env['helpdesk.knowledge.article.feedback'].sudo().search([
                    ('article_id', '=', kb_article3.id),
                    ('partner_id', '=', partner3.id)
                ], limit=1)
                if not kb_feedback3:
                    kb_feedback3 = self.env['helpdesk.knowledge.article.feedback'].sudo().create({
                        'article_id': kb_article3.id,
                        'rating': '4',
                        'feedback': 'Clear and helpful guide!',
                        'partner_id': partner3.id,
                        'helpful': True,
                    })
                    created_count += 1
            
            if kb_article4:
                kb_feedback4 = self.env['helpdesk.knowledge.article.feedback'].sudo().search([
                    ('article_id', '=', kb_article4.id),
                    ('partner_id', '=', partner4.id)
                ], limit=1)
                if not kb_feedback4:
                    kb_feedback4 = self.env['helpdesk.knowledge.article.feedback'].sudo().create({
                        'article_id': kb_article4.id,
                        'rating': '5',
                        'feedback': 'Excellent security tips!',
                        'partner_id': partner4.id,
                        'helpful': True,
                    })
                    created_count += 1
            
            if kb_article5:
                kb_feedback5 = self.env['helpdesk.knowledge.article.feedback'].sudo().search([
                    ('article_id', '=', kb_article5.id),
                    ('partner_id', '=', partner5.id)
                ], limit=1)
                if not kb_feedback5:
                    kb_feedback5 = self.env['helpdesk.knowledge.article.feedback'].sudo().create({
                        'article_id': kb_article5.id,
                        'rating': '3',
                        'feedback': 'Good guide, but could use more screenshots.',
                        'partner_id': partner5.id,
                        'helpful': False,
                    })
                    created_count += 1
            
            # Add more Report Templates (currently 3, need 2 more to reach 5)
            report_template5 = self.env['helpdesk.report.template'].sudo().search([('name', '=', 'Tickets by Category & Type')], limit=1)
            if not report_template5:
                report_template5 = self.env['helpdesk.report.template'].sudo().create({
                    'name': 'Tickets by Category & Type',
                    'view_type': 'pivot',
                    'group_by_field': 'category_id',
                    'secondary_group_by_field': 'ticket_type_id',
                    'measure_field': 'id',
                })
                created_count += 1
            
            report_template6 = self.env['helpdesk.report.template'].sudo().search([('name', '=', 'Tickets Timeline')], limit=1)
            if not report_template6:
                report_template6 = self.env['helpdesk.report.template'].sudo().create({
                    'name': 'Tickets Timeline',
                    'view_type': 'graph',
                    'graph_type': 'timeline',
                    'group_by_field': 'create_date:month',
                    'measure_field': 'id',
                })
                created_count += 1
            
            # Count unique models with demo data
            model_count = 33  # All models are now covered
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Success'),
                    'message': _('Created %d demo records successfully across %d models!') % (created_count, model_count),
                    'type': 'success',
                    'sticky': False,
                }
            }
            
        except Exception as e:
            _logger.error(f"Error creating demo records: {e}")
            raise UserError(_('Error creating demo records: %s') % str(e))
