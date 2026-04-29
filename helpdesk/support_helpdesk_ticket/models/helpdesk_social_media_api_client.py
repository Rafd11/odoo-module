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
import requests
import json
import logging
from datetime import datetime, timedelta

_logger = logging.getLogger(__name__)


class HelpdeskSocialMediaAPIClient:
    """Base class for social media API clients (regular Python class)"""
    
    def __init__(self, platform):
        """Initialize API client with platform configuration"""
        self.platform = platform
        self.api_key = platform.api_key
        self.api_secret = platform.api_secret
        self.access_token = platform.access_token
        self.refresh_token = platform.refresh_token
        self.base_url = self._get_base_url()

    def _get_base_url(self):
        """Get base API URL for the platform - to be overridden"""
        raise NotImplementedError("Subclass must implement _get_base_url")

    def _get_headers(self):
        """Get HTTP headers for API requests"""
        return {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json',
        }

    def _make_request(self, method, endpoint, params=None, data=None):
        """Make HTTP request to API"""
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        headers = self._get_headers()
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data, params=params, timeout=30)
            elif method.upper() == 'PUT':
                response = requests.put(url, headers=headers, json=data, params=params, timeout=30)
            elif method.upper() == 'DELETE':
                response = requests.delete(url, headers=headers, params=params, timeout=30)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            response.raise_for_status()
            return response.json() if response.content else {}
            
        except requests.exceptions.RequestException as e:
            _logger.error(f"API request failed: {e}")
            raise UserError(_('API request failed: %s') % str(e))

    def test_connection(self):
        """Test API connection - to be overridden"""
        raise NotImplementedError("Subclass must implement test_connection")

    def fetch_posts(self, since=None, limit=50):
        """Fetch posts from platform - to be overridden"""
        raise NotImplementedError("Subclass must implement fetch_posts")

    def fetch_messages(self, since=None, limit=50):
        """Fetch direct messages - to be overridden"""
        raise NotImplementedError("Subclass must implement fetch_messages")

    def fetch_mentions(self, since=None, limit=50):
        """Fetch mentions - to be overridden"""
        raise NotImplementedError("Subclass must implement fetch_mentions")

    def reply_to_post(self, post_id, message):
        """Reply to a post - to be overridden"""
        raise NotImplementedError("Subclass must implement reply_to_post")

    def send_message(self, recipient_id, message):
        """Send direct message - to be overridden"""
        raise NotImplementedError("Subclass must implement send_message")

    def refresh_access_token(self):
        """Refresh OAuth access token - to be overridden"""
        raise NotImplementedError("Subclass must implement refresh_access_token")


class FacebookAPIClient(HelpdeskSocialMediaAPIClient):
    """Facebook Graph API Client"""
    
    def __init__(self, platform):
        """Initialize Facebook API client"""
        super().__init__(platform)

    def _get_base_url(self):
        return 'https://graph.facebook.com/v18.0'

    def test_connection(self):
        """Test Facebook API connection"""
        try:
            response = self._make_request('GET', '/me', params={'access_token': self.access_token})
            return {'success': True, 'message': _('Connection successful'), 'data': response}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def fetch_posts(self, since=None, limit=50):
        """Fetch Facebook page posts"""
        if not self.platform.page_id:
            return []
        
        params = {
            'access_token': self.access_token,
            'limit': limit,
            'fields': 'id,message,created_time,from,permalink_url,attachments'
        }
        
        if since:
            params['since'] = since
        
        try:
            response = self._make_request('GET', f'/{self.platform.page_id}/posts', params=params)
            posts = response.get('data', [])
            return self._parse_facebook_posts(posts)
        except Exception as e:
            _logger.error(f"Error fetching Facebook posts: {e}")
            return []

    def fetch_messages(self, since=None, limit=50):
        """Fetch Facebook Messenger messages"""
        if not self.platform.page_id:
            return []
        
        params = {
            'access_token': self.access_token,
            'limit': limit,
            'fields': 'id,message,created_time,from,to'
        }
        
        if since:
            params['since'] = since
        
        try:
            response = self._make_request('GET', f'/{self.platform.page_id}/conversations', params=params)
            conversations = response.get('data', [])
            messages = []
            for conv in conversations:
                msg_response = self._make_request('GET', f'/{conv["id"]}/messages', params=params)
                messages.extend(msg_response.get('data', []))
            return self._parse_facebook_messages(messages)
        except Exception as e:
            _logger.error(f"Error fetching Facebook messages: {e}")
            return []

    def reply_to_post(self, post_id, message):
        """Reply to a Facebook post (comment)"""
        try:
            data = {
                'message': message,
                'access_token': self.access_token
            }
            response = self._make_request('POST', f'/{post_id}/comments', data=data)
            return {'success': True, 'response_id': response.get('id')}
        except Exception as e:
            _logger.error(f"Error replying to Facebook post: {e}")
            return {'success': False, 'error': str(e)}

    def send_message(self, recipient_id, message):
        """Send Facebook Messenger message"""
        try:
            data = {
                'recipient': {'id': recipient_id},
                'message': {'text': message},
                'access_token': self.access_token
            }
            response = self._make_request('POST', '/me/messages', data=data)
            return {'success': True, 'message_id': response.get('message_id')}
        except Exception as e:
            _logger.error(f"Error sending Facebook message: {e}")
            return {'success': False, 'error': str(e)}

    def refresh_access_token(self):
        """Refresh Facebook access token"""
        # Facebook tokens are long-lived, but this can be extended
        return {'success': True, 'message': _('Token refresh not required for long-lived tokens')}

    def _parse_facebook_posts(self, posts):
        """Parse Facebook posts into standard format"""
        parsed = []
        for post in posts:
            parsed.append({
                'post_id': post.get('id'),
                'content': post.get('message', ''),
                'post_date': post.get('created_time'),
                'author_name': post.get('from', {}).get('name', ''),
                'author_social_id': post.get('from', {}).get('id', ''),
                'url': post.get('permalink_url', ''),
                'media_urls': self._extract_media_urls(post.get('attachments', {}).get('data', [])),
            })
        return parsed

    def _parse_facebook_messages(self, messages):
        """Parse Facebook messages into standard format"""
        parsed = []
        for msg in messages:
            parsed.append({
                'post_id': msg.get('id'),
                'content': msg.get('message', ''),
                'post_date': msg.get('created_time'),
                'author_name': msg.get('from', {}).get('name', ''),
                'author_social_id': msg.get('from', {}).get('id', ''),
                'post_type': 'message',
            })
        return parsed

    def _extract_media_urls(self, attachments):
        """Extract media URLs from attachments"""
        urls = []
        for att in attachments:
            if att.get('type') in ['photo', 'video']:
                media = att.get('media', {})
                if media.get('image') or media.get('source'):
                    urls.append(media.get('image', {}).get('src') or media.get('source', ''))
        return '\n'.join(urls)


