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


class HelpdeskKnowledgeArticle(models.Model):
    _name = 'helpdesk.knowledge.article'
    _description = 'Helpdesk Knowledge Base Article'
    _inherit = ['mail.thread']
    _order = 'create_date desc'

    # ==================== Basic Fields ====================
    name = fields.Char(
        string='Title',
        required=True,
        tracking=True,
        help='Article title'
    )
    content = fields.Html(
        string='Content',
        required=True,
        help='Article content in HTML format'
    )
    category_id = fields.Many2one(
        'helpdesk.category',
        string='Category',
        help='Article category'
    )
    tag_ids = fields.Many2many(
        'helpdesk.tag',
        'helpdesk_knowledge_article_tag_rel',
        'article_id',
        'tag_id',
        string='Tags',
        help='Tags for categorizing articles'
    )
    
    # ==================== Status Field ====================
    state = fields.Selection(
        [
            ('draft', 'Draft'),
            ('published', 'Published'),
            ('archived', 'Archived'),
        ],
        string='Status',
        default='draft',
        required=True,
        tracking=True,
        help='Article publication status'
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Whether the article is active'
    )
    
    # ==================== Author & Version ====================
    author_id = fields.Many2one(
        'res.users',
        string='Author',
        default=lambda self: self.env.user,
        required=True,
        tracking=True,
        help='Article author'
    )
    version = fields.Integer(
        string='Version',
        default=1,
        readonly=True,
        help='Article version number'
    )
    
    # ==================== Analytics Fields ====================
    view_count = fields.Integer(
        string='Views',
        default=0,
        readonly=True,
        help='Number of times this article has been viewed'
    )
    rating = fields.Float(
        string='Rating',
        digits=(2, 1),
        compute='_compute_rating',
        store=True,
        help='Average rating from user feedback (1-5 scale)'
    )
    rating_count = fields.Integer(
        string='Rating Count',
        default=0,
        readonly=True,
        help='Number of ratings received'
    )
    feedback_ids = fields.One2many(
        'helpdesk.knowledge.article.feedback',
        'article_id',
        string='Feedback',
        help='User feedback and ratings'
    )
    
    # ==================== Related Articles ====================
    related_article_ids = fields.Many2many(
        'helpdesk.knowledge.article',
        'helpdesk_knowledge_article_related_rel',
        'article_id',
        'related_article_id',
        string='Related Articles',
        help='Related knowledge base articles'
    )
    
    # ==================== FAQ Flag ====================
    is_faq = fields.Boolean(
        string='Is FAQ',
        default=False,
        help='Mark this article as a Frequently Asked Question'
    )
    
    # ==================== Ticket Linking ====================
    ticket_ids = fields.Many2many(
        'helpdesk.ticket',
        'helpdesk_ticket_knowledge_article_rel',
        'article_id',
        'ticket_id',
        string='Linked Tickets',
        help='Tickets linked to this article'
    )
    ticket_count = fields.Integer(
        string='Ticket Count',
        compute='_compute_ticket_count',
        store=True,
        help='Number of tickets linked to this article'
    )
    effectiveness_count = fields.Integer(
        string='Effectiveness Count',
        compute='_compute_effectiveness',
        store=True,
        help='Number of tickets resolved using this article'
    )
    effectiveness_rate = fields.Float(
        string='Effectiveness Rate (%)',
        compute='_compute_effectiveness',
        store=True,
        digits=(5, 2),
        help='Percentage of linked tickets that were resolved'
    )
    
    # ==================== Computed Methods ====================
    @api.depends('feedback_ids.rating')
    def _compute_rating(self):
        """Compute average rating from feedback"""
        for article in self:
            if article.feedback_ids:
                # Convert Selection values ('1', '2', etc.) to integers
                ratings = [int(f.rating) for f in article.feedback_ids if f.rating]
                article.rating = sum(ratings) / len(ratings) if ratings else 0.0
                article.rating_count = len(ratings)
            else:
                article.rating = 0.0
                article.rating_count = 0
    
    @api.depends('ticket_ids')
    def _compute_ticket_count(self):
        """Compute number of linked tickets"""
        for article in self:
            article.ticket_count = len(article.ticket_ids)
    
    @api.depends('ticket_ids.state')
    def _compute_effectiveness(self):
        """Compute effectiveness based on resolved tickets"""
        for article in self:
            resolved_tickets = article.ticket_ids.filtered(
                lambda t: t.state in ['resolved', 'closed']
            )
            article.effectiveness_count = len(resolved_tickets)
            # Calculate effectiveness rate
            if article.ticket_count > 0:
                article.effectiveness_rate = (article.effectiveness_count / article.ticket_count) * 100
            else:
                article.effectiveness_rate = 0.0
    
    # ==================== Action Methods ====================
    def action_publish(self):
        """Publish the article"""
        self.write({'state': 'published'})
    
    def action_archive(self):
        """Archive the article"""
        self.write({'state': 'archived'})
    
    def action_draft(self):
        """Set article back to draft"""
        self.write({'state': 'draft'})
    
    def action_increment_version(self):
        """Increment article version"""
        self.write({'version': self.version + 1})
    
    def action_track_view(self):
        """Track article view (called from portal)"""
        self.sudo().write({'view_count': self.view_count + 1})
    
    def action_create_from_ticket(self, ticket):
        """Create article from ticket"""
        return {
            'name': _('Create Article from Ticket'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.knowledge.article',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_name': ticket.name,
                'default_content': ticket.description or '',
                'default_category_id': ticket.category_id.id if ticket.category_id else False,
                'default_tag_ids': [(6, 0, ticket.tag_ids.ids)],
                'default_ticket_ids': [(6, 0, [ticket.id])],
            }
        }
    
    def action_view_tickets(self):
        """View linked tickets"""
        self.ensure_one()
        return {
            'name': _('Linked Tickets'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.ticket',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.ticket_ids.ids)],
            'context': {'create': False},
        }
    
    def action_view_feedback(self):
        """View article feedback"""
        self.ensure_one()
        return {
            'name': _('Article Feedback'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.knowledge.article.feedback',
            'view_mode': 'tree,form',
            'domain': [('article_id', '=', self.id)],
            'context': {'default_article_id': self.id},
        }
    
    # ==================== Search Methods ====================
    @api.model
    def _search_suggested_articles(self, keywords, limit=5):
        """Search for articles based on keywords"""
        domain = [
            ('state', '=', 'published'),
            ('active', '=', True),
            '|',
            ('name', 'ilike', keywords),
            ('content', 'ilike', keywords),
        ]
        return self.search(domain, limit=limit)
    
    @api.model
    def get_faq_articles(self, category_id=False, limit=10, search_keywords=None):
        """Get FAQ articles"""
        domain = [
            ('is_faq', '=', True),
            ('state', '=', 'published'),
            ('active', '=', True),
        ]
        if category_id:
            domain.append(('category_id', '=', category_id))
        if search_keywords:
            domain += ['|', ('name', 'ilike', search_keywords), ('content', 'ilike', search_keywords)]
        return self.search(domain, limit=limit, order='view_count desc, rating desc')
    
    @api.model
    def search_faq_by_keywords(self, keywords, category_id=False, limit=5):
        """Search FAQ articles by keywords"""
        if not keywords:
            return self.get_faq_articles(category_id=category_id, limit=limit)
        
        # Extract keywords
        keyword_list = keywords.lower().split()
        # Remove common words
        common_words = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        keyword_list = [k for k in keyword_list if len(k) > 2 and k not in common_words]
        
        if not keyword_list:
            return self.get_faq_articles(category_id=category_id, limit=limit)
        
        # Build search domain
        domain = [
            ('is_faq', '=', True),
            ('state', '=', 'published'),
            ('active', '=', True),
        ]
        
        if category_id:
            domain.append(('category_id', '=', category_id))
        
        # Search in name and content
        search_terms = ' '.join(keyword_list[:3])  # Use first 3 keywords
        domain += ['|', ('name', 'ilike', search_terms), ('content', 'ilike', search_terms)]
        
        return self.search(domain, limit=limit, order='view_count desc, rating desc')


class HelpdeskKnowledgeArticleFeedback(models.Model):
    _name = 'helpdesk.knowledge.article.feedback'
    _description = 'Knowledge Base Article Feedback'
    _order = 'create_date desc'

    article_id = fields.Many2one(
        'helpdesk.knowledge.article',
        string='Article',
        required=True,
        ondelete='cascade'
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Customer',
        help='Customer who provided feedback'
    )
    rating = fields.Selection(
        [
            ('1', '1 - Poor'),
            ('2', '2 - Fair'),
            ('3', '3 - Good'),
            ('4', '4 - Very Good'),
            ('5', '5 - Excellent'),
        ],
        string='Rating',
        required=True,
        help='Article rating'
    )
    feedback = fields.Text(
        string='Feedback',
        help='Additional feedback comments'
    )
    helpful = fields.Boolean(
        string='Helpful',
        help='Was this article helpful?'
    )
