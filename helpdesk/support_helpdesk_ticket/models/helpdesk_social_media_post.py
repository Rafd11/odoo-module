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
from datetime import datetime, time


class HelpdeskSocialMediaPost(models.Model):
    _name = 'helpdesk.social.media.post'
    _description = 'Social Media Post/Message'
    _order = 'post_date desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # ==================== Basic Fields ====================
    name = fields.Char(
        string='Reference',
        readonly=True,
        compute='_compute_name',
        store=True,
        help='Reference for this post'
    )
    platform_id = fields.Many2one(
        'helpdesk.social.media.platform',
        string='Platform',
        required=True,
        tracking=True,
        index=True,
        ondelete='cascade',
        help='Social media platform this post is from'
    )
    platform_type = fields.Selection(
        related='platform_id.platform_type',
        string='Platform Type',
        readonly=True,
        store=True,
        help='Type of platform'
    )

    # ==================== Post Information ====================
    post_id = fields.Char(
        string='Social Media Post ID',
        required=True,
        index=True,
        help='Unique ID of the post from the social media platform'
    )
    post_type = fields.Selection(
        [
            ('post', 'Post'),
            ('message', 'Direct Message'),
            ('comment', 'Comment'),
            ('mention', 'Mention'),
            ('reply', 'Reply'),
        ],
        string='Post Type',
        required=True,
        default='post',
        tracking=True,
        help='Type of social media interaction'
    )
    content = fields.Html(
        string='Content',
        required=True,
        help='Content of the post or message'
    )
    post_date = fields.Datetime(
        string='Post Date',
        required=True,
        default=fields.Datetime.now,
        tracking=True,
        index=True,
        help='Date and time when the post was created on the platform'
    )
    url = fields.Char(
        string='Post URL',
        help='URL to view the post on the social media platform'
    )

    # ==================== Author Information ====================
    author_id = fields.Many2one(
        'res.partner',
        string='Author',
        tracking=True,
        index=True,
        ondelete='set null',
        help='Contact/Partner who created this post'
    )
    author_name = fields.Char(
        string='Author Name',
        help='Name of the author from social media'
    )
    author_username = fields.Char(
        string='Author Username',
        help='Username/handle of the author'
    )
    author_social_id = fields.Char(
        string='Author Social ID',
        help='Author ID from the social media platform'
    )
    author_email = fields.Char(
        string='Author Email',
        help='Email address of the author (if available)'
    )
    author_phone = fields.Char(
        string='Author Phone',
        help='Phone number of the author (if available)'
    )

    # ==================== Ticket Relationship ====================
    ticket_id = fields.Many2one(
        'helpdesk.ticket',
        string='Related Ticket',
        tracking=True,
        index=True,
        ondelete='set null',
        help='Ticket created from or linked to this post'
    )
    ticket_number = fields.Char(
        string='Ticket Number',
        related='ticket_id.ticket_number',
        readonly=True,
        store=True,
        help='Related ticket number'
    )

    # ==================== Status ====================
    state = fields.Selection(
        [
            ('new', 'New'),
            ('processing', 'Processing'),
            ('ticket_created', 'Ticket Created'),
            ('linked', 'Linked to Ticket'),
            ('ignored', 'Ignored'),
        ],
        string='Status',
        default='new',
        required=True,
        tracking=True,
        help='Processing status of this post'
    )
    processed_date = fields.Datetime(
        string='Processed Date',
        readonly=True,
        help='Date when this post was processed'
    )

    # ==================== Media Attachments ====================
    has_media = fields.Boolean(
        string='Has Media',
        compute='_compute_has_media',
        help='True if post contains media attachments'
    )
    media_urls = fields.Text(
        string='Media URLs',
        help='URLs of media attachments (images, videos, etc.)'
    )

    # ==================== Threading ====================
    parent_post_id = fields.Many2one(
        'helpdesk.social.media.post',
        string='Parent Post',
        ondelete='cascade',
        help='Parent post if this is a comment or reply'
    )
    child_post_ids = fields.One2many(
        'helpdesk.social.media.post',
        'parent_post_id',
        string='Replies/Comments',
        help='Child posts (comments or replies)'
    )
    is_thread_root = fields.Boolean(
        string='Is Thread Root',
        compute='_compute_is_thread_root',
        help='True if this is the root post of a thread'
    )

    # ==================== Computed Fields ====================
    @api.depends('platform_id', 'post_id')
    def _compute_name(self):
        """Generate reference name"""
        for record in self:
            if record.platform_id and record.post_id:
                record.name = f"{record.platform_id.name}/{record.post_id[:20]}"
            else:
                record.name = _('New')

    @api.depends('media_urls')
    def _compute_has_media(self):
        """Check if post has media"""
        for record in self:
            record.has_media = bool(record.media_urls and record.media_urls.strip())

    @api.depends('parent_post_id')
    def _compute_is_thread_root(self):
        """Check if this is a thread root"""
        for record in self:
            record.is_thread_root = not bool(record.parent_post_id)

    # ==================== Actions ====================
    def action_create_ticket(self):
        """Create ticket from this post"""
        self.ensure_one()
        action = {
            'name': _('Create Ticket from Post'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.social.media.post.create.ticket.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_post_id': self.id,
                'default_platform_id': self.platform_id.id,
                'default_author_id': self.author_id.id if self.author_id else False,
                'default_content': self.content,
            },
        }
        return action

    def action_link_ticket(self):
        """Link this post to an existing ticket"""
        self.ensure_one()
        action = {
            'name': _('Link Ticket'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket',
            'view_mode': 'tree,form',
            'domain': [('channel_id.code', '=', 'social_media')],
            'context': {
                'default_channel_id': self.env['helpdesk.channel'].search([('code', '=', 'social_media')], limit=1).id or False,
                'default_partner_id': self.author_id.id if self.author_id else False,
                'default_social_media_post_id': self.id,
            },
            'target': 'current',
        }
        return action

    def action_view_ticket(self):
        """View related ticket"""
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

    def action_ignore(self):
        """Mark post as ignored"""
        self.write({
            'state': 'ignored',
            'processed_date': fields.Datetime.now(),
        })

    def action_find_or_create_partner(self):
        """Find or create partner from author information"""
        self.ensure_one()
        partner = False
        
        # Try to find by email
        if self.author_email:
            partner = self.env['res.partner'].search([
                ('email', '=', self.author_email)
            ], limit=1)
        
        # Try to find by social ID
        if not partner and self.author_social_id:
            partner = self.env['res.partner'].search([
                ('x_social_media_id', '=', self.author_social_id)
            ], limit=1)
        
        # Create new partner if not found
        if not partner:
            partner_vals = {
                'name': self.author_name or self.author_username or _('Unknown'),
                'is_company': False,
            }
            if self.author_email:
                partner_vals['email'] = self.author_email
            if self.author_phone:
                partner_vals['phone'] = self.author_phone
            if self.author_social_id:
                partner_vals['x_social_media_id'] = self.author_social_id
            
            partner = self.env['res.partner'].create(partner_vals)
        
        self.author_id = partner.id
        return partner

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to handle post processing (batch-friendly)"""
        # Always work with a list for batch creates
        if not isinstance(vals_list, list):
            vals_list = [vals_list]

        posts = super(HelpdeskSocialMediaPost, self).create(vals_list)

        for post in posts:
            # Auto-create partner if author info available
            if not post.author_id and (post.author_email or post.author_social_id):
                post.action_find_or_create_partner()

            # Auto-create ticket if platform is configured to do so
            if post.platform_id.active and post.state == 'new':
                if post.post_type == 'post' and post.platform_id.monitor_posts:
                    post._auto_create_ticket()
                elif post.post_type == 'message' and post.platform_id.monitor_messages:
                    post._auto_create_ticket()
                elif post.post_type == 'mention' and post.platform_id.monitor_mentions:
                    post._auto_create_ticket()

        return posts

    def _auto_create_ticket(self):
        """Automatically create ticket from post"""
        self.ensure_one()
        if self.ticket_id:
            return self.ticket_id
        
        # Ensure partner exists
        if not self.author_id:
            self.action_find_or_create_partner()
        
        # Prepare ticket values
        ticket_vals = {
            'name': self.content[:100] if self.content else _('Social Media Post'),
            'description': self.content,
            'partner_id': self.author_id.id if self.author_id else False,
            'channel': 'social_media',
            'state': 'new',
            'category_id': self.platform_id.default_category_id.id if self.platform_id.default_category_id else False,
            'priority': self.platform_id.default_priority or '1',
            'team_id': self.platform_id.default_team_id.id if self.platform_id.default_team_id else False,
            'user_id': self.platform_id.default_user_id.id if self.platform_id.default_user_id else False,
        }
        
        # Create ticket
        ticket = self.env['helpdesk.ticket'].create(ticket_vals)
        
        # Link post to ticket
        self.write({
            'ticket_id': ticket.id,
            'state': 'ticket_created',
            'processed_date': fields.Datetime.now(),
        })
        
        # Add message to ticket with post details
        ticket.message_post(
            body=_('Ticket created from %s post: %s') % (self.platform_id.name, self.url or self.post_id),
            subject=_('Social Media Post'),
        )
        
        return ticket

    def action_reply(self):
        """Reply to this social media post"""
        self.ensure_one()
        action = {
            'name': _('Reply to Post'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.social.media.post.reply.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_post_id': self.id,
                'default_platform_id': self.platform_id.id,
            },
        }
        return action

    def send_reply(self, message, reply_type='comment'):
        """Send reply to the post via API"""
        self.ensure_one()
        if not self.platform_id.active or not self.platform_id.access_token:
            raise UserError(_('Platform is not active or access token is missing.'))
        
        api_client = self.platform_id._get_api_client()
        if not api_client:
            raise UserError(_('API client not available for this platform.'))
        
        try:
            if reply_type == 'comment' or self.post_type in ['post', 'comment']:
                result = api_client.reply_to_post(self.post_id, message)
            elif reply_type == 'message' or self.post_type == 'message':
                if not self.author_social_id:
                    raise UserError(_('Author social ID is required to send direct message.'))
                result = api_client.send_message(self.author_social_id, message)
            else:
                result = api_client.reply_to_post(self.post_id, message)
            
            if result.get('success'):
                # Create a record of the reply
                reply_vals = {
                    'platform_id': self.platform_id.id,
                    'post_id': result.get('response_id') or result.get('tweet_id') or result.get('message_id', ''),
                    'post_type': 'reply',
                    'content': message,
                    'post_date': fields.Datetime.now(),
                    'parent_post_id': self.id,
                    'state': 'completed',
                }
                self.env['helpdesk.social.media.post'].create(reply_vals)
                
                # Add message to related ticket if exists
                if self.ticket_id:
                    self.ticket_id.message_post(
                        body=_('Replied to %s post: %s') % (self.platform_id.name, message),
                        subject=_('Social Media Reply'),
                    )
                
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Reply Sent'),
                        'message': _('Reply sent successfully to %s.') % self.platform_id.name,
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                raise UserError(_('Failed to send reply: %s') % result.get('error', _('Unknown error')))
                
        except Exception as e:
            raise UserError(_('Error sending reply: %s') % str(e))

    @api.constrains('post_id', 'platform_id')
    def _check_unique_post(self):
        """Ensure post ID is unique per platform"""
        for record in self:
            if record.post_id and record.platform_id:
                duplicate = self.search([
                    ('post_id', '=', record.post_id),
                    ('platform_id', '=', record.platform_id.id),
                    ('id', '!=', record.id)
                ], limit=1)
                if duplicate:
                    raise ValidationError(_('A post with ID %s already exists for platform %s.') %
                                        (record.post_id, record.platform_id.name))

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
            args = [('post_date', '>=', start_of_day), ('post_date', '<=', end_of_day)] + args

        return super(HelpdeskSocialMediaPost, self).search(args, offset=offset, limit=limit, order=order)
