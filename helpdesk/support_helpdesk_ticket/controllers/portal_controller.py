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

import json

from odoo import http
from odoo.http import request, content_disposition
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager
from odoo.exceptions import AccessError, MissingError


class HelpdeskPortalController(CustomerPortal):
    """Portal controller for customer ticket management"""

    def _prepare_portal_layout_values(self):
        """Prepare values for portal layout"""
        values = super(HelpdeskPortalController, self)._prepare_portal_layout_values()
        ticket_count = request.env['helpdesk.ticket'].search_count([
            ('partner_id', '=', request.env.user.partner_id.id)
        ])
        values.update({
            'ticket_count': ticket_count,
        })
        return values

    def _ticket_get_page_view_values(self, ticket, access_token, **kwargs):
        """Get values for ticket detail page"""
        # State, Priority, and Channel labels mapping
        state_labels = {
            'draft': 'Draft',
            'new': 'New',
            'assigned': 'Assigned',
            'in_progress': 'In Progress',
            'resolved': 'Resolved',
            'closed': 'Closed',
            'cancelled': 'Cancelled',
        }
        priority_labels = {
            '0': 'Low',
            '1': 'Medium',
            '2': 'High',
            '3': 'Urgent',
        }
        channel_labels = {
            'email': 'Email',
            'web': 'Web Portal',
            'phone': 'Phone',
            'social_media': 'Social Media',
        }
        
        values = {
            'page_name': 'ticket',
            'ticket': ticket,
            'state_labels': state_labels,
            'priority_labels': priority_labels,
            'channel_labels': channel_labels,
        }
        return self._get_page_view_values(ticket, access_token, values, 'my_tickets_history', False, **kwargs)

    def _prepare_home_portal_values(self, counters):
        """Prepare home portal values"""
        values = super(HelpdeskPortalController, self)._prepare_home_portal_values(counters)
        if 'ticket_count' in counters:
            ticket_count = request.env['helpdesk.ticket'].search_count([
                ('partner_id', '=', request.env.user.partner_id.id)
            ])
            values['ticket_count'] = ticket_count
        return values

    @http.route(['/my/tickets', '/my/tickets/page/<int:page>'], type='http', auth="user", website=False)
    def portal_my_tickets(self, page=1, sortby=None, filterby=None, search=None, search_in='all', **kw):
        """Display customer's tickets"""
        values = self._prepare_portal_layout_values()
        HelpdeskTicket = request.env['helpdesk.ticket']
        
        # Domain: only tickets for current user's partner
        domain = [('partner_id', '=', request.env.user.partner_id.id)]
        
        # Search
        searchbar_sortings = {
            'date': {'label': 'Newest', 'order': 'create_date desc'},
            'name': {'label': 'Subject', 'order': 'name'},
            'state': {'label': 'Status', 'order': 'state'},
            'priority': {'label': 'Priority', 'order': 'priority desc'},
        }
        searchbar_filters = {
            'all': {'label': 'All', 'domain': []},
            'new': {'label': 'New', 'domain': [('state', '=', 'new')]},
            'assigned': {'label': 'Assigned', 'domain': [('state', '=', 'assigned')]},
            'in_progress': {'label': 'In Progress', 'domain': [('state', '=', 'in_progress')]},
            'resolved': {'label': 'Resolved', 'domain': [('state', '=', 'resolved')]},
            'closed': {'label': 'Closed', 'domain': [('state', '=', 'closed')]},
        }
        searchbar_inputs = {
            'all': {'input': 'all', 'label': 'Search in All'},
            'ticket': {'input': 'ticket', 'label': 'Search in Ticket Number'},
            'subject': {'input': 'subject', 'label': 'Search in Subject'},
            'content': {'input': 'content', 'label': 'Search in Description'},
        }
        
        # Defaults
        if not sortby:
            sortby = 'date'
        if not filterby:
            filterby = 'all'
        if not search_in:
            search_in = 'all'
        
        # Apply search
        if search and search_in:
            search_domain = []
            if search_in in ('ticket', 'all'):
                search_domain.append(('ticket_number', 'ilike', search))
            if search_in in ('subject', 'all'):
                search_domain.append(('name', 'ilike', search))
            if search_in in ('content', 'all'):
                search_domain.append(('description', 'ilike', search))
            if search_domain:
                domain += ['|'] * (len(search_domain) - 1) + search_domain
        
        # Apply filter
        if filterby != 'all':
            domain += searchbar_filters[filterby]['domain']
        
        # Count
        ticket_count = HelpdeskTicket.search_count(domain)
        
        # Pager
        pager = portal_pager(
            url="/my/tickets",
            url_args={'sortby': sortby, 'filterby': filterby, 'search_in': search_in, 'search': search},
            total=ticket_count,
            page=page,
            step=self._items_per_page
        )
        
        # Search tickets
        tickets = HelpdeskTicket.search(domain, order=searchbar_sortings[sortby]['order'], limit=self._items_per_page, offset=pager['offset'])
        
        # State, Priority, and Channel labels mapping
        state_labels = {
            'draft': 'Draft',
            'new': 'New',
            'assigned': 'Assigned',
            'in_progress': 'In Progress',
            'resolved': 'Resolved',
            'closed': 'Closed',
            'cancelled': 'Cancelled',
        }
        priority_labels = {
            '0': 'Low',
            '1': 'Medium',
            '2': 'High',
            '3': 'Urgent',
        }
        channel_labels = {
            'email': 'Email',
            'web': 'Web Portal',
            'phone': 'Phone',
            'social_media': 'Social Media',
        }
        
        values.update({
            'tickets': tickets,
            'page_name': 'tickets',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'searchbar_filters': searchbar_filters,
            'searchbar_inputs': searchbar_inputs,
            'sortby': sortby,
            'filterby': filterby,
            'search_in': search_in,
            'search': search,
            'default_url': '/my/tickets',
            'state_labels': state_labels,
            'priority_labels': priority_labels,
            'channel_labels': channel_labels,
        })
        
        return request.render("support_helpdesk_ticket.portal_my_tickets", values)

    @http.route(['/my/tickets/<int:ticket_id>'], type='http', auth="user", website=False)
    def portal_ticket_page(self, ticket_id=None, access_token=None, **kw):
        """Display ticket detail page"""
        try:
            ticket_sudo = self._document_check_access('helpdesk.ticket', ticket_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        
        # Ensure ticket belongs to current user's partner
        if ticket_sudo.partner_id != request.env.user.partner_id:
            return request.redirect('/my')
        
        values = self._ticket_get_page_view_values(ticket_sudo, access_token, **kw)
        return request.render("support_helpdesk_ticket.portal_ticket_page", values)

    @http.route(['/my/tickets/new'], type='http', auth="user", website=False)
    def portal_create_ticket(self, **kw):
        """Display ticket creation form"""
        # Get FAQ articles for the widget (most viewed FAQs)
        faq_articles = request.env['helpdesk.knowledge.article'].get_faq_articles(limit=10)
        partner = request.env.user.partner_id
        icp = request.env['ir.config_parameter'].sudo()
        privacy_policy_url = icp.get_param('support_helpdesk_ticket.privacy_policy_url', default='')
        
        values = {
            'page_name': 'create_ticket',
            'categories': request.env['helpdesk.category'].search([('active', '=', True)]),
            'ticket_types': request.env['helpdesk.ticket.type'].search([('active', '=', True)]),
            'faq_articles': faq_articles,
            'helpdesk_requires_consent': not bool(getattr(partner, 'helpdesk_consent', False)),
            'helpdesk_privacy_policy_url': privacy_policy_url,
        }
        return request.render("support_helpdesk_ticket.portal_create_ticket", values)
    
    @http.route(['/faq/search'], type='jsonrpc', auth="public", website=True, methods=['POST'])
    def portal_faq_search(self, keywords=None, category_id=None, **kw):
        """Search FAQs via AJAX"""
        if not keywords:
            return {'faqs': []}
        
        faq_articles = request.env['helpdesk.knowledge.article'].search_faq_by_keywords(
            keywords=keywords,
            category_id=category_id,
            limit=5
        )
        
        return {
            'faqs': [{
                'id': faq.id,
                'name': faq.name,
                'content': faq.content[:200] + '...' if len(faq.content) > 200 else faq.content,
                'url': '/knowledge/%s' % faq.id,
                'category': faq.category_id.name if faq.category_id else '',
                'views': faq.view_count,
                'rating': faq.rating,
            } for faq in faq_articles]
        }

    @http.route(['/my/tickets/create'], type='http', auth="user", website=False, methods=['POST'], csrf=True)
    def portal_create_ticket_submit(self, **kw):
        """Handle ticket creation form submission"""
        partner = request.env.user.partner_id.sudo()

        # Enforce consent: if the partner has not previously consented,
        # require an explicit consent flag from the form.
        consent_already_given = bool(getattr(partner, 'helpdesk_consent', False))
        consent_from_form = kw.get('helpdesk_consent') in ('on', 'true', '1', True)

        if not consent_already_given and not consent_from_form:
            # Re-render the form with an error message instead of silently failing
            faq_articles = request.env['helpdesk.knowledge.article'].get_faq_articles(limit=10)
            icp = request.env['ir.config_parameter'].sudo()
            privacy_policy_url = icp.get_param('support_helpdesk_ticket.privacy_policy_url', default='')
            values = {
                'page_name': 'create_ticket',
                'categories': request.env['helpdesk.category'].search([('active', '=', True)]),
                'ticket_types': request.env['helpdesk.ticket.type'].search([('active', '=', True)]),
                'faq_articles': faq_articles,
                'helpdesk_requires_consent': True,
                'helpdesk_privacy_policy_url': privacy_policy_url,
                'helpdesk_consent_error': True,
            }
            return request.render("support_helpdesk_ticket.portal_create_ticket", values)

        values = {}
        for field_name, field_value in kw.items():
            if field_name in request.env['helpdesk.ticket']._fields:
                values[field_name] = field_value
        
        # Set partner to current user's partner
        values['partner_id'] = partner.id
        values['channel'] = 'web'
        values['state'] = 'new'

        # Record consent if provided in the form and not already set
        if consent_from_form and not consent_already_given:
            partner.set_helpdesk_consent(consent=True, source='portal')
        
        # Create ticket
        ticket = request.env['helpdesk.ticket'].sudo().create(values)
        
        # Handle file uploads
        if 'attachment' in request.httprequest.files:
            attachments = request.httprequest.files.getlist('attachment')
            for attachment in attachments:
                if attachment.filename:
                    attachment_data = attachment.read()
                    request.env['ir.attachment'].sudo().create({
                        'name': attachment.filename,
                        'datas': attachment_data.encode('base64'),
                        'res_model': 'helpdesk.ticket',
                        'res_id': ticket.id,
                    })
        
        return request.redirect('/my/tickets/%s?access_token=%s' % (ticket.id, ticket._get_access_token()))

    @http.route(['/my/tickets/<int:ticket_id>/comment'], type='http', auth="user", website=False, methods=['POST'], csrf=True)
    def portal_ticket_comment(self, ticket_id=None, access_token=None, **kw):
        """Add comment to ticket"""
        try:
            ticket_sudo = self._document_check_access('helpdesk.ticket', ticket_id, access_token)
        except (AccessError, MissingError):
            return request.redirect('/my')
        
        # Ensure ticket belongs to current user's partner
        if ticket_sudo.partner_id != request.env.user.partner_id:
            return request.redirect('/my')
        
        comment = kw.get('comment', '').strip()
        if comment:
            subtype = request.env.ref('mail.mt_comment', raise_if_not_found=False)
            ticket_sudo.message_post(
                body=comment,
                message_type='comment',
                subtype_id=subtype.id if subtype else False,
            )
            
            # Handle file uploads
            if 'attachment' in request.httprequest.files:
                attachments = request.httprequest.files.getlist('attachment')
                for attachment in attachments:
                    if attachment.filename:
                        attachment_data = attachment.read()
                        request.env['ir.attachment'].sudo().create({
                            'name': attachment.filename,
                            'datas': attachment_data.encode('base64'),
                            'res_model': 'helpdesk.ticket',
                            'res_id': ticket_sudo.id,
                        })
        
        return request.redirect('/my/tickets/%s?access_token=%s' % (ticket_id, access_token or ticket_sudo._get_access_token()))

    @http.route(['/my/tickets/dashboard'], type='http', auth="user", website=False)
    def portal_ticket_dashboard(self, **kw):
        """Display customer ticket dashboard with statistics"""
        values = self._prepare_portal_layout_values()
        HelpdeskTicket = request.env['helpdesk.ticket']
        partner = request.env.user.partner_id
        
        # Domain: only tickets for current user's partner
        domain = [('partner_id', '=', partner.id)]
        
        # Calculate statistics
        total_tickets = HelpdeskTicket.search_count(domain)
        open_tickets = HelpdeskTicket.search_count(domain + [('state', 'in', ['new', 'assigned', 'in_progress'])])
        resolved_tickets = HelpdeskTicket.search_count(domain + [('state', '=', 'resolved')])
        closed_tickets = HelpdeskTicket.search_count(domain + [('state', '=', 'closed')])
        
        # Calculate average resolution time
        resolved_ticket_records = HelpdeskTicket.search(domain + [
            ('state', 'in', ['resolved', 'closed']),
            ('resolved_date', '!=', False),
            ('create_date', '!=', False),
        ])
        
        avg_resolution_time = 0
        if resolved_ticket_records:
            total_hours = 0
            count = 0
            for ticket in resolved_ticket_records:
                if ticket.resolved_date and ticket.create_date:
                    delta = ticket.resolved_date - ticket.create_date
                    total_hours += delta.total_seconds() / 3600
                    count += 1
            if count > 0:
                avg_resolution_time = total_hours / count
        
        # Ticket status distribution for chart
        status_distribution = {}
        for state in ['new', 'assigned', 'in_progress', 'resolved', 'closed', 'cancelled']:
            count = HelpdeskTicket.search_count(domain + [('state', '=', state)])
            status_distribution[state] = count
        
        # Recent tickets (last 10)
        recent_tickets = HelpdeskTicket.search(domain, order='create_date desc', limit=10)
        
        # Tickets by priority
        priority_distribution = {}
        for priority in ['0', '1', '2', '3']:
            count = HelpdeskTicket.search_count(domain + [('priority', '=', priority)])
            priority_labels = {'0': 'Low', '1': 'Medium', '2': 'High', '3': 'Urgent'}
            priority_distribution[priority_labels[priority]] = count
        
        # State, Priority, and Channel labels mapping
        state_labels = {
            'draft': 'Draft',
            'new': 'New',
            'assigned': 'Assigned',
            'in_progress': 'In Progress',
            'resolved': 'Resolved',
            'closed': 'Closed',
            'cancelled': 'Cancelled',
        }
        priority_labels = {
            '0': 'Low',
            '1': 'Medium',
            '2': 'High',
            '3': 'Urgent',
        }
        channel_labels = {
            'email': 'Email',
            'web': 'Web Portal',
            'phone': 'Phone',
            'social_media': 'Social Media',
        }
        
        values.update({
            'page_name': 'ticket_dashboard',
            'total_tickets': total_tickets,
            'open_tickets': open_tickets,
            'resolved_tickets': resolved_tickets,
            'closed_tickets': closed_tickets,
            'avg_resolution_time': avg_resolution_time,
            'avg_resolution_time_hours': int(avg_resolution_time),
            'avg_resolution_time_minutes': int((avg_resolution_time - int(avg_resolution_time)) * 60),
            'status_distribution': status_distribution,
            'priority_distribution': priority_distribution,
            'recent_tickets': recent_tickets,
            'state_labels': state_labels,
            'priority_labels': priority_labels,
            'channel_labels': channel_labels,
        })
        
        return request.render("support_helpdesk_ticket.portal_ticket_dashboard", values)

    # ==================== Data Privacy & GDPR Routes ====================

    @http.route(['/my/tickets/privacy'], type='http', auth="user", website=False)
    def portal_ticket_privacy(self, **kw):
        """Display data privacy and GDPR options for the current customer."""
        values = self._prepare_portal_layout_values()
        partner = request.env.user.partner_id.sudo()
        HelpdeskTicket = request.env['helpdesk.ticket'].sudo()

        domain = [('partner_id', '=', partner.id)]
        ticket_count = HelpdeskTicket.search_count(domain)

        icp = request.env['ir.config_parameter'].sudo()
        privacy_policy_url = icp.get_param('support_helpdesk_ticket.privacy_policy_url', default='')

        values.update({
            'page_name': 'ticket_privacy',
            'ticket_count': ticket_count,
            'partner': partner,
            'helpdesk_has_consent': bool(getattr(partner, 'helpdesk_consent', False)),
            'helpdesk_consent_date': getattr(partner, 'helpdesk_consent_date', False),
            'helpdesk_anonymized': bool(getattr(partner, 'helpdesk_anonymized', False)),
            'helpdesk_privacy_policy_url': privacy_policy_url,
            'status': kw.get('status'),
        })

        return request.render("support_helpdesk_ticket.portal_ticket_privacy", values)

    @http.route(['/my/tickets/privacy/export'], type='http', auth="user", website=False, methods=['GET'], csrf=False)
    def portal_ticket_privacy_export(self, **kw):
        """Export all helpdesk-related personal data for the current customer (GDPR data portability)."""
        partner = request.env.user.partner_id.sudo()
        HelpdeskTicket = request.env['helpdesk.ticket'].sudo()

        tickets = HelpdeskTicket.search([('partner_id', '=', partner.id)])

        export_payload = {
            'partner': {
                'id': partner.id,
                'name': partner.name,
                'email': partner.email,
                'phone': partner.phone,
                'company': partner.company_name,
                'country_id': partner.country_id.name if partner.country_id else False,
                'city': partner.city,
                'zip': partner.zip,
                'create_date': str(partner.create_date) if partner.create_date else False,
            },
            'tickets': [],
        }

        for ticket in tickets:
            messages = request.env['mail.message'].sudo().search([
                ('model', '=', 'helpdesk.ticket'),
                ('res_id', '=', ticket.id),
                ('message_type', '!=', 'notification'),
            ])

            attachments = request.env['ir.attachment'].sudo().search([
                ('res_model', '=', 'helpdesk.ticket'),
                ('res_id', '=', ticket.id),
            ])

            ticket_data = {
                'id': ticket.id,
                'ticket_number': ticket.ticket_number,
                'name': ticket.name,
                'description': ticket.description,
                'state': ticket.state,
                'priority': ticket.priority,
                'team': ticket.team_id.name if ticket.team_id else False,
                'assigned_to': ticket.user_id.name if ticket.user_id else False,
                'rating': ticket.rating,
                'feedback': ticket.feedback,
                'feedback_date': str(ticket.feedback_date) if ticket.feedback_date else False,
                'create_date': str(ticket.create_date) if ticket.create_date else False,
                'write_date': str(ticket.write_date) if ticket.write_date else False,
                'channel': ticket.channel,
                'personal_data_anonymized': getattr(ticket, 'personal_data_anonymized', False),
                'messages': [{
                    'id': msg.id,
                    'date': str(msg.date) if msg.date else False,
                    'author': msg.author_id.name,
                    'subject': msg.subject,
                    'body': msg.body,
                    'message_type': msg.message_type,
                } for msg in messages],
                'attachments': [{
                    'id': att.id,
                    'name': att.name,
                    'mimetype': att.mimetype,
                    'file_size': att.file_size,
                    'create_date': str(att.create_date) if att.create_date else False,
                } for att in attachments],
            }

            export_payload['tickets'].append(ticket_data)

        data = json.dumps(export_payload, ensure_ascii=False, indent=2, default=str)
        filename = 'helpdesk_data_partner_%s.json' % partner.id

        return request.make_response(
            data,
            headers=[
                ('Content-Type', 'application/json; charset=utf-8'),
                ('Content-Disposition', content_disposition(filename)),
            ]
        )

    @http.route(['/my/tickets/privacy/delete'], type='http', auth="user", website=False, methods=['POST'], csrf=True)
    def portal_ticket_privacy_delete(self, **kw):
        """Anonymize helpdesk-related personal data for the current customer (GDPR right to be forgotten)."""
        partner = request.env.user.partner_id.sudo()

        # Anonymize helpdesk data in tickets using partner model helper
        partner._helpdesk_anonymize_personal_data()

        return request.redirect('/my/tickets/privacy?status=deleted')

    # ==================== Knowledge Base Routes ====================
    
    @http.route(['/knowledge', '/knowledge/page/<int:page>'], type='http', auth="public", website=True)
    def portal_knowledge_base(self, page=1, sortby=None, filterby=None, search=None, search_in='all', category_id=None, **kw):
        """Display knowledge base articles"""
        KnowledgeArticle = request.env['helpdesk.knowledge.article']
        
        # Domain: only published and active articles
        domain = [
            ('state', '=', 'published'),
            ('active', '=', True),
        ]
        
        # Filter by category if provided
        if category_id:
            try:
                category_id = int(category_id)
                domain.append(('category_id', '=', category_id))
            except (ValueError, TypeError):
                pass
        
        # Search
        searchbar_sortings = {
            'date': {'label': 'Newest', 'order': 'create_date desc'},
            'popular': {'label': 'Most Viewed', 'order': 'view_count desc'},
            'rating': {'label': 'Highest Rated', 'order': 'rating desc'},
            'name': {'label': 'Title', 'order': 'name'},
        }
        searchbar_filters = {
            'all': {'label': 'All Articles', 'domain': []},
            'faq': {'label': 'FAQs', 'domain': [('is_faq', '=', True)]},
        }
        searchbar_inputs = {
            'all': {'input': 'all', 'label': 'Search in All'},
            'title': {'input': 'title', 'label': 'Search in Title'},
            'content': {'input': 'content', 'label': 'Search in Content'},
        }
        
        # Get categories for filter
        categories = request.env['helpdesk.category'].search([('active', '=', True)])
        
        # Defaults
        if not sortby:
            sortby = 'date'
        if not filterby:
            filterby = 'all'
        if not search_in:
            search_in = 'all'
        
        # Apply search
        if search and search_in:
            search_domain = []
            if search_in in ('title', 'all'):
                search_domain.append(('name', 'ilike', search))
            if search_in in ('content', 'all'):
                search_domain.append(('content', 'ilike', search))
            if search_domain:
                domain += ['|'] * (len(search_domain) - 1) + search_domain
        
        # Apply filter
        if filterby != 'all':
            domain += searchbar_filters[filterby]['domain']
        
        # Count
        article_count = KnowledgeArticle.search_count(domain)
        
        # Pager
        pager = portal_pager(
            url="/knowledge",
            url_args={'sortby': sortby, 'filterby': filterby, 'search_in': search_in, 'search': search, 'category_id': category_id},
            total=article_count,
            page=page,
            step=self._items_per_page
        )
        
        # Search articles
        articles = KnowledgeArticle.search(domain, order=searchbar_sortings[sortby]['order'], limit=self._items_per_page, offset=pager['offset'])
        
        values = {
            'articles': articles,
            'page_name': 'knowledge_base',
            'pager': pager,
            'searchbar_sortings': searchbar_sortings,
            'searchbar_filters': searchbar_filters,
            'searchbar_inputs': searchbar_inputs,
            'sortby': sortby,
            'filterby': filterby,
            'search_in': search_in,
            'search': search,
            'category_id': category_id,
            'categories': categories,
            'default_url': '/knowledge',
        }
        
        return request.render("support_helpdesk_ticket.portal_knowledge_base", values)
    
    @http.route(['/knowledge/<int:article_id>'], type='http', auth="public", website=True)
    def portal_knowledge_article(self, article_id=None, **kw):
        """Display knowledge base article detail"""
        try:
            article = request.env['helpdesk.knowledge.article'].sudo().browse(article_id)
            if article.state != 'published' or not article.active:
                return request.redirect('/knowledge')
        except:
            return request.redirect('/knowledge')
        
        # Track view
        article.action_track_view()
        
        # Get related articles
        related_articles = article.related_article_ids.filtered(
            lambda a: a.state == 'published' and a.active
        )[:5]
        
        # Get articles from same category
        same_category_articles = request.env['helpdesk.knowledge.article'].search([
            ('category_id', '=', article.category_id.id),
            ('state', '=', 'published'),
            ('active', '=', True),
            ('id', '!=', article.id),
        ], limit=5, order='view_count desc')
        
        # Get FAQ articles if this is not an FAQ
        faq_articles = []
        if not article.is_faq:
            faq_articles = request.env['helpdesk.knowledge.article'].get_faq_articles(
                category_id=article.category_id.id if article.category_id else False,
                limit=5
            )
        
        values = {
            'article': article,
            'page_name': 'knowledge_article',
            'related_articles': related_articles,
            'same_category_articles': same_category_articles,
            'faq_articles': faq_articles,
        }
        
        return request.render("support_helpdesk_ticket.portal_knowledge_article", values)
    
    @http.route(['/knowledge/category/<int:category_id>', '/knowledge/category/<int:category_id>/page/<int:page>'], 
                type='http', auth="public", website=True)
    def portal_knowledge_category(self, category_id=None, page=1, **kw):
        """Display articles by category"""
        try:
            category = request.env['helpdesk.category'].sudo().browse(category_id)
            if not category.exists() or not category.active:
                return request.redirect('/knowledge')
        except:
            return request.redirect('/knowledge')
        
        # Redirect to main knowledge base with category filter
        return request.redirect('/knowledge?category_id=%s' % category_id)
    
    @http.route(['/knowledge/<int:article_id>/feedback'], type='http', auth="public", website=True, methods=['POST'], csrf=True)
    def portal_knowledge_feedback(self, article_id=None, **kw):
        """Submit article feedback/rating"""
        try:
            article = request.env['helpdesk.knowledge.article'].sudo().browse(article_id)
            if article.state != 'published' or not article.active:
                return request.redirect('/knowledge')
        except:
            return request.redirect('/knowledge')
        
        # Get feedback data
        rating = kw.get('rating')
        feedback_text = kw.get('feedback', '').strip()
        helpful = kw.get('helpful') == 'on'
        
        # Get partner if user is logged in
        partner_id = False
        if request.env.user and not request.env.user._is_public():
            partner_id = request.env.user.partner_id.id
        
        # Create feedback
        if rating:
            request.env['helpdesk.knowledge.article.feedback'].sudo().create({
                'article_id': article.id,
                'partner_id': partner_id,
                'rating': rating,
                'feedback': feedback_text,
                'helpful': helpful,
            })
        
        return request.redirect('/knowledge/%s' % article_id)
    
    @http.route(['/faq', '/faq/page/<int:page>'], type='http', auth="public", website=True)
    def portal_faq(self, page=1, search=None, category_id=None, **kw):
        """Display FAQ articles"""
        KnowledgeArticle = request.env['helpdesk.knowledge.article']
        
        # Domain: only published, active FAQ articles
        domain = [
            ('is_faq', '=', True),
            ('state', '=', 'published'),
            ('active', '=', True),
        ]
        
        # Filter by category if provided
        if category_id:
            try:
                category_id = int(category_id)
                domain.append(('category_id', '=', category_id))
            except (ValueError, TypeError):
                pass
        
        # Search
        if search:
            domain += ['|', ('name', 'ilike', search), ('content', 'ilike', search)]
        
        # Get categories for filter
        categories = request.env['helpdesk.category'].search([('active', '=', True)])
        
        # Count
        faq_count = KnowledgeArticle.search_count(domain)
        
        # Pager
        pager = portal_pager(
            url="/faq",
            url_args={'search': search, 'category_id': category_id},
            total=faq_count,
            page=page,
            step=self._items_per_page
        )
        
        # Search FAQ articles
        faq_articles = KnowledgeArticle.search(domain, order='view_count desc, rating desc', limit=self._items_per_page, offset=pager['offset'])
        
        values = {
            'faq_articles': faq_articles,
            'page_name': 'faq',
            'pager': pager,
            'search': search,
            'category_id': category_id,
            'categories': categories,
            'default_url': '/faq',
        }
        
        return request.render("support_helpdesk_ticket.portal_faq", values)
