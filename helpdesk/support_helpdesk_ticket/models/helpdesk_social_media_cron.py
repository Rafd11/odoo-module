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
import logging

_logger = logging.getLogger(__name__)


class HelpdeskSocialMediaCron(models.Model):
    """Cron job model for polling social media APIs"""
    _name = 'helpdesk.social.media.cron'
    _description = 'Social Media API Polling'

    @api.model
    def cron_fetch_social_media_posts(self):
        """Cron job to fetch posts from all active social media platforms"""
        platforms = self.env['helpdesk.social.media.platform'].search([
            ('active', '=', True),
            ('access_token', '!=', False)
        ])
        
        for platform in platforms:
            try:
                self._fetch_platform_posts(platform)
            except Exception as e:
                _logger.error(f"Error fetching posts for platform {platform.name}: {e}")

    def _fetch_platform_posts(self, platform):
        """Fetch posts for a specific platform"""
        api_client = platform._get_api_client()
        if not api_client:
            return
        
        # Calculate since date (last 24 hours or last fetch)
        since = (datetime.now() - timedelta(days=1)).isoformat()
        
        # Fetch posts if monitoring enabled
        if platform.monitor_posts:
            posts = api_client.fetch_posts(since=since, limit=50)
            self._create_posts_from_api(platform, posts, 'post')
        
        # Fetch messages if monitoring enabled
        if platform.monitor_messages:
            messages = api_client.fetch_messages(since=since, limit=50)
            self._create_posts_from_api(platform, messages, 'message')
        
        # Fetch mentions if monitoring enabled
        if platform.monitor_mentions:
            mentions = api_client.fetch_mentions(since=since, limit=50)
            self._create_posts_from_api(platform, mentions, 'mention')

    def _create_posts_from_api(self, platform, posts_data, post_type):
        """Create post records from API data"""
        created_count = 0
        
        for post_data in posts_data:
            post_id = post_data.get('post_id')
            if not post_id:
                continue
            
            # Check if post already exists
            existing = self.env['helpdesk.social.media.post'].search([
                ('platform_id', '=', platform.id),
                ('post_id', '=', post_id)
            ], limit=1)
            
            if existing:
                continue
            
            # Parse post date
            post_date = post_data.get('post_date')
            if isinstance(post_date, str):
                try:
                    post_date = fields.Datetime.from_string(post_date)
                except:
                    post_date = fields.Datetime.now()
            elif not post_date:
                post_date = fields.Datetime.now()
            
            # Create post record
            post_vals = {
                'platform_id': platform.id,
                'post_id': post_id,
                'post_type': post_data.get('post_type', post_type),
                'content': post_data.get('content', ''),
                'post_date': post_date,
                'author_name': post_data.get('author_name', ''),
                'author_username': post_data.get('author_username', ''),
                'author_social_id': post_data.get('author_social_id', ''),
                'author_email': post_data.get('author_email', ''),
                'url': post_data.get('url', ''),
                'media_urls': post_data.get('media_urls', ''),
                'state': 'new',
            }
            
            post = self.env['helpdesk.social.media.post'].create(post_vals)
            
            # Auto-create ticket if configured
            if platform.monitor_posts and post_type == 'post':
                post._auto_create_ticket()
            elif platform.monitor_messages and post_type == 'message':
                post._auto_create_ticket()
            elif platform.monitor_mentions and post_type == 'mention':
                post._auto_create_ticket()
            
            created_count += 1
        
        if created_count > 0:
            _logger.info(f"Created {created_count} new posts from {platform.name}")
