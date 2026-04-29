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


class HelpdeskSocialMediaPostCreateTicketWizard(models.TransientModel):
    _name = 'helpdesk.social.media.post.create.ticket.wizard'
    _description = 'Create Ticket from Social Media Post Wizard'

    post_id = fields.Many2one(
        'helpdesk.social.media.post',
        string='Social Media Post',
        required=True,
        readonly=True,
        help='Post to create ticket from'
    )
    platform_id = fields.Many2one(
        'helpdesk.social.media.platform',
        string='Platform',
        related='post_id.platform_id',
        readonly=True,
        help='Social media platform'
    )
    author_id = fields.Many2one(
        'res.partner',
        string='Contact',
        help='Contact associated with this post'
    )
    name = fields.Char(
        string='Subject',
        required=True,
        help='Ticket subject'
    )
    description = fields.Html(
        string='Description',
        required=True,
        help='Ticket description'
    )
    category_id = fields.Many2one(
        'helpdesk.category',
        string='Category',
        help='Ticket category'
    )
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
        help='Ticket priority'
    )
    ticket_type_id = fields.Many2one(
        'helpdesk.ticket.type',
        string='Ticket Type',
        help='Type of ticket'
    )
    team_id = fields.Many2one(
        'helpdesk.team',
        string='Team',
        help='Team to assign the ticket to'
    )
    user_id = fields.Many2one(
        'res.users',
        string='Agent',
        help='Agent to assign the ticket to'
    )

    @api.model
    def default_get(self, fields_list):
        """Set default values from social media post"""
        res = super(HelpdeskSocialMediaPostCreateTicketWizard, self).default_get(fields_list)
        
        post_id = self.env.context.get('default_post_id') or self.env.context.get('active_id')
        if post_id:
            post = self.env['helpdesk.social.media.post'].browse(post_id)
            if 'post_id' in fields_list:
                res['post_id'] = post.id
            if 'platform_id' in fields_list:
                res['platform_id'] = post.platform_id.id
            if 'author_id' in fields_list and not res.get('author_id'):
                res['author_id'] = post.author_id.id if post.author_id else False
            if 'name' in fields_list and not res.get('name'):
                # Use first part of content as subject
                content_text = post.content.replace('<p>', '').replace('</p>', '').strip() if post.content else ''
                res['name'] = content_text[:100] if content_text else _('Support Request from %s') % post.platform_id.name
            if 'description' in fields_list and not res.get('description'):
                res['description'] = post.content or ''
            if 'category_id' in fields_list and not res.get('category_id'):
                res['category_id'] = post.platform_id.default_category_id.id if post.platform_id.default_category_id else False
            if 'priority' in fields_list and not res.get('priority'):
                res['priority'] = post.platform_id.default_priority or '1'
            if 'team_id' in fields_list and not res.get('team_id'):
                res['team_id'] = post.platform_id.default_team_id.id if post.platform_id.default_team_id else False
            if 'user_id' in fields_list and not res.get('user_id'):
                res['user_id'] = post.platform_id.default_user_id.id if post.platform_id.default_user_id else False
        
        return res

    @api.onchange('author_id')
    def _onchange_author_id(self):
        """Update description if author changes"""
        if self.author_id and self.post_id:
            # Could add author info to description
            pass

    def action_create_ticket(self):
        """Create ticket from social media post"""
        self.ensure_one()
        
        # Ensure partner exists
        partner = self.author_id
        if not partner and self.post_id.author_id:
            partner = self.post_id.author_id
        if not partner and self.post_id:
            partner = self.post_id.action_find_or_create_partner()
        
        # Prepare ticket values
        ticket_vals = {
            'name': self.name,
            'description': self.description,
            'partner_id': partner.id if partner else False,
            'channel': 'social_media',
            'state': 'new',
            'priority': self.priority,
            'category_id': self.category_id.id if self.category_id else False,
            'ticket_type_id': self.ticket_type_id.id if self.ticket_type_id else False,
            'team_id': self.team_id.id if self.team_id else False,
            'user_id': self.user_id.id if self.user_id else False,
        }
        
        # Create ticket
        ticket = self.env['helpdesk.ticket'].create(ticket_vals)
        
        # Link post to ticket
        if self.post_id:
            self.post_id.write({
                'ticket_id': ticket.id,
                'state': 'ticket_created',
                'processed_date': fields.Datetime.now(),
            })
            
            # Add message to ticket with post details
            ticket.message_post(
                body=_('Ticket created from %s post: <a href="%s" target="_blank">View Post</a>') % 
                     (self.post_id.platform_id.name, self.post_id.url or '#'),
                subject=_('Social Media Post'),
            )
        
        # Return action to view the created ticket
        action = {
            'name': _('Ticket Created'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket',
            'view_mode': 'form',
            'res_id': ticket.id,
            'target': 'current',
        }
        return action
