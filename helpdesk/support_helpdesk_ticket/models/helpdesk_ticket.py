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
from datetime import datetime, timedelta, time

_logger = logging.getLogger(__name__)


class HelpdeskTicket(models.Model):
    _name = 'helpdesk.ticket'
    _description = 'Helpdesk Ticket'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'create_date desc'
    _rec_name = 'ticket_number'

    # ==================== Basic Fields ====================
    name = fields.Char(
        string='Subject',
        required=True,
        tracking=True,
        help='Brief description of the ticket'
    )
    ticket_number = fields.Char(
        string='Ticket Number',
        readonly=True,
        copy=False,
        index=True,
        default=lambda self: _('New'),
        help='Unique ticket number'
    )
    description = fields.Html(
        string='Description',
        help='Detailed description of the issue'
    )
    reference = fields.Char(
        string='Reference',
        help='External reference number'
    )

    # ==================== Status Field ====================
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('new', 'New'),
            ('assigned', 'Assigned'),
            ('in_progress', 'In Progress'),
            ('resolved', 'Resolved'),
            ('closed', 'Closed'),
            ('cancelled', 'Cancelled'),
        ],
        string='Status',
        default='new',
        required=True,
        tracking=True,
        copy=False,
        index=True,
        help='Current status of the ticket'
    )

    # ==================== Priority Field ====================
    priority = fields.Selection(
        [
            ('0', 'Low'),
            ('1', 'Medium'),
            ('2', 'High'),
            ('3', 'Urgent'),
        ],
        string='Priority',
        default='1',
        required=True,
        tracking=True,
        index=True,
        help='Priority level of the ticket'
    )
    priority_color = fields.Integer(
        string='Priority Color',
        compute='_compute_priority_color',
        help='Color code for priority (0-11)'
    )
    old_priority = fields.Selection(
        [
            ('0', 'Low'),
            ('1', 'Medium'),
            ('2', 'High'),
            ('3', 'Urgent'),
        ],
        string='Previous Priority',
        readonly=True,
        help='Previous priority before change'
    )
    priority_change_date = fields.Datetime(
        string='Priority Change Date',
        readonly=True,
        help='Date when priority was last changed'
    )
    priority_change_count = fields.Integer(
        string='Priority Changes',
        compute='_compute_priority_change_count',
        help='Number of times priority has been changed'
    )

    # ==================== Ticket Type ====================
    ticket_type_id = fields.Many2one(
        'helpdesk.ticket.type',
        string='Ticket Type',
        tracking=True,
        help='Type of ticket'
    )

    # ==================== Template ====================
    template_id = fields.Many2one(
        'helpdesk.ticket.template',
        string='Template',
        help='Template used to create this ticket'
    )

    # ==================== Parent/Child Relationships ====================
    parent_ticket_id = fields.Many2one(
        'helpdesk.ticket',
        string='Parent Ticket',
        help='Parent ticket if this ticket was split from another ticket',
        index=True
    )
    child_ticket_ids = fields.One2many(
        'helpdesk.ticket',
        'parent_ticket_id',
        string='Child Tickets',
        help='Child tickets created by splitting this ticket'
    )
    child_ticket_count = fields.Integer(
        string='Child Tickets Count',
        compute='_compute_child_ticket_count',
        help='Number of child tickets'
    )
    is_parent = fields.Boolean(
        string='Is Parent',
        compute='_compute_is_parent',
        help='True if this ticket has child tickets'
    )
    is_child = fields.Boolean(
        string='Is Child',
        compute='_compute_is_child',
        help='True if this ticket is a child ticket'
    )

    # ==================== Category and Tags ====================
    category_id = fields.Many2one(
        'helpdesk.category',
        string='Category',
        tracking=True,
        help='Ticket category'
    )
    tag_ids = fields.Many2many(
        'helpdesk.tag',
        'helpdesk_ticket_tag_rel',
        'ticket_id',
        'tag_id',
        string='Tags',
        help='Tags for categorization'
    )

    # ==================== Customer/Partner Relationship ====================
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        required=True,
        tracking=True,
        index=True,
        help='Customer/Partner associated with this ticket'
    )
    partner_name = fields.Char(
        string='Customer Name',
        related='partner_id.name',
        readonly=True,
        store=True
    )
    partner_email = fields.Char(
        string='Customer Email',
        related='partner_id.email',
        readonly=True,
        store=True
    )
    partner_phone = fields.Char(
        string='Customer Phone',
        related='partner_id.phone',
        readonly=True,
        store=True
    )

    personal_data_anonymized = fields.Boolean(
        string='Personal Data Anonymized',
        help='Indicates whether personal data in this ticket has been anonymized for GDPR compliance.',
        readonly=True,
    )

    # ==================== Assignment Fields ====================
    user_id = fields.Many2one(
        'res.users',
        string='Assigned To',
        tracking=True,
        index=True,
        help='User assigned to handle this ticket'
    )
    team_id = fields.Many2one(
        'helpdesk.team',
        string='Team',
        tracking=True,
        index=True,
        help='Team responsible for this ticket'
    )
    
    # Assignment History
    assignment_history_ids = fields.One2many(
        'helpdesk.ticket.assignment.history',
        'ticket_id',
        string='Assignment History',
        readonly=True,
        help='History of all assignments for this ticket'
    )
    assignment_history_count = fields.Integer(
        string='Assignment Count',
        compute='_compute_assignment_history_count',
        help='Number of times this ticket has been assigned'
    )
    
    # Notification History
    notification_history_ids = fields.One2many(
        'helpdesk.notification.history',
        'ticket_id',
        string='Notification History',
        readonly=True,
        help='History of all notifications sent for this ticket'
    )
    notification_history_count = fields.Integer(
        string='Notification Count',
        compute='_compute_notification_history_count',
        help='Number of notifications sent for this ticket'
    )
    
    # Reminders
    reminder_ids = fields.One2many(
        'helpdesk.reminder',
        'ticket_id',
        string='Reminders',
        readonly=True,
        help='Reminders for this ticket'
    )
    reminder_count = fields.Integer(
        string='Reminder Count',
        compute='_compute_reminder_count',
        help='Number of reminders for this ticket'
    )
    pending_reminder_count = fields.Integer(
        string='Pending Reminders',
        compute='_compute_reminder_count',
        help='Number of pending reminders'
    )

    # ==================== Date Fields ====================
    assigned_date = fields.Datetime(
        string='Assigned Date',
        readonly=True,
        help='Date when ticket was assigned'
    )
    resolved_date = fields.Datetime(
        string='Resolved Date',
        readonly=True,
        help='Date when ticket was resolved'
    )
    closed_date = fields.Datetime(
        string='Closed Date',
        readonly=True,
        help='Date when ticket was closed'
    )
    last_stage_update = fields.Datetime(
        string='Last Stage Update',
        readonly=True,
        help='Date of last status change'
    )

    # ==================== Channel Field ====================
    channel_id = fields.Many2one(
        'helpdesk.channel',
        string='Channel',
        required=True,
        tracking=True,
        index=True,
        help='Channel through which ticket was created'
    )
    channel = fields.Char(
        string='Channel (Legacy)',
        related='channel_id.code',
        readonly=True,
        store=True,
        help='Legacy channel code for backward compatibility'
    )

    # ==================== Phone Support Fields ====================
    phone_number = fields.Char(
        string='Phone Number',
        tracking=True,
        help='Phone number used to create this ticket (if applicable)'
    )
    call_log_ids = fields.One2many(
        'helpdesk.call.log',
        'ticket_id',
        string='Call History',
        help='Call logs associated with this ticket'
    )
    call_log_count = fields.Integer(
        string='Call Count',
        compute='_compute_call_log_count',
        store=False,
        help='Number of calls related to this ticket'
    )

    # ==================== Social Media Support Fields ====================
    social_media_post_ids = fields.One2many(
        'helpdesk.social.media.post',
        'ticket_id',
        string='Social Media Posts',
        help='Social media posts associated with this ticket'
    )
    social_media_post_count = fields.Integer(
        string='Social Media Posts Count',
        compute='_compute_social_media_post_count',
        store=False,
        help='Number of social media posts related to this ticket'
    )

    # ==================== Ticket Messages/Discuss Panel ====================
    discuss_message_ids = fields.One2many(
        'helpdesk.ticket.message',
        'ticket_id',
        string='Discuss Messages',
        help='Messages in the discuss panel'
    )
    discuss_message_count = fields.Integer(
        string='Discuss Message Count',
        compute='_compute_discuss_message_count',
        store=False,
        help='Number of messages in the discuss panel'
    )

    # ==================== Rating and Feedback ====================
    rating = fields.Selection(
        [
            ('0', 'Very Dissatisfied'),
            ('1', 'Dissatisfied'),
            ('2', 'Neutral'),
            ('3', 'Satisfied'),
            ('4', 'Very Satisfied'),
        ],
        string='Rating',
        help='Customer satisfaction rating'
    )
    feedback = fields.Text(
        string='Feedback',
        help='Customer feedback about the service'
    )
    feedback_date = fields.Datetime(
        string='Feedback Date',
        readonly=True,
        help='Date when feedback was provided'
    )

    # ==================== Internal Notes ====================
    internal_note = fields.Html(
        string='Internal Notes',
        help='Private notes visible only to staff (not visible to customer)',
        groups='support_helpdesk_ticket.group_helpdesk_user,support_helpdesk_ticket.group_helpdesk_agent,support_helpdesk_ticket.group_helpdesk_manager'
    )

    # ==================== SLA Fields (for future implementation) ====================
    sla_policy_id = fields.Many2one(
        'helpdesk.sla.policy',
        string='SLA Policy',
        help='Service Level Agreement policy applied to this ticket'
    )
    sla_response_deadline = fields.Datetime(
        string='SLA Response Deadline',
        help='Deadline for first response'
    )
    sla_resolution_deadline = fields.Datetime(
        string='SLA Resolution Deadline',
        help='Deadline for ticket resolution'
    )
    sla_response_status = fields.Selection(
        [
            ('met', 'Met'),
            ('at_risk', 'At Risk'),
            ('breached', 'Breached'),
        ],
        string='SLA Response Status',
        compute='_compute_sla_status',
        store=True
    )
    sla_resolution_status = fields.Selection(
        [
            ('met', 'Met'),
            ('at_risk', 'At Risk'),
            ('breached', 'Breached'),
        ],
        string='SLA Resolution Status',
        compute='_compute_sla_status',
        store=True
    )
    sla_response_time_remaining = fields.Float(
        string='SLA Response Time Remaining (Hours)',
        compute='_compute_sla_time_remaining',
        store=True,
        help='Time remaining until response deadline in hours'
    )
    sla_resolution_time_remaining = fields.Float(
        string='SLA Resolution Time Remaining (Hours)',
        compute='_compute_sla_time_remaining',
        store=True,
        help='Time remaining until resolution deadline in hours'
    )

    # ==================== Computed Fields ====================
    is_assigned = fields.Boolean(
        string='Is Assigned',
        compute='_compute_is_assigned',
        store=True
    )
    is_overdue = fields.Boolean(
        string='Is Overdue',
        compute='_compute_is_overdue',
        store=True,
        help='Check if ticket is overdue based on SLA'
    )
    days_since_creation = fields.Integer(
        string='Days Since Creation',
        compute='_compute_days_since_creation',
        store=True,
        help='Number of days since ticket creation'
    )
    days_to_resolve = fields.Integer(
        string='Days to Resolve',
        compute='_compute_days_to_resolve',
        store=True,
        help='Number of days taken to resolve'
    )

    # ==================== Model Linking Fields (for future implementation) ====================
    model_link_ids = fields.One2many(
        'helpdesk.ticket.model.link',
        'ticket_id',
        string='Linked Models',
        help='Models and objects linked to this ticket'
    )
    model_link_count = fields.Integer(
        string='Linked Records Count',
        compute='_compute_model_link_count',
        help='Number of linked records'
    )
    
    # Task 8.4: Quick access fields
    quick_link_ids = fields.One2many(
        'helpdesk.ticket.model.link',
        'ticket_id',
        string='Quick Links',
        compute='_compute_quick_links',
        help='Quick access to linked records (first 5)'
    )

    # ==================== Status History ====================
    status_history_ids = fields.One2many(
        'helpdesk.ticket.status.history',
        'ticket_id',
        string='Status History',
        help='History of status changes'
    )
    status_history_count = fields.Integer(
        string='Status Changes',
        compute='_compute_status_history_count'
    )

    # ==================== Attachment Support ====================
    attachment_count = fields.Integer(
        string='Attachment Count',
        compute='_compute_attachment_count'
    )

    # ==================== Knowledge Base Integration ====================
    knowledge_article_ids = fields.Many2many(
        'helpdesk.knowledge.article',
        'helpdesk_ticket_knowledge_article_rel',
        'ticket_id',
        'article_id',
        string='Linked Articles',
        help='Knowledge base articles linked to this ticket'
    )
    suggested_article_ids = fields.Many2many(
        'helpdesk.knowledge.article',
        compute='_compute_suggested_articles',
        string='Suggested Articles',
        help='Articles suggested based on ticket content'
    )
    knowledge_article_count = fields.Integer(
        string='Article Count',
        compute='_compute_knowledge_article_count',
        help='Number of linked knowledge base articles'
    )

    # ==================== Computed Methods ====================
    @api.depends('user_id')
    def _compute_is_assigned(self):
        """Compute if ticket is assigned to a user"""
        for ticket in self:
            ticket.is_assigned = bool(ticket.user_id)

    @api.depends('sla_resolution_deadline', 'state')
    def _compute_is_overdue(self):
        """Compute if ticket is overdue based on SLA deadline."""
        now = fields.Datetime.now()
        for ticket in self:
            if ticket.sla_resolution_deadline and ticket.state not in ['resolved', 'closed', 'cancelled']:
                ticket.is_overdue = ticket.sla_resolution_deadline < now
            else:
                ticket.is_overdue = False

    @api.depends('create_date')
    def _compute_days_since_creation(self):
        """Compute days since ticket creation"""
        for ticket in self:
            if ticket.create_date:
                delta = fields.Datetime.now() - ticket.create_date
                ticket.days_since_creation = delta.days
            else:
                ticket.days_since_creation = 0

    @api.depends('create_date', 'resolved_date')
    def _compute_days_to_resolve(self):
        """Compute days taken to resolve"""
        for ticket in self:
            if ticket.resolved_date and ticket.create_date:
                delta = ticket.resolved_date - ticket.create_date
                ticket.days_to_resolve = delta.days
            else:
                ticket.days_to_resolve = 0

    @api.depends('sla_response_deadline', 'sla_resolution_deadline', 'state')
    def _compute_sla_status(self):
        """Compute SLA status based on deadlines"""
        now = fields.Datetime.now()
        for ticket in self:
            # Response SLA Status
            if ticket.sla_response_deadline:
                if ticket.state in ['resolved', 'closed', 'cancelled']:
                    ticket.sla_response_status = 'met' if ticket.assigned_date and ticket.assigned_date <= ticket.sla_response_deadline else 'breached'
                elif ticket.sla_response_deadline < now:
                    ticket.sla_response_status = 'breached'
                elif (ticket.sla_response_deadline - now).total_seconds() < 3600 * 2:  # Less than 2 hours remaining
                    ticket.sla_response_status = 'at_risk'
                else:
                    ticket.sla_response_status = 'met'
            else:
                ticket.sla_response_status = False

            # Resolution SLA Status
            if ticket.sla_resolution_deadline:
                if ticket.state in ['resolved', 'closed']:
                    ticket.sla_resolution_status = 'met' if ticket.resolved_date and ticket.resolved_date <= ticket.sla_resolution_deadline else 'breached'
                elif ticket.sla_resolution_deadline < now:
                    ticket.sla_resolution_status = 'breached'
                elif (ticket.sla_resolution_deadline - now).total_seconds() < 3600 * 4:  # Less than 4 hours remaining
                    ticket.sla_resolution_status = 'at_risk'
                else:
                    ticket.sla_resolution_status = 'met'
            else:
                ticket.sla_resolution_status = False

    @api.depends('sla_response_deadline', 'sla_resolution_deadline', 'state', 'assigned_date', 'resolved_date')
    def _compute_sla_time_remaining(self):
        """Compute time remaining for SLA response and resolution"""
        now = fields.Datetime.now()
        for ticket in self:
            # Response time remaining
            if ticket.sla_response_deadline and ticket.state not in ['resolved', 'closed', 'cancelled']:
                if ticket.assigned_date:
                    # Already responded, no time remaining
                    ticket.sla_response_time_remaining = 0.0
                else:
                    # Calculate time remaining until response deadline
                    delta = ticket.sla_response_deadline - now
                    if delta.total_seconds() > 0:
                        ticket.sla_response_time_remaining = delta.total_seconds() / 3600.0  # Convert to hours
                    else:
                        ticket.sla_response_time_remaining = 0.0  # Deadline passed
            else:
                ticket.sla_response_time_remaining = 0.0

            # Resolution time remaining
            if ticket.sla_resolution_deadline and ticket.state not in ['resolved', 'closed', 'cancelled']:
                if ticket.resolved_date:
                    # Already resolved, no time remaining
                    ticket.sla_resolution_time_remaining = 0.0
                else:
                    # Calculate time remaining until resolution deadline
                    delta = ticket.sla_resolution_deadline - now
                    if delta.total_seconds() > 0:
                        ticket.sla_resolution_time_remaining = delta.total_seconds() / 3600.0  # Convert to hours
                    else:
                        ticket.sla_resolution_time_remaining = 0.0  # Deadline passed
            else:
                ticket.sla_resolution_time_remaining = 0.0

    @api.depends('priority')
    def _compute_priority_color(self):
        """Compute a color index for the current priority.

        Odoo color codes convention:
        0 = no color, 1 = orange, 2 = red, 3 = blue, ...
        """
        priority_colors = {
            '0': 0,  # Low  -> no color
            '1': 3,  # Medium -> blue
            '2': 1,  # High -> orange
            '3': 2,  # Urgent -> red
        }
        for ticket in self:
            ticket.priority_color = priority_colors.get(ticket.priority, 0)

    @api.depends('message_ids.tracking_value_ids')
    def _compute_priority_change_count(self):
        """Compute how many times the ticket priority changed, based on mail tracking."""
        Tracking = self.env['mail.tracking.value'].sudo()
        priority_field = self.env['ir.model.fields'].search([
            ('model', '=', self._name),
            ('name', '=', 'priority')
        ], limit=1)
        for ticket in self:
            if not ticket.id:
                ticket.priority_change_count = 0
                continue
            if not priority_field:
                ticket.priority_change_count = 0
                continue
            ticket.priority_change_count = Tracking.search_count([
                ('field_id', '=', priority_field.id),
                ('mail_message_id.model', '=', self._name),
                ('mail_message_id.res_id', '=', ticket.id),
            ])

    def _compute_attachment_count(self):
        """Compute number of attachments linked to this ticket.

        We rely on the generic mail.thread counter `message_attachment_count`,
        which already computes the number of attachments for any threaded model.
        """
        for ticket in self:
            # `message_attachment_count` comes from `mail.thread`
            ticket.attachment_count = ticket.message_attachment_count

    def _compute_model_link_count(self):
        """Compute number of linked records"""
        for ticket in self:
            ticket.model_link_count = len(ticket.model_link_ids)
    
    @api.depends('model_link_ids')
    def _compute_quick_links(self):
        """Task 8.4: Compute quick links (first 5 for quick access)"""
        for ticket in self:
            ticket.quick_link_ids = ticket.model_link_ids[:5]

    @api.depends('call_log_ids')
    def _compute_call_log_count(self):
        """Compute call log count"""
        for ticket in self:
            ticket.call_log_count = len(ticket.call_log_ids)

    @api.depends('social_media_post_ids')
    def _compute_social_media_post_count(self):
        """Compute social media post count"""
        for ticket in self:
            ticket.social_media_post_count = len(ticket.social_media_post_ids)

    @api.depends('discuss_message_ids')
    def _compute_discuss_message_count(self):
        """Compute discuss message count"""
        for ticket in self:
            ticket.discuss_message_count = len(ticket.discuss_message_ids)

    def _compute_status_history_count(self):
        """Compute number of status changes"""
        for ticket in self:
            ticket.status_history_count = len(ticket.status_history_ids)

    @api.depends('knowledge_article_ids')
    def _compute_knowledge_article_count(self):
        """Compute number of linked articles"""
        for ticket in self:
            ticket.knowledge_article_count = len(ticket.knowledge_article_ids)
    
    @api.depends('assignment_history_ids')
    def _compute_assignment_history_count(self):
        """Compute assignment history count"""
        for ticket in self:
            ticket.assignment_history_count = len(ticket.assignment_history_ids)
    
    @api.depends('notification_history_ids')
    def _compute_notification_history_count(self):
        """Compute notification history count"""
        for ticket in self:
            ticket.notification_history_count = len(ticket.notification_history_ids)
    
    @api.depends('reminder_ids', 'reminder_ids.status')
    def _compute_reminder_count(self):
        """Compute reminder counts"""
        for ticket in self:
            ticket.reminder_count = len(ticket.reminder_ids)
            ticket.pending_reminder_count = len(ticket.reminder_ids.filtered(lambda r: r.status == 'pending'))

    @api.depends('name', 'description', 'category_id', 'tag_ids')
    def _compute_suggested_articles(self):
        """Compute suggested articles based on ticket content"""
        KnowledgeArticle = self.env['helpdesk.knowledge.article']
        for ticket in self:
            suggested_articles = self.env['helpdesk.knowledge.article']
            
            if ticket.name or ticket.description:
                # Extract keywords from ticket name and description
                keywords = []
                if ticket.name:
                    keywords.extend(ticket.name.lower().split())
                if ticket.description:
                    # Remove HTML tags and extract words
                    import re
                    text_content = re.sub(r'<[^>]+>', '', ticket.description or '')
                    keywords.extend(text_content.lower().split())
                
                # Remove common words and get unique keywords
                common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'what', 'which', 'who', 'when', 'where', 'why', 'how'}
                keywords = [k for k in keywords if len(k) > 3 and k not in common_words]
                keywords = list(set(keywords))[:10]  # Limit to 10 unique keywords
                
                if keywords:
                    # Search for articles matching keywords
                    domain = [
                        ('state', '=', 'published'),
                        ('active', '=', True),
                        '|',
                        ('name', 'ilike', ' '.join(keywords[:3])),  # Match first 3 keywords in title
                        ('content', 'ilike', ' '.join(keywords[:3])),  # Match first 3 keywords in content
                    ]
                    
                    # Add category filter if ticket has category
                    if ticket.category_id:
                        domain = ['|'] + domain + [('category_id', '=', ticket.category_id.id)]
                    
                    # Add tag filter if ticket has tags
                    if ticket.tag_ids:
                        domain = ['|'] + domain + [('tag_ids', 'in', ticket.tag_ids.ids)]
                    
                    suggested_articles = KnowledgeArticle.search(domain, limit=5, order='view_count desc, rating desc')
            
            # Also include FAQ articles if no specific matches
            if not suggested_articles and ticket.category_id:
                faq_articles = KnowledgeArticle.get_faq_articles(
                    category_id=ticket.category_id.id,
                    limit=3
                )
                suggested_articles = faq_articles
            
            ticket.suggested_article_ids = suggested_articles

    # ==================== Email Integration ====================
    @api.model
    def message_new(self, msg_dict, custom_values=None):
        """
        Override to create ticket from incoming email
        
        Handles:
        - Email-to-ticket conversion
        - Partner extraction/creation from email
        - Team assignment from email alias
        - HTML email parsing
        - Email attachments (handled automatically by mail.thread)
        """
        custom_values = custom_values or {}
        
        # Extract email information
        email_from = msg_dict.get('email_from', '')
        email_subject = msg_dict.get('subject', '')
        email_body = msg_dict.get('body', '')
        email_body_html = msg_dict.get('body_html', '')
        partner_ids = msg_dict.get('partner_ids', [])
        email_to = msg_dict.get('to', '')
        email_cc = msg_dict.get('cc', '')
        message_id = msg_dict.get('message_id', '')
        
        # Parse HTML email body if available, otherwise use plain text
        # Odoo's mail.thread will handle HTML conversion, but we prefer HTML if available
        description = email_body_html or email_body or ''
        
        # Find or create partner from email
        partner = None
        if partner_ids:
            partner = self.env['res.partner'].browse(partner_ids[0])
        elif email_from:
            # Extract email address from email_from (e.g., "John Doe <john@example.com>")
            email_address = email_from
            name = email_from
            if '<' in email_from and '>' in email_from:
                name = email_from.split('<')[0].strip().strip('"\'')
                email_address = email_from.split('<')[1].split('>')[0].strip()
            
            # Try to find partner by email
            partner = self.env['res.partner'].search([
                ('email', '=', email_address)
            ], limit=1)
            
            # If not found, create a new partner
            if not partner:
                partner = self.env['res.partner'].create({
                    'name': name or email_address,
                    'email': email_address,
                    'is_company': False,
                })
        
        # Extract team from alias if available
        team = None
        alias_name = None
        
        # Try to extract alias from 'to' field
        if email_to and '@' in email_to:
            alias_name = email_to.split('@')[0].strip()
        
        # Search for alias
        if alias_name:
            alias = self.env['mail.alias'].search([
                ('alias_name', '=', alias_name)
            ], limit=1)
            
            if alias and alias.alias_model_id.model == 'helpdesk.ticket':
                # Try to find team with this alias
                team = self.env['helpdesk.team'].search([
                    ('alias_id', '=', alias.id)
                ], limit=1)
                
                # If no team found, check alias defaults
                if not team and alias.alias_defaults:
                    import ast
                    try:
                        defaults = ast.literal_eval(alias.alias_defaults)
                        if 'team_id' in defaults:
                            team = self.env['helpdesk.team'].browse(defaults['team_id'])
                    except:
                        pass
        
        # Get email channel
        email_channel = self.env['helpdesk.channel'].search([('code', '=', 'email')], limit=1)
        if not email_channel:
            email_channel = self.env['helpdesk.channel'].search([('active', '=', True)], limit=1)
        
        # Prepare ticket values
        ticket_vals = {
            'name': email_subject or _('New Ticket from Email'),
            'description': description,
            'partner_id': partner.id if partner else False,
            'channel_id': email_channel.id if email_channel else False,
            'state': 'new',
        }
        
        # Add team if found
        if team:
            ticket_vals['team_id'] = team.id
            # Auto-assign if team has default user
            if team.team_leader_id:
                ticket_vals['user_id'] = team.team_leader_id.id
                ticket_vals['state'] = 'assigned'
        
        # Merge with custom values (custom values take precedence)
        ticket_vals.update(custom_values)
        
        # Create ticket (mail.thread will handle attachments automatically)
        ticket = super(HelpdeskTicket, self).message_new(msg_dict, custom_values=ticket_vals)
        
        # Log email creation
        _logger.info('Ticket %s created from email: %s', ticket.ticket_number, email_from)
        
        return ticket

    def message_update(self, msg_dict, update_vals=None):
        """
        Override to handle email replies to existing tickets
        
        Handles:
        - Email threading (message_id and references)
        - Comment notifications
        - Email attachments (handled automatically by mail.thread)
        """
        update_vals = update_vals or {}
        
        # Extract email information
        email_body = msg_dict.get('body', '')
        email_body_html = msg_dict.get('body_html', '')
        message_id = msg_dict.get('message_id', '')
        references = msg_dict.get('references', '')
        author_id = msg_dict.get('author_id', False)
        partner_ids = msg_dict.get('partner_ids', [])
        
        # Use HTML body if available, otherwise plain text
        body = email_body_html or email_body or ''
        
        # Post reply as a message/comment (mail.thread handles threading via message_id)
        if body:
            # Determine if this is a customer reply or internal reply
            is_customer_reply = False
            if self.partner_id and partner_ids:
                is_customer_reply = self.partner_id.id in partner_ids
            
            # Post the message (mail.thread will handle threading automatically)
            subtype = self.env.ref('mail.mt_comment', raise_if_not_found=False)
            message = self.message_post(
                body=body,
                message_type='email',
                subtype_id=subtype.id if subtype else False,
                author_id=author_id,
                partner_ids=partner_ids,
                message_id=message_id,
                references=references,
            )
            
            # Send comment notification if this is a customer reply
            if is_customer_reply:
                self._send_comment_notification(message)
            else:
                # Internal comment - notify customer if configured
                self._send_comment_notification(message, notify_customer=True)
        
        return super(HelpdeskTicket, self).message_update(msg_dict, update_vals)
    
    def _send_comment_notification(self, message, notify_customer=False):
        """
        Send notification when a comment is added to a ticket
        
        :param message: The message/comment that was posted
        :param notify_customer: If True, notify customer even for internal comments
        """
        # Use notification template system
        templates = self.env['helpdesk.notification.template'].search([
            ('active', '=', True),
            ('notification_type', '=', 'ticket_comment')
        ])
        
        for template in templates:
            template.send_notification(self, {'message': message})
        
        # Fallback to email template if no notification templates found
        if not templates:
            # Determine who to notify
            notify_partners = []
            
            if notify_customer and self.partner_id and self.partner_id.email:
                notify_partners.append(self.partner_id.id)
            elif not notify_customer:
                # Customer replied - notify assigned agent and team
                if self.user_id and self.user_id.partner_id:
                    notify_partners.append(self.user_id.partner_id.id)
                if self.team_id and self.team_id.team_leader_id and self.team_id.team_leader_id.partner_id:
                    if self.team_id.team_leader_id.partner_id.id not in notify_partners:
                        notify_partners.append(self.team_id.team_leader_id.partner_id.id)
            
            if notify_partners:
                template = self.env.ref(
                    'support_helpdesk_ticket.email_template_ticket_comment',
                    raise_if_not_found=False
                )
                
                if template:
                    # Get email addresses
                    email_addresses = [
                        self.env['res.partner'].browse(pid).email_formatted
                        for pid in notify_partners
                        if self.env['res.partner'].browse(pid).email
                    ]
                    
                    if email_addresses:
                        template.with_context(message_body=message.body).send_mail(
                            self.id,
                            force_send=True,
                            email_values={'email_to': ','.join(email_addresses)}
                        )

    # ==================== Helper Methods for Config Parameters ====================
    
    @api.model
    def _get_config_param(self, key, default=None):
        """Get configuration parameter value"""
        return self.env['ir.config_parameter'].sudo().get_param(key, default)
    
    @api.model
    def _get_config_bool(self, key, default=False):
        """Get boolean configuration parameter"""
        value = self._get_config_param(key, str(default))
        return value.lower() in ('true', '1', 'yes', 'on')
    
    @api.model
    def _apply_config_defaults(self, vals):
        """Apply default values from configuration settings"""
        # Priority: Config defaults < Type defaults < Category defaults < Provided values
        
        # Default Priority (from config)
        if 'priority' not in vals:
            default_priority = self._get_config_param('helpdesk.default_priority', '1')
            if default_priority:
                vals['priority'] = default_priority
        
        # Default State (from config)
        if 'state' not in vals:
            default_state = self._get_config_param('helpdesk.default_state', 'new')
            if default_state:
                vals['state'] = default_state
        
        # Default Channel (from config)
        if 'channel_id' not in vals:
            # Try to get from config parameter (Many2one)
            default_channel_id = self._get_config_param('helpdesk.default_channel_id', False)
            if default_channel_id:
                vals['channel_id'] = int(default_channel_id)
            else:
                # Fallback: try legacy code-based config
                default_channel_code = self._get_config_param('helpdesk.default_channel', 'web')
                if default_channel_code:
                    default_channel = self.env['helpdesk.channel'].search([('code', '=', default_channel_code)], limit=1)
                    if default_channel:
                        vals['channel_id'] = default_channel.id
            
            # Final fallback: get first active channel
            if 'channel_id' not in vals:
                default_channel = self.env['helpdesk.channel'].search([('active', '=', True)], limit=1, order='sequence')
                if default_channel:
                    vals['channel_id'] = default_channel.id
        
        # Default Team (from config) - only if not set
        if 'team_id' not in vals:
            default_team_id = self._get_config_param('helpdesk.default_team_id', False)
            if default_team_id:
                try:
                    vals['team_id'] = int(default_team_id)
                except (ValueError, TypeError):
                    pass
        
        # Default Category (from config) - only if not set
        if 'category_id' not in vals:
            default_category_id = self._get_config_param('helpdesk.default_category_id', False)
            if default_category_id:
                try:
                    vals['category_id'] = int(default_category_id)
                except (ValueError, TypeError):
                    pass
        
        # Default Ticket Type (from config) - only if not set
        if 'ticket_type_id' not in vals:
            default_ticket_type_id = self._get_config_param('helpdesk.default_ticket_type_id', False)
            if default_ticket_type_id:
                try:
                    vals['ticket_type_id'] = int(default_ticket_type_id)
                except (ValueError, TypeError):
                    pass
        
        return vals
    
    @api.model
    def _validate_required_fields(self, vals):
        """Validate required fields based on configuration"""
        errors = []
        
        # Check if category is required
        if self._get_config_bool('helpdesk.require_category', False):
            if not vals.get('category_id'):
                errors.append(_('Category is required'))
        
        # Check if priority is required
        if self._get_config_bool('helpdesk.require_priority', False):
            if not vals.get('priority'):
                errors.append(_('Priority is required'))
        
        # Check if ticket type is required
        if self._get_config_bool('helpdesk.require_ticket_type', False):
            if not vals.get('ticket_type_id'):
                errors.append(_('Ticket Type is required'))
        
        if errors:
            raise ValidationError('\n'.join(errors))
    
    @api.model
    def _generate_ticket_number(self, vals):
        """Generate ticket number based on configuration"""
        sequence_model = self.env['ir.sequence']
        ticket_prefix = self._get_config_param('helpdesk.ticket_prefix', 'TKT')
        number_format = self._get_config_param('helpdesk.ticket_number_format', 'sequential')
        
        sequence_code = 'helpdesk.ticket'
        sequence = None

        # Check if team has specific sequence
        if 'team_id' in vals and vals['team_id']:
            team = self.env['helpdesk.team'].browse(vals['team_id'])
            if team.sequence_id:
                sequence = team.sequence_id
            elif team.sequence_code:
                sequence = sequence_model.search([
                    ('code', '=', team.sequence_code),
                    ('company_id', 'in', [False, self.env.company.id])
                ], limit=1)

        # Use default sequence if team sequence not available
        if not sequence:
            sequence = sequence_model.search([
                ('code', '=', sequence_code),
                ('company_id', 'in', [False, self.env.company.id])
            ], limit=1)

        # Generate ticket number based on format
        if number_format == 'date_based':
            # Date-based format: YYYYMMDD-001
            today = fields.Date.today()
            date_str = today.strftime('%Y%m%d')
            if sequence:
                seq_number = sequence.next_by_id() or '001'
                # Extract number from sequence (remove prefix if exists)
                seq_num = seq_number.split('-')[-1] if '-' in seq_number else seq_number
                ticket_number = f"{date_str}-{seq_num}"
            else:
                ticket_number = sequence_model.next_by_code(sequence_code) or f"{date_str}-001"
        elif number_format == 'random':
            # Random format (using sequence but with prefix)
            import random
            random_suffix = str(random.randint(1000, 9999))
            ticket_number = f"{ticket_prefix}-{random_suffix}"
        else:
            # Sequential format (default)
            if sequence:
                seq_number = sequence.next_by_id() or '001'
                # Add prefix if not already present
                if ticket_prefix and not seq_number.startswith(ticket_prefix):
                    ticket_number = f"{ticket_prefix}-{seq_number}"
                else:
                    ticket_number = seq_number
            else:
                seq_number = sequence_model.next_by_code(sequence_code) or '001'
                ticket_number = f"{ticket_prefix}-{seq_number}" if ticket_prefix else seq_number
        
        return ticket_number

    # ==================== CRUD Methods ====================
    @api.model_create_multi
    def create(self, vals_list):
        """Override create to generate ticket number (batch-friendly)"""
        # Ensure we always work with a list for batch creates
        if not isinstance(vals_list, list):
            vals_list = [vals_list]

        for vals in vals_list:
            # Apply configuration defaults FIRST (lowest priority)
            vals = self._apply_config_defaults(vals)
            
            # Generate ticket number if needed
            if vals.get('ticket_number', _('New')) == _('New'):
                vals['ticket_number'] = self._generate_ticket_number(vals)

            # Task 9.2: Apply type-based defaults if ticket type is specified (higher priority than config)
            if 'ticket_type_id' in vals and vals.get('ticket_type_id'):
                ticket_type = self.env['helpdesk.ticket.type'].browse(vals['ticket_type_id'])
                if ticket_type:
                    # Apply type-based defaults (only if not already set)
                    if ticket_type.default_priority and 'priority' not in vals:
                        vals['priority'] = ticket_type.default_priority
                    if ticket_type.default_category_id and 'category_id' not in vals:
                        vals['category_id'] = ticket_type.default_category_id.id
                    if ticket_type.default_team_id and 'team_id' not in vals:
                        vals['team_id'] = ticket_type.default_team_id.id
                    if ticket_type.default_sla_policy_id and 'sla_policy_id' not in vals:
                        vals['sla_policy_id'] = ticket_type.default_sla_policy_id.id
                    if ticket_type.default_template_id and 'template_id' not in vals:
                        vals['template_id'] = ticket_type.default_template_id.id

            # Apply template if specified (highest priority)
            if 'template_id' in vals and vals['template_id']:
                template = self.env['helpdesk.ticket.template'].browse(vals['template_id'])
                if template:
                    template_values = template._get_template_values()
                    # Merge template values with provided values (provided values take precedence)
                    for key, value in template_values.items():
                        if key not in vals or not vals.get(key):
                            vals[key] = value

            # Validate required fields based on configuration
            self._validate_required_fields(vals)

            # Set last stage update
            vals['last_stage_update'] = fields.Datetime.now()

        tickets = super(HelpdeskTicket, self).create(vals_list)

        # Post-create processing per ticket
        for ticket in tickets:
            # Auto-assign SLA policy and deadlines if tracking is enabled
            # Skip automatic deadline calculation when a custom SLA resolution deadline
            # has already been explicitly provided (e.g., in demo or import data).
            if self._get_config_bool('helpdesk.enable_sla_tracking', True):
                custom_resolution_deadline_set = bool(ticket.sla_resolution_deadline)
                if not ticket.sla_policy_id:
                    ticket._assign_sla_policy()
                # Only calculate deadlines if they weren't explicitly set
                if not custom_resolution_deadline_set:
                    ticket._calculate_sla_deadlines()
            else:
                # SLA tracking disabled, clear any SLA fields
                ticket.sla_policy_id = False

            # Auto-assign ticket if enabled and not already assigned
            if self._get_config_bool('helpdesk.auto_assign_tickets', False) and not ticket.user_id:
                ticket._auto_assign_ticket()

            # Send notification if configured
            ticket._send_ticket_created_notification()

            # Execute workflow rules for ticket creation (if enabled)
            if self._get_config_bool('helpdesk.enable_workflow', True):
                ticket._execute_workflow_rules('create')

            # Task 8.5: Auto-link models based on auto-linking rules
            ticket._process_auto_links()

        return tickets
    
    # ==================== Type-Based Configuration (Task 9.2) ====================
    @api.onchange('ticket_type_id')
    def _onchange_ticket_type_id(self):
        """Task 9.2: Apply type-based defaults when ticket type changes"""
        if self.ticket_type_id:
            # Apply defaults only if fields are not already set
            if self.ticket_type_id.default_priority and not self.priority:
                self.priority = self.ticket_type_id.default_priority
            if self.ticket_type_id.default_category_id and not self.category_id:
                self.category_id = self.ticket_type_id.default_category_id
            if self.ticket_type_id.default_team_id and not self.team_id:
                self.team_id = self.ticket_type_id.default_team_id
            if self.ticket_type_id.default_sla_policy_id and not self.sla_policy_id:
                self.sla_policy_id = self.ticket_type_id.default_sla_policy_id
            if self.ticket_type_id.default_template_id and not self.template_id:
                self.template_id = self.ticket_type_id.default_template_id
    
    def _apply_type_based_routing(self):
        """Task 9.2: Apply type-based routing (team assignment)"""
        self.ensure_one()
        if self.ticket_type_id and self.ticket_type_id.default_team_id and not self.team_id:
            self.team_id = self.ticket_type_id.default_team_id
    
    def _apply_type_based_sla(self):
        """Task 9.2: Apply type-based SLA assignment"""
        self.ensure_one()
        if self.ticket_type_id and self.ticket_type_id.default_sla_policy_id and not self.sla_policy_id:
            self.sla_policy_id = self.ticket_type_id.default_sla_policy_id
            # Recalculate SLA deadlines if SLA was assigned
            if self.sla_policy_id:
                self._calculate_sla_deadlines()
    
    # ==================== Auto-Assignment ====================
    def _auto_assign_ticket(self):
        """Auto-assign ticket based on configuration settings"""
        self.ensure_one()
        if self.user_id:
            return  # Already assigned
        
        assignment_method = self._get_config_param('helpdesk.auto_assignment_method', 'round_robin')
        team = self.team_id
        
        if not team:
            return  # No team to assign from
        
        # Get team members
        team_members = team.member_ids.filtered(lambda m: m.active)
        if not team_members:
            return  # No active team members
        
        assigned_user = None
        
        if assignment_method == 'round_robin':
            # Round-robin: Assign to member with least recent assignment
            # Get last assignment per user
            last_assignments = {}
            for member in team_members:
                last_ticket = self.search([
                    ('team_id', '=', team.id),
                    ('user_id', '=', member.id)
                ], order='assigned_date desc', limit=1)
                if last_ticket and last_ticket.assigned_date:
                    last_assignments[member.id] = last_ticket.assigned_date
                else:
                    last_assignments[member.id] = fields.Datetime.from_string('1970-01-01')
            
            # Assign to user with oldest assignment
            assigned_user = min(team_members, key=lambda m: last_assignments.get(m.id, fields.Datetime.from_string('1970-01-01')))
        
        elif assignment_method == 'load_based':
            # Load-based: Assign to member with least open tickets
            max_tickets = int(self._get_config_param('helpdesk.max_tickets_per_agent', 10))
            member_loads = {}
            for member in team_members:
                open_tickets_count = self.search_count([
                    ('team_id', '=', team.id),
                    ('user_id', '=', member.id),
                    ('state', 'not in', ['closed', 'cancelled'])
                ])
                if open_tickets_count < max_tickets:
                    member_loads[member.id] = open_tickets_count
            
            if member_loads:
                # Assign to member with least tickets
                assigned_user = min(team_members, key=lambda m: member_loads.get(m.id, max_tickets))
        
        elif assignment_method == 'random':
            # Random assignment
            import random
            assigned_user = random.choice(team_members)
        
        elif assignment_method == 'team_based':
            # Team-based: Assign to team leader or first member
            if team.leader_id and team.leader_id in team_members:
                assigned_user = team.leader_id
            elif team_members:
                assigned_user = team_members[0]
        
        # Assign the user
        if assigned_user:
            self.with_context(assignment_method='auto_assignment').write({
                'user_id': assigned_user.id,
                'assigned_date': fields.Datetime.now()
            })
    
    # ==================== Workflow Engine ====================
    def _execute_workflow_rules(self, trigger_type, changed_fields=None):
        """
        Execute workflow rules for the ticket based on trigger type
        
        :param trigger_type: 'create', 'write', 'state_change', or 'field_change'
        :param changed_fields: list of field names that changed (for field_change trigger)
        """
        # Check if workflow automation is enabled
        if not self._get_config_bool('helpdesk.enable_workflow', True):
            return
        
        for ticket in self:
            # Map trigger types
            trigger_map = {
                'create': 'on_create',
                'write': 'on_update',
                'state_change': 'on_status_change',
                'field_change': 'on_field_change',
            }
            workflow_trigger = trigger_map.get(trigger_type, trigger_type)
            
            # Search for active rules matching the trigger
            domain = [
                ('active', '=', True),
                ('trigger', '=', workflow_trigger)
            ]
            
            # For field_change trigger, filter by specific fields
            if workflow_trigger == 'on_field_change' and changed_fields:
                # Get field IDs for the changed fields
                field_ids = self.env['ir.model.fields'].search([
                    ('model', '=', 'helpdesk.ticket'),
                    ('name', 'in', changed_fields)
                ]).ids
                if field_ids:
                    domain.append(('trigger_field_ids', 'in', field_ids))
                else:
                    # No matching fields, skip
                    continue
            
            rules = self.env['helpdesk.workflow.rule'].search(domain, order='sequence, id')
            
            for rule in rules:
                try:
                    # Evaluate conditions
                    if rule._evaluate_condition(ticket):
                        import time
                        start_time = time.time()
                        
                        # Log execution before action
                        log = self.env['helpdesk.workflow.execution.log'].create({
                            'rule_id': rule.id,
                            'ticket_id': ticket.id,
                            'trigger_type': trigger_type,
                            'status': 'executing',
                            'execution_date': fields.Datetime.now(),
                        })
                        
                        # Execute action
                        rule._execute_action(ticket)
                        
                        # Calculate execution time
                        execution_time = time.time() - start_time
                        
                        # Update log to success
                        log.write({
                            'status': 'success',
                            'execution_time': execution_time
                        })
                    else:
                        # Condition not met, log as skipped
                        self.env['helpdesk.workflow.execution.log'].create({
                            'rule_id': rule.id,
                            'ticket_id': ticket.id,
                            'trigger_type': trigger_type,
                            'status': 'skipped',
                            'execution_date': fields.Datetime.now(),
                        })
                except Exception as e:
                    # Log error
                    _logger.error('Workflow rule execution failed: %s', str(e))
                    log = self.env['helpdesk.workflow.execution.log'].search([
                        ('rule_id', '=', rule.id),
                        ('ticket_id', '=', ticket.id),
                    ], order='id desc', limit=1)
                    if log:
                        log.write({
                            'status': 'error',
                            'error_message': str(e)
                        })
                    else:
                        # Create error log if not found
                        self.env['helpdesk.workflow.execution.log'].create({
                            'rule_id': rule.id,
                            'ticket_id': ticket.id,
                            'trigger_type': trigger_type,
                            'status': 'error',
                            'error_message': str(e),
                            'execution_date': fields.Datetime.now(),
                        })

    def write(self, vals):
        """Override write to track status changes and update dates"""
        # Track status change
        if 'state' in vals:
            for ticket in self:
                old_state = ticket.state
                new_state = vals['state']
                
                # Validate state transition if not from wizard
                if old_state != new_state and not self.env.context.get('skip_state_validation'):
                    ticket._validate_state_transition(old_state, new_state)
                
                # Update dates based on state change
                if new_state == 'assigned' and old_state != 'assigned':
                    vals['assigned_date'] = vals.get('assigned_date', fields.Datetime.now())
                elif new_state == 'resolved' and old_state != 'resolved':
                    vals['resolved_date'] = vals.get('resolved_date', fields.Datetime.now())
                elif new_state == 'closed' and old_state != 'closed':
                    vals['closed_date'] = vals.get('closed_date', fields.Datetime.now())
                
                # Update last stage update
                vals['last_stage_update'] = fields.Datetime.now()
                
                # Create status history record
                if old_state != new_state:
                    self.env['helpdesk.ticket.status.history'].create({
                        'ticket_id': ticket.id,
                        'old_state': old_state,
                        'new_state': new_state,
                        'user_id': self.env.user.id,
                        'note': vals.get('status_change_note', ''),
                        'reason': self.env.context.get('status_change_reason', 'manual')
                    })
        
        # Task 9.2: Apply type-based routing and SLA when type changes
        if 'ticket_type_id' in vals and vals.get('ticket_type_id'):
            for ticket in self:
                ticket._apply_type_based_routing()
                ticket._apply_type_based_sla()
        
        # Re-assign SLA policy if ticket attributes changed that affect matching
        if any(field in vals for field in ['priority', 'category_id', 'ticket_type_id', 'team_id']):
            for ticket in self:
                # Task 9.2: Check type-based SLA first, then fall back to policy matching
                if not ticket.sla_policy_id:
                    ticket._apply_type_based_sla()
                # Check if current policy still matches
                if ticket.sla_policy_id and not ticket.sla_policy_id._matches_ticket(ticket):
                    # Policy no longer matches, find new one
                    ticket._assign_sla_policy()
                elif not ticket.sla_policy_id:
                    # No policy assigned, try to assign one
                    ticket._assign_sla_policy()
                # Recalculate deadlines if policy changed
                if 'sla_policy_id' in vals or ticket.sla_policy_id:
                    ticket._calculate_sla_deadlines()
        
        # Track assignment change
        assignment_changed = False
        assignment_method = self.env.context.get('assignment_method', 'manual')
        workflow_rule_id = self.env.context.get('workflow_rule_id', False)
        
        if 'user_id' in vals or 'team_id' in vals:
            for ticket in self:
                old_user_id = ticket.user_id.id if ticket.user_id else False
                old_team_id = ticket.team_id.id if ticket.team_id else False
                new_user_id = vals.get('user_id') if 'user_id' in vals else old_user_id
                new_team_id = vals.get('team_id') if 'team_id' in vals else old_team_id
                
                # Handle None values (unassignment)
                if new_user_id is None:
                    new_user_id = False
                if new_team_id is None:
                    new_team_id = False
                
                # Check if assignment actually changed
                user_changed = old_user_id != new_user_id
                team_changed = old_team_id != new_team_id
                
                if user_changed or team_changed:
                    # Handle team-based auto-assignment
                    if team_changed and new_team_id and (not new_user_id or new_user_id == old_user_id):
                        # Ticket assigned to team but no user - try auto-assignment
                        new_team = self.env['helpdesk.team'].browse(new_team_id)
                        if new_team.auto_assign_enabled and new_team.member_ids:
                            # Use team's default algorithm or workflow rule's algorithm
                            if workflow_rule_id:
                                rule = self.env['helpdesk.workflow.rule'].browse(workflow_rule_id)
                                if rule.action_assign_algorithm != 'manual':
                                    algorithm = rule.action_assign_algorithm
                                else:
                                    algorithm = new_team.default_assignment_algorithm
                            else:
                                algorithm = new_team.default_assignment_algorithm
                            
                            # Get assigned user using algorithm
                            if algorithm:
                                assigned_user = rule._get_assigned_user(ticket, new_team, algorithm) if workflow_rule_id else self._get_team_assigned_user(ticket, new_team, algorithm)
                                if assigned_user:
                                    new_user_id = assigned_user.id
                                    vals['user_id'] = assigned_user.id
                                    assignment_method = algorithm
                    
                    # Fallback: If team is assigned but no user, assign team leader or first member
                    if team_changed and new_team_id and not new_user_id:
                        new_team = self.env['helpdesk.team'].browse(new_team_id)
                        if new_team.member_ids:
                            # Try team leader first, then first member
                            fallback_user = new_team.team_leader_id if new_team.team_leader_id and new_team.team_leader_id in new_team.member_ids else new_team.member_ids[0]
                            if fallback_user:
                                new_user_id = fallback_user.id
                                vals['user_id'] = fallback_user.id
                                if not assignment_method or assignment_method == 'workflow':
                                    assignment_method = 'team_based'
                    
                    # Ensure new_user_id is set before creating history (required field)
                    if not new_user_id:
                        # If still no user, use current user as fallback
                        new_user_id = self.env.user.id
                        if 'user_id' not in vals:
                            vals['user_id'] = self.env.user.id
                    
                    # Send assignment notification if enabled
                    if user_changed and new_user_id and ticket._get_config_bool('helpdesk.notify_on_assignment', True):
                        # Notification will be sent via workflow or notification system
                        # This is just a flag check - actual notification handled elsewhere
                        pass
                    
                    # Create assignment history record
                    history_vals = {
                        'ticket_id': ticket.id,
                        'old_user_id': old_user_id,
                        'new_user_id': new_user_id,
                        'old_team_id': old_team_id,
                        'new_team_id': new_team_id if new_team_id else False,
                        'assignment_date': fields.Datetime.now(),
                        'assigned_by_id': self.env.user.id,
                        'assignment_method': assignment_method,
                        'workflow_rule_id': workflow_rule_id,
                        'note': self.env.context.get('assignment_note', ''),
                    }
                    self.env['helpdesk.ticket.assignment.history'].create(history_vals)
                    
                    # Update state if needed
                    if 'user_id' in vals and vals['user_id']:
                        if ticket.state == 'new' and not ticket.assigned_date:
                            vals['state'] = 'assigned'
                            vals['assigned_date'] = fields.Datetime.now()
                            assignment_changed = True
        
        # Category-based routing
        if 'category_id' in vals and vals['category_id']:
            for ticket in self:
                category = self.env['helpdesk.category'].browse(vals['category_id'])
                if category:
                    # Apply category defaults
                    if category.default_team_id and not ticket.team_id:
                        vals['team_id'] = category.default_team_id.id
                    if category.default_user_id and not ticket.user_id:
                        vals['user_id'] = category.default_user_id.id
                    if category.default_priority and not ticket.priority:
                        vals['priority'] = category.default_priority
                    if category.default_sla_policy_id and not ticket.sla_policy_id:
                        vals['sla_policy_id'] = category.default_sla_policy_id.id
                        # Calculate SLA deadlines
                        ticket._calculate_sla_deadlines()
        
        # Track changed fields for field_change trigger
        changed_fields = list(vals.keys())
        
        result = super(HelpdeskTicket, self).write(vals)
        
        # Execute workflow rules
        for ticket in self:
            # Check for state change
            if 'state' in vals:
                old_state = ticket._origin.state if ticket._origin else ticket.state
                new_state = vals['state']
                if old_state != new_state:
                    # Execute state change workflow rules
                    ticket._execute_workflow_rules('state_change')
                    # Send notifications
                    ticket._send_status_change_notification(
                        old_state=old_state,
                        new_state=new_state
                    )
            
            # Execute field change workflow rules
            if changed_fields:
                ticket._execute_workflow_rules('field_change', changed_fields)
            
            # Execute update workflow rules (for general updates)
            if any(field in vals for field in changed_fields if field != 'state'):
                ticket._execute_workflow_rules('write')
        
        return result

    # ==================== Action Methods ====================
    def action_assign(self):
        """Assign ticket to current user"""
        self.write({
            'user_id': self.env.user.id,
            'state': 'assigned',
            'assigned_date': fields.Datetime.now()
        })
        return True

    def action_start_progress(self):
        """Start working on ticket"""
        self.write({
            'state': 'in_progress',
            'last_stage_update': fields.Datetime.now()
        })
        return True

    def action_resolve(self):
        """Mark ticket as resolved"""
        self.write({
            'state': 'resolved',
            'resolved_date': fields.Datetime.now(),
            'last_stage_update': fields.Datetime.now()
        })
        return True

    def action_close(self):
        """Close ticket"""
        self.write({
            'state': 'closed',
            'closed_date': fields.Datetime.now(),
            'last_stage_update': fields.Datetime.now()
        })
        return True

    def action_cancel(self):
        """Cancel ticket"""
        self.write({
            'state': 'cancelled',
            'last_stage_update': fields.Datetime.now()
        })
        return True

    def action_reopen(self):
        """Reopen ticket"""
        self.write({
            'state': 'in_progress',
            'resolved_date': False,
            'closed_date': False,
            'last_stage_update': fields.Datetime.now()
        })
        return True

    def action_set_rating(self, rating, feedback=None):
        """Set customer rating and feedback"""
        self.write({
            'rating': rating,
            'feedback': feedback,
            'feedback_date': fields.Datetime.now()
        })
        return True

    def action_open_linked_records(self):
        """Task 8.4: Open action to view linked records with quick access"""
        self.ensure_one()
        return {
            'name': _('Linked Records'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket.model.link',
            'view_mode': 'tree,form',
            'domain': [('ticket_id', '=', self.id)],
            'context': {
                'default_ticket_id': self.id,
                'from_ticket_id': self.id,
                'from_ticket_number': self.ticket_number,
            },
        }
    
    def action_quick_add_link(self):
        """Task 8.4: Quick action to add a linked record"""
        self.ensure_one()
        return {
            'name': _('Link Record'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket.model.link',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_ticket_id': self.id,
                'from_ticket_id': self.id,
            },
        }
    
    def action_manage_links(self):
        """Task 8.6: Open link management interface"""
        self.ensure_one()
        return {
            'name': _('Manage Linked Records'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket.model.link',
            'view_mode': 'tree,form',
            'domain': [('ticket_id', '=', self.id)],
            'context': {
                'default_ticket_id': self.id,
                'from_ticket_id': self.id,
                'search_default_group_model': 1,
            },
        }

    
    def action_validate_all_links(self):
        """Task 8.6: Validate all links for this ticket"""
        self.ensure_one()
        link_ids = self.model_link_ids.ids
        if not link_ids:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Links'),
                    'message': _('No links to validate.'),
                    'type': 'warning',
                    'sticky': False,
                }
            }
        return self.env['helpdesk.ticket.model.link'].action_bulk_validate(link_ids)

    def action_change_status_wizard(self):
        """Open status change wizard"""
        self.ensure_one()
        return {
            'name': _('Change Status'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket.status.change.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_ticket_id': self.id,
                'default_old_state': self.state,
            }
        }

    def action_view_status_history(self):
        """View status history"""
        self.ensure_one()
        return {
            'name': _('Status History'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket.status.history',
            'view_mode': 'tree,form',
            'domain': [('ticket_id', '=', self.id)],
            'context': {'default_ticket_id': self.id},
        }
    
    def action_view_assignment_history(self):
        """View assignment history"""
        self.ensure_one()
        return {
            'name': _('Assignment History'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket.assignment.history',
            'view_mode': 'tree,form',
            'domain': [('ticket_id', '=', self.id)],
            'context': {'default_ticket_id': self.id},
        }
    
    def action_view_notification_history(self):
        """View notification history"""
        self.ensure_one()
        return {
            'name': _('Notification History'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.notification.history',
            'view_mode': 'tree,form',
            'domain': [('ticket_id', '=', self.id)],
            'context': {'default_ticket_id': self.id},
        }
    
    def _get_team_assigned_user(self, ticket, team, algorithm):
        """
        Get user to assign from team using algorithm (helper method)
        
        :param ticket: The ticket to assign
        :param team: The team to assign from
        :param algorithm: The algorithm to use
        :return: res.users record or False
        """
        if not team or not team.member_ids:
            return False
        
        members = team.member_ids.filtered(lambda u: u.active)
        if not members:
            return False
        
        # Use workflow rule's assignment methods
        rule = self.env['helpdesk.workflow.rule']
        if algorithm == 'round_robin':
            return rule._assign_round_robin(ticket, members)
        elif algorithm == 'workload_based':
            return rule._assign_workload_based(ticket, members)
        elif algorithm == 'skill_based':
            return rule._assign_skill_based(ticket, members)
        
        return False

    # ==================== Knowledge Base Integration Actions ====================
    def action_view_knowledge_articles(self):
        """View linked knowledge base articles"""
        self.ensure_one()
        return {
            'name': _('Linked Articles'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.knowledge.article',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.knowledge_article_ids.ids)],
            'context': {'create': False},
        }
    
    def action_create_article_from_ticket(self):
        """Create knowledge base article from ticket"""
        self.ensure_one()
        KnowledgeArticle = self.env['helpdesk.knowledge.article']
        return {
            'name': _('Create Article from Ticket'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.knowledge.article',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_name': self.name,
                'default_content': self.description or '',
                'default_category_id': self.category_id.id if self.category_id else False,
                'default_tag_ids': [(6, 0, self.tag_ids.ids)],
                'default_ticket_ids': [(6, 0, [self.id])],
                'default_author_id': self.env.user.id,
            }
        }
    
    def action_link_article(self, article_id=None):
        """Link a knowledge base article to this ticket"""
        self.ensure_one()
        if not article_id:
            # Try to get from context
            article_id = self.env.context.get('article_id')
        if article_id:
            article = self.env['helpdesk.knowledge.article'].browse(article_id)
            if article.exists():
                self.write({
                    'knowledge_article_ids': [(4, article_id)]
                })
                # Also link ticket to article
                article.write({
                    'ticket_ids': [(4, self.id)]
                })
        return True
    
    def action_unlink_article(self, article_id=None):
        """Unlink a knowledge base article from this ticket"""
        self.ensure_one()
        if not article_id:
            # Try to get from context
            article_id = self.env.context.get('article_id')
        if article_id:
            article = self.env['helpdesk.knowledge.article'].browse(article_id)
            if article.exists():
                self.write({
                    'knowledge_article_ids': [(3, article_id)]
                })
                # Also unlink ticket from article
                article.write({
                    'ticket_ids': [(3, self.id)]
                })
        return True

    # ==================== Workflow Validation ====================
    def _validate_state_transition(self, old_state, new_state):
        """Validate state transition"""
        allowed_transitions = {
            'draft': ['new', 'cancelled'],
            'new': ['assigned', 'in_progress', 'cancelled'],
            'assigned': ['in_progress', 'new', 'cancelled'],
            'in_progress': ['resolved', 'assigned', 'cancelled'],
            'resolved': ['closed', 'in_progress', 'cancelled'],
            'closed': ['in_progress'],  # Reopen
            'cancelled': ['new'],  # Reactivate
        }
        
        if old_state in allowed_transitions:
            if new_state not in allowed_transitions[old_state]:
                state_names = dict(self._fields['state'].selection)
                allowed = [state_names[s] for s in allowed_transitions[old_state]]
                raise ValidationError(_(
                    'Invalid status transition from %s to %s.\n'
                    'Allowed transitions: %s'
                ) % (
                    state_names[old_state],
                    state_names[new_state],
                    ', '.join(allowed)
                ))

    # ==================== Notification Methods ====================
    def _send_ticket_created_notification(self):
        """Send notification when ticket is created"""
        # Check if notifications are enabled (default is True for backward compatibility)
        # Note: This is a general notification, specific notification types have their own toggles
        
        # Use notification template system
        templates = self.env['helpdesk.notification.template'].search([
            ('active', '=', True),
            ('notification_type', '=', 'ticket_created')
        ])
        
        for template in templates:
            template.send_notification(self)
        
        # Fallback to old method if no templates found
        if not templates and self.partner_id and self.partner_id.email:
            # Check if customer notifications are enabled
            if self._get_config_bool('helpdesk.notify_customer_on_update', True):
                template = self.env.ref(
                    'support_helpdesk_ticket.email_template_ticket_created',
                    raise_if_not_found=False
                )
                
                if template:
                    template.send_mail(self.id, force_send=True)
                else:
                    # Fallback: send simple notification
                    subtype = self.env.ref('mail.mt_comment', raise_if_not_found=False)
                    self.message_post(
                        body=_('Ticket Created: %s') % self.ticket_number,
                        subject=_('Ticket Created: %s') % self.ticket_number,
                        partner_ids=[self.partner_id.id],
                        subtype_id=subtype.id if subtype else False,
                    )

    def _send_status_change_notification(self, old_state=None, new_state=None, note=None):
        """Send notification when status changes"""
        # Check if status change notifications are enabled
        if not self._get_config_bool('helpdesk.notify_on_status_change', True):
            return
        
        # Use notification template system
        templates = self.env['helpdesk.notification.template'].search([
            ('active', '=', True),
            ('notification_type', '=', 'ticket_status_change')
        ])
        
        context = {
            'old_state': old_state,
            'new_state': new_state,
            'note': note,
        }
        
        for template in templates:
            template.send_notification(self, context)
        
        # Fallback to old method if no templates found
        if not templates and self.partner_id and self.partner_id.email:
            # Check if customer notifications are enabled
            if self._get_config_bool('helpdesk.notify_customer_on_update', True):
                template = self.env.ref(
                    'support_helpdesk_ticket.email_template_ticket_status_change',
                raise_if_not_found=False
            )
            
            if template:
                template.send_mail(self.id, force_send=True)
            else:
                # Fallback: send simple notification
                state_names = dict(self._fields['state'].selection)
                subject = _('Ticket Status Updated: %s -> %s') % (
                    state_names.get(old_state, old_state),
                    state_names.get(new_state, new_state)
                )
                subtype = self.env.ref('mail.mt_comment', raise_if_not_found=False)
                self.message_post(
                    body=subject,
                    subject=subject,
                    partner_ids=[self.partner_id.id],
                    subtype_id=subtype.id if subtype else False,
                )

    def _send_assignment_notification(self):
        """Send notification when ticket is assigned"""
        # Check if assignment notifications are enabled
        if not self._get_config_bool('helpdesk.notify_on_assignment', True):
            return
        
        # Use notification template system
        templates = self.env['helpdesk.notification.template'].search([
            ('active', '=', True),
            ('notification_type', '=', 'ticket_assigned')
        ])
        
        for template in templates:
            template.send_notification(self)
        
        # Fallback to old method if no templates found
        if not templates and self.user_id and self.user_id.email:
            template = self.env.ref(
                'support_helpdesk_ticket.email_template_ticket_assigned',
                raise_if_not_found=False
            )
            
            if template:
                template.send_mail(self.id, force_send=True)
            else:
                # Fallback notification
                subtype = self.env.ref('mail.mt_comment', raise_if_not_found=False)
                self.message_post(
                    body=_('Ticket Assigned: %s') % self.ticket_number,
                    subject=_('Ticket Assigned: %s') % self.ticket_number,
                    partner_ids=[self.user_id.partner_id.id],
                    subtype_id=subtype.id if subtype else False,
                )
    
    def _send_notification(self, notification_type, context=None):
        """
        Send notification using notification template system
        
        :param notification_type: Type of notification
        :param context: Additional context
        """
        templates = self.env['helpdesk.notification.template'].search([
            ('active', '=', True),
            ('notification_type', '=', notification_type)
        ])
        
        for template in templates:
            template.send_notification(self, context or {})

    def _notify_team_status_change(self, old_state=None, new_state=None, note=None):
        """Notify team members about status change"""
        if not self.team_id or not self.team_id.member_ids:
            return
        
        # TODO: Implement team notification in Task 4.1
        pass

    # ==================== Priority-Based Methods ====================
    def _assign_sla_policy(self):
        """Assign SLA policy to ticket based on matching rules"""
        for ticket in self:
            if ticket.sla_policy_id:
                continue
            
            # Task 9.2: Check type-based SLA first (highest priority)
            if ticket.ticket_type_id and ticket.ticket_type_id.default_sla_policy_id:
                ticket.sla_policy_id = ticket.ticket_type_id.default_sla_policy_id.id
                ticket._calculate_sla_deadlines()
                continue
            
            # Check config default SLA policy (second priority)
            default_sla_policy_id = ticket._get_config_param('helpdesk.default_sla_policy_id', False)
            if default_sla_policy_id:
                try:
                    policy = self.env['helpdesk.sla.policy'].browse(int(default_sla_policy_id))
                    if policy.exists():
                        ticket.sla_policy_id = policy.id
                        ticket._calculate_sla_deadlines()
                        continue
                except (ValueError, TypeError):
                    pass
            
            # Find matching policy using the policy model's matching logic (lowest priority)
            policy = self.env['helpdesk.sla.policy']._find_matching_policy(ticket)
            if policy:
                ticket.sla_policy_id = policy.id
                # Recalculate deadlines with new policy
                ticket._calculate_sla_deadlines()
            else:
                # If no policy found, use default response/resolution times from config
                default_response_time = ticket._get_config_param('helpdesk.default_response_time', False)
                default_resolution_time = ticket._get_config_param('helpdesk.default_resolution_time', False)
                if default_response_time or default_resolution_time:
                    # Create a temporary policy-like structure for deadline calculation
                    # Note: This doesn't create a policy record, just uses the times
                    now = fields.Datetime.now()
                    if default_response_time:
                        try:
                            ticket.sla_response_deadline = now + timedelta(hours=float(default_response_time))
                        except (ValueError, TypeError):
                            pass
                    if default_resolution_time:
                        try:
                            ticket.sla_resolution_deadline = now + timedelta(hours=float(default_resolution_time))
                        except (ValueError, TypeError):
                            pass

    def _assign_sla_by_priority(self, priority=None):
        """Assign SLA policy based on priority (legacy method - use _assign_sla_policy instead)"""
        # This method is kept for backward compatibility
        # New implementation uses _assign_sla_policy which supports all rule types
        self._assign_sla_policy()
    
    def _calculate_sla_deadlines(self):
        """Calculate SLA response and resolution deadlines"""
        if not self.sla_policy_id:
            return
        
        policy = self.sla_policy_id
        now = fields.Datetime.now()
        
        # Get timezone context for working hours calculation
        tz_name = policy.timezone or 'UTC'
        
        # Check if working hours should be used (config override or policy setting)
        use_working_hours = self._get_config_bool('helpdesk.sla_working_hours', False)
        if not use_working_hours:
            use_working_hours = policy.working_hours and policy.working_hours_id
        
        # Calculate response deadline
        if policy.response_time:
            if use_working_hours and policy.working_hours_id:
                # Use working hours calculation with timezone support
                self.sla_response_deadline = self._calculate_working_hours_deadline(
                    now, policy.response_time, policy.working_hours_id, tz_name
                )
            else:
                # Simple time delta
                self.sla_response_deadline = now + timedelta(hours=policy.response_time)
        
        # Calculate resolution deadline
        if policy.resolution_time:
            if use_working_hours and policy.working_hours_id:
                # Use working hours calculation with timezone support
                self.sla_resolution_deadline = self._calculate_working_hours_deadline(
                    now, policy.resolution_time, policy.working_hours_id, tz_name
                )
            else:
                # Simple time delta
                self.sla_resolution_deadline = now + timedelta(hours=policy.resolution_time)

    def _calculate_working_hours_deadline(self, start_time, hours, calendar, tz_name='UTC'):
        """Calculate deadline based on working hours calendar with timezone support"""
        if not calendar:
            return start_time + timedelta(hours=hours)
        
        # Use Odoo's resource.calendar to calculate working hours
        try:
            calendar_obj = self.env['resource.calendar'].browse(calendar.id)
            
            # Convert start_time to timezone if needed
            if tz_name and tz_name != 'UTC':
                try:
                    # Try using zoneinfo (Python 3.9+) first
                    try:
                        from zoneinfo import ZoneInfo
                        utc_tz = ZoneInfo('UTC')
                        policy_tz = ZoneInfo(tz_name)
                        utc_dt = start_time.replace(tzinfo=utc_tz)
                        local_dt = utc_dt.astimezone(policy_tz)
                        start_time_local = local_dt.replace(tzinfo=None)
                    except ImportError:
                        # Fallback to pytz
                        import pytz
                        from pytz import timezone as tz
                        utc_tz = pytz.UTC
                        policy_tz = tz(tz_name)
                        utc_dt = utc_tz.localize(start_time.replace(tzinfo=None))
                        local_dt = utc_dt.astimezone(policy_tz)
                        start_time_local = local_dt.replace(tzinfo=None)
                except Exception as e:
                    _logger.warning('Error converting timezone: %s', str(e))
                    start_time_local = start_time
            else:
                start_time_local = start_time
            
            # Use Odoo's built-in method to calculate deadline based on working hours
            # This properly accounts for weekends, holidays, and business hours
            if hasattr(calendar_obj, 'plan_hours'):
                deadline_local = calendar_obj.plan_hours(hours, start_time_local, compute_leaves=True)
            else:
                # Fallback: calculate manually
                deadline_local = self._calculate_working_hours_manual(start_time_local, hours, calendar)
            
            # Convert back to UTC if timezone was used
            if tz_name and tz_name != 'UTC':
                try:
                    # Try using zoneinfo (Python 3.9+) first
                    try:
                        from zoneinfo import ZoneInfo
                        policy_tz = ZoneInfo(tz_name)
                        utc_tz = ZoneInfo('UTC')
                        local_dt = deadline_local.replace(tzinfo=policy_tz)
                        utc_dt = local_dt.astimezone(utc_tz)
                        return utc_dt.replace(tzinfo=None)
                    except ImportError:
                        # Fallback to pytz
                        import pytz
                        from pytz import timezone as tz
                        policy_tz = tz(tz_name)
                        local_dt = policy_tz.localize(deadline_local.replace(tzinfo=None))
                        utc_dt = local_dt.astimezone(pytz.UTC)
                        return utc_dt.replace(tzinfo=None)
                except Exception as e:
                    _logger.warning('Error converting timezone back to UTC: %s', str(e))
                    return deadline_local
            
            return deadline_local
        except Exception as e:
            _logger.warning('Error calculating working hours deadline: %s', str(e))
            # Fallback to simple calculation
            return start_time + timedelta(hours=hours)

    def _calculate_working_hours_manual(self, start_time, hours, calendar):
        """Manual calculation of working hours deadline (fallback method)"""
        try:
            calendar_obj = self.env['resource.calendar'].browse(calendar.id)
            
            # Get calendar working hours
            if calendar_obj.attendance_ids:
                # Calculate average working hours per day
                total_hours = 0
                days = set()
                for attendance in calendar_obj.attendance_ids:
                    if attendance.dayofweek not in days:
                        hours_per_day = (attendance.hour_to - attendance.hour_from)
                        total_hours += hours_per_day
                        days.add(attendance.dayofweek)
                
                if total_hours > 0:
                    avg_hours_per_day = total_hours / max(len(days), 1)
                    days_needed = hours / avg_hours_per_day
                    
                    # Add days, skipping weekends if calendar doesn't include them
                    current = start_time
                    days_added = 0
                    while days_added < days_needed:
                        current += timedelta(days=1)
                        # Check if it's a working day (simplified - doesn't check holidays)
                        weekday = current.weekday()
                        # Check if calendar has attendance for this weekday
                        has_attendance = any(
                            att.dayofweek == str(weekday) 
                            for att in calendar_obj.attendance_ids
                        )
                        if has_attendance:
                            days_added += 1
                    
                    return current
            else:
                # No attendance defined, use default 8 hours per day
                days_needed = hours / 8.0
                return start_time + timedelta(days=days_needed)
        except Exception:
            # Final fallback
            return start_time + timedelta(hours=hours)

    def action_set_priority(self, priority):
        """Set ticket priority"""
        self.write({
            'priority': priority,
            'old_priority': self.priority,
            'priority_change_date': fields.Datetime.now()
        })
        return True

    def action_increase_priority(self):
        """Increase ticket priority"""
        priority_map = {
            '0': '1',  # Low -> Medium
            '1': '2',  # Medium -> High
            '2': '3',  # High -> Urgent
            '3': '3',  # Urgent -> Urgent (max)
        }
        new_priority = priority_map.get(self.priority, self.priority)
        if new_priority != self.priority:
            self.action_set_priority(new_priority)
        return True

    def action_decrease_priority(self):
        """Decrease ticket priority"""
        priority_map = {
            '3': '2',  # Urgent -> High
            '2': '1',  # High -> Medium
            '1': '0',  # Medium -> Low
            '0': '0',  # Low -> Low (min)
        }
        new_priority = priority_map.get(self.priority, self.priority)
        if new_priority != self.priority:
            self.action_set_priority(new_priority)
        return True

    def action_apply_template(self):
        """Open template selection wizard"""
        self.ensure_one()
        return {
            'name': _('Apply Template'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket.template.apply.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_ticket_id': self.id,
            }
        }

    def action_merge_tickets(self):
        """Open merge wizard"""
        self.ensure_one()
        return {
            'name': _('Merge Tickets'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket.merge.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_ticket_id': self.id,
            }
        }

    def action_split_ticket(self):
        """Open split wizard"""
        self.ensure_one()
        return {
            'name': _('Split Ticket'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket.split.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_ticket_id': self.id,
            }
        }

    def action_view_child_tickets(self):
        """View child tickets"""
        self.ensure_one()
        return {
            'name': _('Child Tickets'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket',
            'view_mode': 'tree,form',
            'domain': [('parent_ticket_id', '=', self.id)],
            'context': {'default_parent_ticket_id': self.id},
        }

    def action_view_parent_ticket(self):
        """View parent ticket"""
        self.ensure_one()
        if not self.parent_ticket_id:
            return False
        return {
            'name': _('Parent Ticket'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket',
            'res_id': self.parent_ticket_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    # ==================== Constraints ====================
    @api.constrains('partner_id')
    def _check_partner(self):
        """Ensure partner is set"""
        for ticket in self:
            if not ticket.partner_id:
                raise ValidationError(_('Customer is required for ticket.'))

    @api.constrains('state', 'resolved_date')
    def _check_resolved_state(self):
        """Ensure resolved date is set when state is resolved"""
        for ticket in self:
            if ticket.state == 'resolved' and not ticket.resolved_date:
                ticket.resolved_date = fields.Datetime.now()

    @api.constrains('state')
    def _check_state(self):
        """Validate state transitions"""
        for ticket in self:
            if ticket._origin and ticket._origin.state != ticket.state:
                # Validation is done in write method
                pass

    # ==================== Name Get ====================
    def name_get(self):
        """Return ticket number and name"""
        result = []
        for ticket in self:
            name = ticket.ticket_number
            if ticket.name:
                name = '%s - %s' % (ticket.ticket_number, ticket.name)
            result.append((ticket.id, name))
        return result

    def _get_access_token(self):
        """Generate access token for portal access"""
        self.ensure_one()
        # portal.mixin provides this method automatically
        return super(HelpdeskTicket, self)._get_access_token()

    # ==================== Search Methods ====================
    @api.model
    def search(self, args, offset=0, limit=None, order=None):
        """Override search to handle today filter"""
        if self.env.context.get('search_default_today'):
            today = fields.Date.context_today(self)
            start_of_day = fields.Datetime.to_string(
                datetime.combine(today, time.min)
            )
            end_of_day = fields.Datetime.to_string(
                datetime.combine(today, time.max)
            )
            args = [('create_date', '>=', start_of_day), ('create_date', '<=', end_of_day)] + args

        return super(HelpdeskTicket, self).search(args, offset=offset, limit=limit, order=order)

    # ==================== Workload Fields (for workload view) ====================
    workload_count = fields.Integer(
        string='Workload Count',
        compute='_compute_workload_stats',
        help='Total number of tickets assigned to this user'
    )
    new_count = fields.Integer(
        string='New Count',
        compute='_compute_workload_stats',
        help='Number of new tickets'
    )
    assigned_count = fields.Integer(
        string='Assigned Count',
        compute='_compute_workload_stats',
        help='Number of assigned tickets'
    )
    in_progress_count = fields.Integer(
        string='In Progress Count',
        compute='_compute_workload_stats',
        help='Number of tickets in progress'
    )
    resolved_count = fields.Integer(
        string='Resolved Count',
        compute='_compute_workload_stats',
        help='Number of resolved tickets'
    )
    overdue_count = fields.Integer(
        string='Overdue Count',
        compute='_compute_workload_stats',
        help='Number of overdue tickets'
    )

    @api.depends('user_id', 'state', 'is_overdue')
    def _compute_workload_stats(self):
        """Compute workload statistics for grouping"""
        # This is computed when grouping by user_id
        # The actual computation happens at the view level
        for ticket in self:
            ticket.workload_count = 1 if ticket.user_id else 0
            ticket.new_count = 1 if ticket.state == 'new' else 0
            ticket.assigned_count = 1 if ticket.state == 'assigned' else 0
            ticket.in_progress_count = 1 if ticket.state == 'in_progress' else 0
            ticket.resolved_count = 1 if ticket.state == 'resolved' else 0
            ticket.overdue_count = 1 if ticket.is_overdue else 0

    # ==================== SLA Monitoring & Alerts ====================
    @api.model
    def _check_sla_status(self):
        """Scheduled action to check SLA status and send alerts"""
        # Find all open tickets with SLA policies
        open_tickets = self.search([
            ('state', 'not in', ['resolved', 'closed', 'cancelled']),
            ('sla_policy_id', '!=', False),
        ])
        
        for ticket in open_tickets:
            # Update SLA status (triggers recomputation)
            ticket._compute_sla_status()
            
            # Check and send alerts
            ticket._check_sla_warnings()
            ticket._check_sla_escalations()
            ticket._check_sla_breaches()
            
            # Check and execute escalation rules
            ticket._check_escalation_rules()
            
            # Check and create reminders
            ticket._check_reminder_rules()
        
        return True
    
    def _check_reminder_rules(self):
        """Check reminder rules for ticket"""
        # Check if reminders are enabled
        if not self._get_config_bool('helpdesk.enable_reminders', True):
            return
        """Check and create reminders based on reminder rules"""
        self.ensure_one()
        
        # Search for active reminder rules
        rules = self.env['helpdesk.reminder.rule'].search([
            ('active', '=', True)
        ], order='sequence, id')
        
        for rule in rules:
            try:
                rule.create_reminder(self)
            except Exception as e:
                _logger.error('Error creating reminder from rule %s on ticket %s: %s', rule.name, self.ticket_number, str(e))
    
    @api.model
    def _check_reminder_rules_batch(self):
        """Check reminder rules for all open tickets (batch processing)"""
        # Get open tickets
        open_tickets = self.search([
            ('state', 'not in', ['closed', 'cancelled'])
        ])
        
        for ticket in open_tickets:
            ticket._check_reminder_rules()
    
    # ==================== Auto-Model Linking (Task 8.5) ====================
    def _process_auto_links(self):
        """Process auto-linking rules for this ticket"""
        self.ensure_one()
        
        # Skip if auto-linking is disabled for this ticket
        if self.env.context.get('skip_auto_link'):
            return
        
        # Get active auto-linking rules
        rules = self.env['helpdesk.auto.link.rule'].search([
            ('active', '=', True)
        ], order='sequence, id')
        
        created_links = []
        for rule in rules:
            try:
                links = rule.process_ticket(self)
                created_links.extend(links)
            except Exception as e:
                _logger.error('Error processing auto-link rule %s on ticket %s: %s', 
                            rule.name, self.ticket_number, str(e))
        
        return created_links
    
    def action_manual_auto_link(self):
        """Task 8.5: Manually trigger auto-linking"""
        self.ensure_one()
        created_links = self._process_auto_links()
        
        if created_links:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Auto-Linking Complete'),
                    'message': _('%d record(s) linked automatically.') % len(created_links),
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('No Links Found'),
                    'message': _('No matching records found for auto-linking.'),
                    'type': 'warning',
                    'sticky': False,
                }
            }
    
    def action_create_reminder(self):
        """Create manual reminder for this ticket"""
        self.ensure_one()
        return {
            'name': _('Create Reminder'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.reminder',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_ticket_id': self.id,
                'default_user_id': self.user_id.id if self.user_id else self.env.user.id,
                'default_reminder_type': 'manual',
            },
        }
    
    def action_view_reminders(self):
        """View reminders for this ticket"""
        self.ensure_one()
        return {
            'name': _('Reminders'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.reminder',
            'view_mode': 'tree,form',
            'domain': [('ticket_id', '=', self.id)],
            'context': {'default_ticket_id': self.id},
        }
    
    @api.model
    def _auto_close_resolved_tickets(self):
        """Auto-close resolved tickets based on configuration (batch method for cron)"""
        if not self._get_config_bool('helpdesk.auto_close_resolved', False):
            return
        
        auto_close_days = int(self._get_config_param('helpdesk.auto_close_days', 7))
        cutoff_date = fields.Datetime.now() - timedelta(days=auto_close_days)
        
        resolved_tickets = self.search([
            ('state', '=', 'resolved'),
            ('resolved_date', '<=', cutoff_date),
        ])
        
        for ticket in resolved_tickets:
            ticket.with_context(skip_state_validation=True).write({
                'state': 'closed',
                'closed_date': fields.Datetime.now()
            })
            subtype = self.env.ref('mail.mt_note', raise_if_not_found=False)
            ticket.message_post(
                body=_('Ticket automatically closed after %d days in resolved state.') % auto_close_days,
                subject=_('Auto-Closed'),
                subtype_id=subtype.id if subtype else False
            )
    
    def _check_escalation_rules(self):
        """Check escalation rules for ticket"""
        # Check if escalation is enabled
        if not self._get_config_bool('helpdesk.enable_escalation', True):
            return
        """Check and execute escalation rules for this ticket"""
        self.ensure_one()
        
        # Search for active escalation rules
        rules = self.env['helpdesk.escalation.rule'].search([
            ('active', '=', True)
        ], order='sequence, escalation_level, id')
        
        for rule in rules:
            try:
                # Check if rule should execute
                if rule._evaluate_condition(self) and rule._evaluate_trigger(self):
                    # Check if already escalated at this level
                    last_escalation = self.env['helpdesk.escalation.log'].search([
                        ('rule_id', '=', rule.id),
                        ('ticket_id', '=', self.id),
                    ], order='escalation_date desc', limit=1)
                    
                    if not last_escalation or rule.repeat_escalation:
                        # Check repeat interval if repeat is enabled
                        if last_escalation and rule.repeat_escalation:
                            hours_since = (fields.Datetime.now() - last_escalation.escalation_date).total_seconds() / 3600.0
                            if hours_since < rule.repeat_interval_hours:
                                continue
                            
                            # Check max repeats
                            escalation_count = self.env['helpdesk.escalation.log'].search_count([
                                ('rule_id', '=', rule.id),
                                ('ticket_id', '=', self.id),
                            ])
                            if escalation_count >= rule.max_repeats:
                                continue
                        
                        # Execute escalation rule
                        rule.execute_on_ticket(self)
            except Exception as e:
                _logger.error('Error executing escalation rule %s on ticket %s: %s', rule.name, self.ticket_number, str(e))

    def _check_sla_warnings(self):
        """Check if ticket is at warning threshold of SLA time and send warning alerts"""
        self.ensure_one()
        if not self.sla_policy_id:
            return
        
        now = fields.Datetime.now()
        policy = self.sla_policy_id
        
        # Check response SLA warning (using policy threshold)
        if self.sla_response_deadline and not self.assigned_date:
            elapsed = (now - self.create_date).total_seconds() / 3600.0  # hours
            total_time = policy.response_time
            percentage = (elapsed / total_time) * 100 if total_time > 0 else 0
            warning_threshold = policy.response_warning_threshold or 80.0
            escalation_threshold = policy.response_escalation_threshold or 90.0
            
            if percentage >= warning_threshold and percentage < escalation_threshold:
                # Check if we already sent warning (check last message)
                last_warning = self.message_ids.filtered(
                    lambda m: 'SLA Warning' in (m.subject or '')
                )[:1]
                if not last_warning or (now - last_warning.date).total_seconds() > 3600:  # Don't spam, max once per hour
                    self._send_sla_warning_alert('response', percentage)
        
        # Check resolution SLA warning (using policy threshold)
        if self.sla_resolution_deadline and self.state not in ['resolved', 'closed']:
            elapsed = (now - self.create_date).total_seconds() / 3600.0  # hours
            total_time = policy.resolution_time
            percentage = (elapsed / total_time) * 100 if total_time > 0 else 0
            warning_threshold = policy.resolution_warning_threshold or 80.0
            escalation_threshold = policy.resolution_escalation_threshold or 90.0
            
            if percentage >= warning_threshold and percentage < escalation_threshold:
                # Check if we already sent warning
                last_warning = self.message_ids.filtered(
                    lambda m: 'SLA Warning' in (m.subject or '')
                )[:1]
                if not last_warning or (now - last_warning.date).total_seconds() > 3600:
                    self._send_sla_warning_alert('resolution', percentage)

    def _check_sla_escalations(self):
        """Check if ticket is at escalation threshold of SLA time and send escalation alerts"""
        self.ensure_one()
        if not self.sla_policy_id:
            return
        
        now = fields.Datetime.now()
        policy = self.sla_policy_id
        
        # Check response SLA escalation (using policy threshold)
        if self.sla_response_deadline and not self.assigned_date:
            elapsed = (now - self.create_date).total_seconds() / 3600.0  # hours
            total_time = policy.response_time
            percentage = (elapsed / total_time) * 100 if total_time > 0 else 0
            escalation_threshold = policy.response_escalation_threshold or 90.0
            
            if percentage >= escalation_threshold and percentage < 100:
                # Check if we already sent escalation
                last_escalation = self.message_ids.filtered(
                    lambda m: 'SLA Escalation' in (m.subject or '')
                )[:1]
                if not last_escalation or (now - last_escalation.date).total_seconds() > 3600:
                    self._send_sla_escalation_alert('response', percentage)
        
        # Check resolution SLA escalation (using policy threshold)
        if self.sla_resolution_deadline and self.state not in ['resolved', 'closed']:
            elapsed = (now - self.create_date).total_seconds() / 3600.0  # hours
            total_time = policy.resolution_time
            percentage = (elapsed / total_time) * 100 if total_time > 0 else 0
            escalation_threshold = policy.resolution_escalation_threshold or 90.0
            
            if percentage >= escalation_threshold and percentage < 100:
                # Check if we already sent escalation
                last_escalation = self.message_ids.filtered(
                    lambda m: 'SLA Escalation' in (m.subject or '')
                )[:1]
                if not last_escalation or (now - last_escalation.date).total_seconds() > 3600:
                    self._send_sla_escalation_alert('resolution', percentage)

    def _check_sla_breaches(self):
        """Check if SLA has been breached and handle breach"""
        self.ensure_one()
        if not self.sla_policy_id:
            return
        
        now = fields.Datetime.now()
        
        # Check response SLA breach
        if self.sla_response_deadline and self.sla_response_deadline < now:
            if not self.assigned_date or self.assigned_date > self.sla_response_deadline:
                # Check if we already sent breach notification
                last_breach = self.message_ids.filtered(
                    lambda m: 'SLA Breach' in (m.subject or '') and 'response' in (m.body or '').lower()
                )[:1]
                if not last_breach:
                    self._handle_sla_breach('response')
        
        # Check resolution SLA breach
        if self.sla_resolution_deadline and self.sla_resolution_deadline < now:
            if self.state not in ['resolved', 'closed']:
                # Check if we already sent breach notification
                last_breach = self.message_ids.filtered(
                    lambda m: 'SLA Breach' in (m.subject or '') and 'resolution' in (m.body or '').lower()
                )[:1]
                if not last_breach:
                    self._handle_sla_breach('resolution')

    def _send_sla_warning_alert(self, sla_type, percentage):
        """Send warning alert at 80% of SLA time"""
        self.ensure_one()
        
        sla_name = 'Response' if sla_type == 'response' else 'Resolution'
        deadline = self.sla_response_deadline if sla_type == 'response' else self.sla_resolution_deadline
        
        # Email to assigned agent
        if self.user_id and self.user_id.email:
            self._send_sla_email(
                self.user_id,
                'warning',
                sla_type,
                percentage,
                deadline
            )
        
        # Email to supervisor/team leader
        if self.team_id and self.team_id.team_leader_id and self.team_id.team_leader_id.email:
            if self.team_id.team_leader_id != self.user_id:  # Don't send duplicate
                self._send_sla_email(
                    self.team_id.team_leader_id,
                    'warning',
                    sla_type,
                    percentage,
                    deadline
                )
        
        # Post message on ticket
        self.message_post(
            body=_('⚠️ <b>SLA Warning:</b> %s SLA is at %d%% of allocated time. Deadline: %s') % (
                sla_name,
                int(percentage),
                deadline.strftime('%Y-%m-%d %H:%M:%S') if deadline else 'N/A'
            ),
            subject=_('SLA Warning Alert'),
            message_type='notification',
        )

    def _send_sla_escalation_alert(self, sla_type, percentage):
        """Send escalation alert at 90% of SLA time"""
        self.ensure_one()
        policy = self.sla_policy_id
        
        sla_name = 'Response' if sla_type == 'response' else 'Resolution'
        deadline = self.sla_response_deadline if sla_type == 'response' else self.sla_resolution_deadline
        
        # Auto-escalate if policy is configured
        if policy.auto_escalate:
            # Escalate to supervisor/team leader
            if policy.escalation_team_id and policy.escalation_team_id.team_leader_id:
                self.write({
                    'team_id': policy.escalation_team_id.id,
                    'user_id': policy.escalation_team_id.team_leader_id.id,
                })
            elif self.team_id and self.team_id.team_leader_id:
                self.write({'user_id': self.team_id.team_leader_id.id})
            
            # Priority upgrade option
            if self.priority in ['0', '1']:
                # Increase priority by one level
                priority_map = {'0': '1', '1': '2'}
                new_priority = priority_map.get(self.priority, self.priority)
                self.write({'priority': new_priority})
        
        # Email to management/escalation user
        escalation_users = []
        if policy.escalation_user_id:
            escalation_users.append(policy.escalation_user_id)
        if self.team_id and self.team_id.team_leader_id:
            escalation_users.append(self.team_id.team_leader_id)
        
        for user in escalation_users:
            if user.email:
                self._send_sla_email(
                    user,
                    'escalation',
                    sla_type,
                    percentage,
                    deadline
                )
        
        # Post message on ticket
        self.message_post(
            body=_('🚨 <b>SLA Escalation:</b> %s SLA is at %d%% of allocated time. Ticket has been escalated. Deadline: %s') % (
                sla_name,
                int(percentage),
                deadline.strftime('%Y-%m-%d %H:%M:%S') if deadline else 'N/A'
            ),
            subject=_('SLA Escalation Alert'),
            message_type='notification',
        )

    def _handle_sla_breach(self, sla_type):
        """Handle SLA breach"""
        # Check if SLA breach notifications are enabled
        if not self._get_config_bool('helpdesk.notify_on_sla_breach', True):
            return
        self.ensure_one()
        policy = self.sla_policy_id
        
        sla_name = 'Response' if sla_type == 'response' else 'Resolution'
        deadline = self.sla_response_deadline if sla_type == 'response' else self.sla_resolution_deadline
        
        # Log breach
        self.env['helpdesk.ticket.status.history'].create({
            'ticket_id': self.id,
            'old_state': self.state,
            'new_state': self.state,
            'user_id': self.env.user.id,
            'reason': 'sla',
            'note': _('SLA Breach: %s deadline exceeded') % sla_name,
        })
        
        # Breach notification to escalation users
        escalation_users = []
        if policy and policy.escalation_user_id:
            escalation_users.append(policy.escalation_user_id)
        if self.team_id and self.team_id.team_leader_id:
            escalation_users.append(self.team_id.team_leader_id)
        if self.user_id:
            escalation_users.append(self.user_id)
        
        for user in escalation_users:
            if user.email:
                self._send_sla_email(
                    user,
                    'breach',
                    sla_type,
                    100,
                    deadline
                )
        
        # Customer notification (optional - can be configured)
        if self.partner_id and self.partner_id.email:
            # Only send if configured in SLA policy
            # For now, we'll skip customer notification by default
            pass
        
        # Post message on ticket
        self.message_post(
            body=_('❌ <b>SLA Breach:</b> %s SLA deadline has been exceeded. Deadline was: %s') % (
                sla_name,
                deadline.strftime('%Y-%m-%d %H:%M:%S') if deadline else 'N/A'
            ),
            subject=_('SLA Breach Notification'),
            message_type='notification',
        )

    def _send_sla_email(self, user, alert_type, sla_type, percentage, deadline):
        """Send SLA alert email to user"""
        self.ensure_one()
        
        sla_name = 'Response' if sla_type == 'response' else 'Resolution'
        
        if alert_type == 'warning':
            subject = _('SLA Warning: Ticket #%s - %s SLA at %d%%') % (
                self.ticket_number, sla_name, int(percentage)
            )
            body = _('''
                <p>This is a warning that ticket <b>#%s</b> is approaching its SLA deadline.</p>
                <p><b>Ticket:</b> %s</p>
                <p><b>SLA Type:</b> %s</p>
                <p><b>Progress:</b> %d%% of allocated time elapsed</p>
                <p><b>Deadline:</b> %s</p>
                <p>Please take action to ensure the SLA is met.</p>
            ''') % (
                self.ticket_number,
                self.name,
                sla_name,
                int(percentage),
                deadline.strftime('%Y-%m-%d %H:%M:%S') if deadline else 'N/A'
            )
        elif alert_type == 'escalation':
            subject = _('SLA Escalation: Ticket #%s - %s SLA at %d%%') % (
                self.ticket_number, sla_name, int(percentage)
            )
            body = _('''
                <p>This ticket has been escalated due to approaching SLA deadline.</p>
                <p><b>Ticket:</b> #%s - %s</p>
                <p><b>SLA Type:</b> %s</p>
                <p><b>Progress:</b> %d%% of allocated time elapsed</p>
                <p><b>Deadline:</b> %s</p>
                <p>Immediate action is required.</p>
            ''') % (
                self.ticket_number,
                self.name,
                sla_name,
                int(percentage),
                deadline.strftime('%Y-%m-%d %H:%M:%S') if deadline else 'N/A'
            )
        else:  # breach
            subject = _('SLA Breach: Ticket #%s - %s SLA Exceeded') % (
                self.ticket_number, sla_name
            )
            body = _('''
                <p><b>ALERT:</b> Ticket #%s has breached its SLA deadline.</p>
                <p><b>Ticket:</b> %s</p>
                <p><b>SLA Type:</b> %s</p>
                <p><b>Deadline:</b> %s</p>
                <p><b>Current Status:</b> %s</p>
                <p>This requires immediate attention.</p>
            ''') % (
                self.ticket_number,
                self.name,
                sla_name,
                deadline.strftime('%Y-%m-%d %H:%M:%S') if deadline else 'N/A',
                dict(self._fields['state'].selection)[self.state]
            )
        
        # Send email
        try:
            mail_values = {
                'subject': subject,
                'body_html': body,
                'email_to': user.email,
                'email_from': self.env.user.email or self.env.company.email or 'noreply@odoo.com',
                'model': self._name,
                'res_id': self.id,
                'auto_delete': True,
            }
            mail = self.env['mail.mail'].sudo().create(mail_values)
            mail.send()
        except Exception as e:
            # Log error but don't fail
            _logger.error('Failed to send SLA email to %s: %s', user.email, str(e))
