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
from odoo.exceptions import ValidationError, UserError


class HelpdeskSocialMediaPlatform(models.Model):
    _name = 'helpdesk.social.media.platform'
    _description = 'Social Media Platform Configuration'
    _order = 'name'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    # ==================== Basic Fields ====================
    name = fields.Char(
        string='Platform Name',
        required=True,
        tracking=True,
        help='Name of the social media platform (e.g., Facebook, Twitter)'
    )
    platform_type = fields.Selection(
        [
            ('facebook', 'Facebook'),
            ('twitter', 'Twitter'),
            ('instagram', 'Instagram'),
            ('linkedin', 'LinkedIn'),
            ('other', 'Other'),
        ],
        string='Platform Type',
        required=True,
        default='facebook',
        tracking=True,
        help='Type of social media platform'
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        tracking=True,
        help='If unchecked, this platform integration will be disabled'
    )

    # ==================== API Configuration ====================
    api_key = fields.Char(
        string='API Key / App ID',
        tracking=True,
        help='API Key or Application ID for the platform'
    )
    api_secret = fields.Char(
        string='API Secret / App Secret',
        tracking=True,
        help='API Secret or Application Secret (stored encrypted)'
    )
    access_token = fields.Char(
        string='Access Token',
        tracking=True,
        help='OAuth Access Token for API authentication'
    )
    refresh_token = fields.Char(
        string='Refresh Token',
        tracking=True,
        help='OAuth Refresh Token for token renewal'
    )
    token_expiry = fields.Datetime(
        string='Token Expiry',
        help='Date and time when the access token expires'
    )

    # ==================== Configuration Fields ====================
    page_id = fields.Char(
        string='Page ID / Username',
        help='Facebook Page ID, Twitter Username, or Instagram Username'
    )
    webhook_url = fields.Char(
        string='Webhook URL',
        readonly=True,
        compute='_compute_webhook_url',
        store=False,
        help='Webhook URL for real-time updates (auto-generated)'
    )
    webhook_secret = fields.Char(
        string='Webhook Secret',
        help='Secret key for webhook verification'
    )

    # ==================== Monitoring Settings ====================
    monitor_posts = fields.Boolean(
        string='Monitor Posts',
        default=True,
        help='Automatically create tickets from new posts'
    )
    monitor_messages = fields.Boolean(
        string='Monitor Messages',
        default=True,
        help='Automatically create tickets from direct messages'
    )
    monitor_comments = fields.Boolean(
        string='Monitor Comments',
        default=False,
        help='Automatically create tickets from comments'
    )
    monitor_mentions = fields.Boolean(
        string='Monitor Mentions',
        default=True,
        help='Automatically create tickets from mentions'
    )

    # ==================== Auto-Assignment Settings ====================
    default_team_id = fields.Many2one(
        'helpdesk.team',
        string='Default Team',
        help='Default team to assign tickets from this platform'
    )
    default_user_id = fields.Many2one(
        'res.users',
        string='Default Agent',
        help='Default agent to assign tickets from this platform'
    )
    default_category_id = fields.Many2one(
        'helpdesk.category',
        string='Default Category',
        help='Default category for tickets from this platform'
    )
    default_priority = fields.Selection(
        [
            ('0', 'Low'),
            ('1', 'Medium'),
            ('2', 'High'),
            ('3', 'Urgent'),
        ],
        string='Default Priority',
        default='1',
        help='Default priority for tickets from this platform'
    )

    # ==================== Statistics ====================
    post_count = fields.Integer(
        string='Posts Count',
        compute='_compute_post_count',
        help='Number of posts from this platform'
    )
    ticket_count = fields.Integer(
        string='Tickets Count',
        compute='_compute_ticket_count',
        help='Number of tickets created from this platform'
    )

    # ==================== Relationships ====================
    post_ids = fields.One2many(
        'helpdesk.social.media.post',
        'platform_id',
        string='Posts',
        help='Social media posts from this platform'
    )

    def _compute_webhook_url(self):
        """Compute webhook URL for the platform"""
        base_url = self.env['ir.config_parameter'].sudo().get_param('web.base.url')
        for record in self:
            if record.id:
                record.webhook_url = f"{base_url}/helpdesk/social/webhook/{record.id}"
            else:
                record.webhook_url = False

    @api.depends('post_ids')
    def _compute_post_count(self):
        """Compute post count"""
        for record in self:
            record.post_count = len(record.post_ids)

    @api.depends('post_ids', 'post_ids.ticket_id')
    def _compute_ticket_count(self):
        """Compute ticket count"""
        for record in self:
            record.ticket_count = len(record.post_ids.filtered('ticket_id'))

    def action_view_posts(self):
        """Open posts from this platform"""
        self.ensure_one()
        action = {
            'name': _('Posts from %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.social.media.post',
            'view_mode': 'tree,form',
            'domain': [('platform_id', '=', self.id)],
            'context': {'default_platform_id': self.id},
        }
        return action

    def action_view_tickets(self):
        """Open tickets created from this platform"""
        self.ensure_one()
        tickets = self.post_ids.mapped('ticket_id').filtered(lambda t: t)
        action = {
            'name': _('Tickets from %s') % self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket',
            'view_mode': 'tree,form,kanban',
            'domain': [('id', 'in', tickets.ids)],
            'context': {'default_channel_id': self.env['helpdesk.channel'].search([('code', '=', 'social_media')], limit=1).id or False},
        }
        return action

    def _get_api_client(self):
        """Get API client instance for this platform"""
        self.ensure_one()
        if not self.active or not self.access_token:
            return False
        
        if self.platform_type == 'facebook':
            from .helpdesk_social_media_api_client import FacebookAPIClient
            return FacebookAPIClient(self)
        elif self.platform_type == 'twitter':
            from .helpdesk_social_media_api_client import TwitterAPIClient
            return TwitterAPIClient(self)
        else:
            return False

    def action_test_connection(self):
        """Test API connection"""
        self.ensure_one()
        api_client = self._get_api_client()
        if not api_client:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Connection Test Failed'),
                    'message': _('API client not available. Please check platform configuration and access token.'),
                    'type': 'danger',
                    'sticky': True,
                }
            }
        
        result = api_client.test_connection()
        if result.get('success'):
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Connection Successful'),
                    'message': result.get('message', _('Connection test passed.')),
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Connection Test Failed'),
                    'message': result.get('message', _('Connection test failed.')),
                    'type': 'danger',
                    'sticky': True,
                }
            }

    def action_refresh_token(self):
        """Refresh OAuth access token"""
        self.ensure_one()
        api_client = self._get_api_client()
        if not api_client:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Token Refresh Failed'),
                    'message': _('API client not available.'),
                    'type': 'danger',
                    'sticky': True,
                }
            }
        
        result = api_client.refresh_access_token()
        if result.get('success'):
            # Update token if returned
            if result.get('access_token'):
                self.write({'access_token': result['access_token']})
            if result.get('token_expiry'):
                self.write({'token_expiry': result['token_expiry']})
            
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Token Refreshed'),
                    'message': result.get('message', _('Access token refreshed successfully.')),
                    'type': 'success',
                    'sticky': False,
                }
            }
        else:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Token Refresh Failed'),
                    'message': result.get('message', _('Failed to refresh access token.')),
                    'type': 'danger',
                    'sticky': True,
                }
            }

    def action_fetch_posts(self):
        """Manually fetch posts from API"""
        self.ensure_one()
        api_client = self._get_api_client()
        if not api_client:
            raise UserError(_('API client not available. Please check platform configuration.'))
        
        # Fetch posts
        posts = api_client.fetch_posts(limit=50)
        
        # Create post records
        created_count = 0
        for post_data in posts:
            existing = self.env['helpdesk.social.media.post'].search([
                ('platform_id', '=', self.id),
                ('post_id', '=', post_data.get('post_id'))
            ], limit=1)
            
            if not existing:
                post_vals = {
                    'platform_id': self.id,
                    'post_id': post_data.get('post_id'),
                    'post_type': post_data.get('post_type', 'post'),
                    'content': post_data.get('content', ''),
                    'post_date': post_data.get('post_date') or fields.Datetime.now(),
                    'author_name': post_data.get('author_name', ''),
                    'author_username': post_data.get('author_username', ''),
                    'author_social_id': post_data.get('author_social_id', ''),
                    'author_email': post_data.get('author_email', ''),
                    'url': post_data.get('url', ''),
                    'media_urls': post_data.get('media_urls', ''),
                    'state': 'new',
                }
                self.env['helpdesk.social.media.post'].create(post_vals)
                created_count += 1
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Posts Fetched'),
                'message': _('Fetched %d new posts from %s.') % (created_count, self.name),
                'type': 'success',
                'sticky': False,
            }
        }

    @api.constrains('api_key', 'api_secret')
    def _check_api_credentials(self):
        """Validate API credentials format"""
        for record in self:
            if record.active and record.platform_type != 'other':
                if not record.api_key:
                    raise ValidationError(_('API Key is required for active platform integrations.'))