class TwitterAPIClient(HelpdeskSocialMediaAPIClient):
    """Twitter API v2 Client"""
    
    def __init__(self, platform):
        """Initialize Twitter API client"""
        super().__init__(platform)

    def _get_base_url(self):
        return 'https://api.twitter.com/2'

    def test_connection(self):
        """Test Twitter API connection"""
        try:
            response = self._make_request('GET', '/users/me')
            return {'success': True, 'message': _('Connection successful'), 'data': response}
        except Exception as e:
            return {'success': False, 'message': str(e)}

    def fetch_posts(self, since=None, limit=50):
        """Fetch tweets mentioning the account"""
        if not self.platform.page_id:  # page_id stores username
            return []
        
        params = {
            'query': f'@{self.platform.page_id}',
            'max_results': min(limit, 100),
            'tweet.fields': 'created_at,author_id,text,public_metrics',
            'expansions': 'author_id',
            'user.fields': 'name,username'
        }
        
        if since:
            params['start_time'] = since
        
        try:
            response = self._make_request('GET', '/tweets/search/recent', params=params)
            tweets = response.get('data', [])
            users = {u['id']: u for u in response.get('includes', {}).get('users', [])}
            return self._parse_twitter_tweets(tweets, users)
        except Exception as e:
            _logger.error(f"Error fetching Twitter mentions: {e}")
            return []

    def fetch_messages(self, since=None, limit=50):
        """Fetch Twitter direct messages"""
        params = {
            'max_results': min(limit, 50),
        }
        
        if since:
            params['start_time'] = since
        
        try:
            response = self._make_request('GET', '/dm_events', params=params)
            events = response.get('data', [])
            return self._parse_twitter_messages(events)
        except Exception as e:
            _logger.error(f"Error fetching Twitter messages: {e}")
            return []

    def reply_to_post(self, post_id, message):
        """Reply to a Twitter tweet"""
        try:
            data = {
                'text': message,
                'reply': {'in_reply_to_tweet_id': post_id}
            }
            response = self._make_request('POST', '/tweets', data=data)
            return {'success': True, 'tweet_id': response.get('data', {}).get('id')}
        except Exception as e:
            _logger.error(f"Error replying to Twitter tweet: {e}")
            return {'success': False, 'error': str(e)}

    def send_message(self, recipient_id, message):
        """Send Twitter direct message"""
        try:
            data = {
                'event': {
                    'type': 'MessageCreate',
                    'message_create': {
                        'target': {'recipient_id': recipient_id},
                        'message_data': {'text': message}
                    }
                }
            }
            response = self._make_request('POST', '/dm_events/new', data=data)
            return {'success': True, 'event_id': response.get('event', {}).get('id')}
        except Exception as e:
            _logger.error(f"Error sending Twitter message: {e}")
            return {'success': False, 'error': str(e)}

    def refresh_access_token(self):
        """Refresh Twitter OAuth token"""
        # Twitter uses OAuth 1.0a or 2.0 - implementation depends on auth method
        return {'success': True, 'message': _('Token refresh implementation depends on OAuth method')}

    def _parse_twitter_tweets(self, tweets, users):
        """Parse Twitter tweets into standard format"""
        parsed = []
        for tweet in tweets:
            author = users.get(tweet.get('author_id', ''), {})
            parsed.append({
                'post_id': tweet.get('id'),
                'content': tweet.get('text', ''),
                'post_date': tweet.get('created_at'),
                'author_name': author.get('name', ''),
                'author_username': author.get('username', ''),
                'author_social_id': tweet.get('author_id', ''),
                'url': f"https://twitter.com/{author.get('username', '')}/status/{tweet.get('id', '')}",
                'post_type': 'mention',
            })
        return parsed

    def _parse_twitter_messages(self, events):
        """Parse Twitter messages into standard format"""
        parsed = []
        for event in events:
            if event.get('type') == 'MessageCreate':
                msg = event.get('message_create', {})
                parsed.append({
                    'post_id': event.get('id'),
                    'content': msg.get('message_data', {}).get('text', ''),
                    'post_date': event.get('created_timestamp'),
                    'author_social_id': msg.get('sender_id', ''),
                    'post_type': 'message',
                })
        return parsed
