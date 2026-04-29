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


class HelpdeskSocialMediaPostReplyWizard(models.TransientModel):
    _name = 'helpdesk.social.media.post.reply.wizard'
    _description = 'Reply to Social Media Post Wizard'

    post_id = fields.Many2one(
        'helpdesk.social.media.post',
        string='Post',
        required=True,
        readonly=True,
        help='Post to reply to'
    )
    platform_id = fields.Many2one(
        'helpdesk.social.media.platform',
        string='Platform',
        related='post_id.platform_id',
        readonly=True,
        help='Social media platform'
    )
    reply_type = fields.Selection(
        [
            ('comment', 'Comment/Reply'),
            ('message', 'Direct Message'),
        ],
        string='Reply Type',
        default='comment',
        required=True,
        help='Type of reply to send'
    )
    message = fields.Html(
        string='Message',
        required=True,
        help='Message to send as reply'
    )
    ticket_id = fields.Many2one(
        'helpdesk.ticket',
        string='Related Ticket',
        related='post_id.ticket_id',
        readonly=True,
        help='Related ticket'
    )

    @api.model
    def default_get(self, fields_list):
        """Set default values"""
        res = super(HelpdeskSocialMediaPostReplyWizard, self).default_get(fields_list)
        
        post_id = self.env.context.get('default_post_id') or self.env.context.get('active_id')
        if post_id:
            post = self.env['helpdesk.social.media.post'].browse(post_id)
            if 'post_id' in fields_list:
                res['post_id'] = post.id
            if 'platform_id' in fields_list:
                res['platform_id'] = post.platform_id.id
            if 'reply_type' in fields_list and not res.get('reply_type'):
                # Default to message for DMs, comment for posts
                res['reply_type'] = 'message' if post.post_type == 'message' else 'comment'
        
        return res

    def action_send_reply(self):
        """Send reply to social media post"""
        self.ensure_one()
        
        # Convert HTML to plain text for social media (most platforms don't support HTML)
        import re
        message_text = re.sub('<[^<]+?>', '', self.message)  # Strip HTML tags
        message_text = message_text.strip()
        
        if not message_text:
            raise UserError(_('Message cannot be empty.'))
        
        # Send reply via API
        result = self.post_id.send_reply(message_text, self.reply_type)
        
        return result
