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

from odoo import http
from odoo.http import request
from odoo.exceptions import ValidationError
import re
import base64


class HelpdeskPublicController(http.Controller):
    """Public controller for ticket submission (no authentication required)"""

    @http.route(['/support/ticket', '/support/ticket/submit'], type='http', auth="public", website=False, methods=['GET', 'POST'], csrf=True)
    def public_create_ticket(self, **post):
        """Public ticket submission form"""
        error = {}
        success = False
        ticket_number = None
        
        if request.httprequest.method == 'POST':
            # CAPTCHA validation (simple honeypot field)
            if post.get('website', ''):  # Honeypot field - should be empty
                # Bot detected, silently fail
                return request.render("support_helpdesk_ticket.public_create_ticket", {
                    'error': {},
                    'success': False,
                    'categories': request.env['helpdesk.category'].sudo().search([('active', '=', True)]),
                })
            
            # Form validation
            required_fields = {
                'name': 'Subject',
                'description': 'Description',
                'customer_name': 'Your Name',
                'customer_email': 'Email Address',
            }
            
            for field, label in required_fields.items():
                if not post.get(field) or not post.get(field).strip():
                    error[field] = '%s is required' % label
            
            # Email validation
            customer_email = post.get('customer_email', '').strip()
            if customer_email and not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', customer_email):
                error['customer_email'] = 'Please enter a valid email address'
            
            # If no errors, create ticket
            if not error:
                # Find or create partner
                partner = request.env['res.partner'].sudo().search([
                    ('email', '=', customer_email)
                ], limit=1)
                
                if not partner:
                    partner = request.env['res.partner'].sudo().create({
                        'name': post.get('customer_name', '').strip(),
                        'email': customer_email,
                        'is_company': False,
                    })
                
                # Prepare ticket values
                ticket_vals = {
                    'name': post.get('name', '').strip(),
                    'description': post.get('description', '').strip(),
                    'partner_id': partner.id,
                    'channel': 'web',
                    'state': 'new',
                }
                
                # Add category if provided
                if post.get('category_id'):
                    try:
                        ticket_vals['category_id'] = int(post.get('category_id'))
                    except (ValueError, TypeError):
                        pass
                
                # Add priority if provided
                if post.get('priority'):
                    ticket_vals['priority'] = post.get('priority')
                
                # Create ticket
                ticket = request.env['helpdesk.ticket'].sudo().create(ticket_vals)
                ticket_number = ticket.ticket_number
                
                # Handle file uploads
                if 'attachment' in request.httprequest.files:
                    attachments = request.httprequest.files.getlist('attachment')
                    for attachment in attachments:
                        if attachment.filename:
                            attachment_data = attachment.read()
                            request.env['ir.attachment'].sudo().create({
                                'name': attachment.filename,
                                'datas': base64.b64encode(attachment_data).decode('utf-8'),
                                'res_model': 'helpdesk.ticket',
                                'res_id': ticket.id,
                            })
                
                # Send confirmation email
                template = request.env.ref(
                    'support_helpdesk_ticket.email_template_ticket_created',
                    raise_if_not_found=False
                )
                if template:
                    template.sudo().send_mail(ticket.id, force_send=True)
                
                success = True
                # Redirect to confirmation page
                return request.redirect('/support/ticket/confirm?ticket=%s' % ticket_number)
        
        # GET request or validation errors
        categories = request.env['helpdesk.category'].sudo().search([('active', '=', True)])
        priorities = request.env['helpdesk.ticket'].sudo()._fields['priority'].selection
        
        return request.render("support_helpdesk_ticket.public_create_ticket", {
            'error': error,
            'success': success,
            'ticket_number': ticket_number,
            'categories': categories,
            'priorities': priorities,
            'default_values': post,
        })

    @http.route(['/support/ticket/confirm'], type='http', auth="public", website=False)
    def public_ticket_confirm(self, ticket=None, **kw):
        """Ticket submission confirmation page"""
        ticket_obj = None
        if ticket:
            ticket_obj = request.env['helpdesk.ticket'].sudo().search([
                ('ticket_number', '=', ticket)
            ], limit=1)
        
        return request.render("support_helpdesk_ticket.public_ticket_confirm", {
            'ticket': ticket_obj,
            'ticket_number': ticket,
        })
