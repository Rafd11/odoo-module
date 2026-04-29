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

# -*- coding: utf-8 -*-

from odoo import http, fields
from odoo.http import request
import json
import logging
import hmac
import hashlib

_logger = logging.getLogger(__name__)


class SocialMediaWebhookController(http.Controller):
    """Controller for receiving social media webhooks"""

    @http.route('/helpdesk/social/webhook/<int:platform_id>', type='http', auth='public', methods=['POST'], csrf=False)
    def webhook_receiver(self, platform_id, **kwargs):
        """Receive webhook from social media platform"""
        try:
            platform = request.env['helpdesk.social.media.platform'].sudo().browse(platform_id)
            if not platform.exists() or not platform.active:
                return request.make_response('Platform not found or inactive', 404)
            
            # Get request data
            data = request.httprequest.get_data(as_text=True)
            headers = dict(request.httprequest.headers)
            
            # Verify webhook signature if configured
            if platform.webhook_secret:
                if not self._verify_webhook_signature(platform, data, headers):
                    _logger.warning(f"Invalid webhook signature for platform {platform_id}")
                    return request.make_response('Invalid signature', 403)
            
            # Parse webhook data
            try:
                webhook_data = json.loads(data) if data else {}
            except json.JSONDecodeError:
                webhook_data = {}
            
            # Process webhook based on platform type
            if platform.platform_type == 'facebook':
                self._process_facebook_webhook(platform, webhook_data, headers)
            elif platform.platform_type == 'twitter':
                self._process_twitter_webhook(platform, webhook_data, headers)
            elif platform.platform_type == 'instagram':
                self._process_instagram_webhook(platform, webhook_data, headers)
            
            return request.make_response('OK', 200)
            
        except Exception as e:
            _logger.error(f"Error processing webhook: {e}")
            return request.make_response('Error processing webhook', 500)

    @http.route('/helpdesk/social/webhook/<int:platform_id>', type='http', auth='public', methods=['GET'], csrf=False)
    def webhook_verification(self, platform_id, **kwargs):
        """Handle webhook verification (for Facebook, etc.)"""
        try:
            platform = request.env['helpdesk.social.media.platform'].sudo().browse(platform_id)
            if not platform.exists():
                return request.make_response('Platform not found', 404)
            
            # Facebook webhook verification
            if platform.platform_type == 'facebook':
                verify_token = request.params.get('hub.verify_token')
                challenge = request.params.get('hub.challenge')
                
                if verify_token == platform.webhook_secret:
                    return request.make_response(challenge, 200)
                else:
                    return request.make_response('Invalid verify token', 403)
            
            return request.make_response('OK', 200)
            
        except Exception as e:
            _logger.error(f"Error verifying webhook: {e}")
            return request.make_response('Error', 500)

    def _verify_webhook_signature(self, platform, data, headers):
        """Verify webhook signature"""
        if platform.platform_type == 'facebook':
            signature = headers.get('X-Hub-Signature-256', '').replace('sha256=', '')
            if signature:
                expected = hmac.new(
                    platform.webhook_secret.encode('utf-8'),
                    data.encode('utf-8'),
                    hashlib.sha256
                ).hexdigest()
                return hmac.compare_digest(signature, expected)
        
        return True  # Skip verification if not configured

    def _process_facebook_webhook(self, platform, data, headers):
        """Process Facebook webhook"""
        entry = data.get('entry', [{}])[0]
        changes = entry.get('changes', [])
        
        for change in changes:
            if change.get('field') == 'feed':
                value = change.get('value', {})
                item = value.get('item', '')
                
                if item == 'post' and platform.monitor_posts:
                    post_id = value.get('post_id', '')
                    self._create_post_from_webhook(platform, 'post', post_id)
                elif item == 'comment' and platform.monitor_comments:
                    post_id = value.get('post_id', '')
                    self._create_post_from_webhook(platform, 'comment', post_id)

    def _process_twitter_webhook(self, platform, data, headers):
        """Process Twitter webhook"""
        # Twitter webhook structure
        for tweet_create_event in data.get('tweet_create_events', []):
            if platform.monitor_mentions:
                tweet_id = tweet_create_event.get('id_str', '')
                self._create_post_from_webhook(platform, 'mention', tweet_id)
        
        for direct_message_event in data.get('direct_message_events', []):
            if platform.monitor_messages:
                message_id = direct_message_event.get('id', '')
                self._create_post_from_webhook(platform, 'message', message_id)

    def _process_instagram_webhook(self, platform, data, headers):
        """Process Instagram webhook"""
        # Instagram webhook processing
        for entry in data.get('entry', []):
            for change in entry.get('changes', []):
                if change.get('field') == 'comments' and platform.monitor_comments:
                    comment_id = change.get('value', {}).get('id', '')
                    self._create_post_from_webhook(platform, 'comment', comment_id)

    def _create_post_from_webhook(self, platform, post_type, post_id):
        """Create social media post from webhook data"""
        try:
            # Check if post already exists
            existing = request.env['helpdesk.social.media.post'].sudo().search([
                ('platform_id', '=', platform.id),
                ('post_id', '=', post_id)
            ], limit=1)
            
            if existing:
                return existing
            
            # Fetch full post details using API client
            api_client = platform._get_api_client()
            if not api_client:
                return False
            
            # Fetch post details
            if post_type == 'post':
                posts = api_client.fetch_posts(limit=1)
                post_data = next((p for p in posts if p.get('post_id') == post_id), None)
            elif post_type == 'message':
                messages = api_client.fetch_messages(limit=1)
                post_data = next((m for m in messages if m.get('post_id') == post_id), None)
            else:
                # For comments/mentions, try to fetch from parent
                post_data = {'post_id': post_id, 'post_type': post_type}
            
            if not post_data:
                return False
            
            # Create post record
            post_vals = {
                'platform_id': platform.id,
                'post_id': post_data.get('post_id', post_id),
                'post_type': post_type,
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
            
            post = request.env['helpdesk.social.media.post'].sudo().create(post_vals)
            
            # Auto-create ticket if configured
            if platform.monitor_posts and post_type == 'post':
                post._auto_create_ticket()
            elif platform.monitor_messages and post_type == 'message':
                post._auto_create_ticket()
            elif platform.monitor_mentions and post_type == 'mention':
                post._auto_create_ticket()
            
            return post
            
        except Exception as e:
            _logger.error(f"Error creating post from webhook: {e}")
            return False
