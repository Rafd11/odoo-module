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
import os


class HelpdeskAPIDocumentationController(http.Controller):
    """Controller for displaying REST API Documentation"""

    @http.route('/helpdesk/api/documentation', type='http', auth='user', website=True)
    def api_documentation(self, **kwargs):
        """Display REST API Documentation page"""
        
        # Get the module path
        module_path = os.path.dirname(os.path.dirname(__file__))
        doc_path = os.path.join(module_path, 'README', 'API_DOCUMENTATION.md')
        
        # Try to read the markdown file
        markdown_content = ""
        try:
            if os.path.exists(doc_path):
                with open(doc_path, 'r', encoding='utf-8') as f:
                    markdown_content = f.read()
        except Exception as e:
            markdown_content = f"Error reading documentation file: {str(e)}"
        
        # If file not found or empty, use default content
        if not markdown_content:
            markdown_content = """
# REST API Documentation

## Overview

This REST API provides endpoints to manage discuss messages for helpdesk tickets.

**Base URL**: `/api/helpdesk/ticket/{ticket_id}/messages`

**Authentication**: Cookie-based session authentication (Odoo standard)

## Available Endpoints

1. **GET** `/api/helpdesk/ticket/<ticket_id>/messages` - Get all messages for a ticket
2. **POST** `/api/helpdesk/ticket/<ticket_id>/messages` - Create a new message
3. **GET** `/api/helpdesk/ticket/<ticket_id>/messages/<message_id>` - Get a specific message
4. **PUT** `/api/helpdesk/ticket/<ticket_id>/messages/<message_id>` - Update a message
5. **DELETE** `/api/helpdesk/ticket/<ticket_id>/messages/<message_id>` - Delete a message
6. **POST** `/api/helpdesk/ticket/<ticket_id>/messages/upload` - Upload attachment

For detailed documentation, please refer to the API_DOCUMENTATION.md file in the module's README folder.
"""
        
        # Convert markdown to HTML (basic conversion)
        html_content = self._markdown_to_html(markdown_content)
        
        # Get base URL - ensure proper formatting without double slashes
        base_url = request.httprequest.url_root.rstrip('/')
        # Ensure base_url ends with single slash for proper URL joining
        if base_url and not base_url.endswith('/'):
            base_url += '/'
        
        return request.render('support_helpdesk_ticket.api_documentation_page', {
            'content': html_content,
            'base_url': base_url,
        })
    
    def _markdown_to_html(self, markdown_text):
        """Convert markdown to HTML (enhanced implementation)"""
        import re
        
        html = markdown_text
        
        # Code blocks first (before inline code) - use placeholder to avoid wrapping in p tags
        code_blocks = []
        def code_block_replacer(match):
            lang = match.group(1) or ''
            code = match.group(2).strip()
            placeholder = f'__CODE_BLOCK_{len(code_blocks)}__'
            code_blocks.append(f'<pre><code class="language-{lang}">{code}</code></pre>')
            return placeholder
        
        html = re.sub(r'```(\w+)?\n(.*?)```', code_block_replacer, html, flags=re.DOTALL)
        
        # Headers
        html = re.sub(r'^#### (.*?)$', r'<h4>\1</h4>', html, flags=re.MULTILINE)
        html = re.sub(r'^### (.*?)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.*?)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        html = re.sub(r'^# (.*?)$', r'<h1>\1</h1>', html, flags=re.MULTILINE)
        
        # Bold
        html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', html)
        
        # Inline code (after code blocks) - simple approach
        # Match inline code but skip if it's part of a code block placeholder
        def inline_code_replacer(match):
            # Don't process if it's inside a code block placeholder
            if '__CODE_BLOCK_' in match.group(0):
                return match.group(0)
            return f'<code>{match.group(1)}</code>'
        
        html = re.sub(r'`([^`\n]+)`', inline_code_replacer, html)
        
        # Links
        html = re.sub(r'\[(.*?)\]\((.*?)\)', r'<a href="\2" target="_blank">\1</a>', html)
        
        # Horizontal rules
        html = re.sub(r'^---$', r'<hr>', html, flags=re.MULTILINE)
        
        # Process line by line to handle code blocks properly
        lines = html.split('\n')
        result = []
        in_table = False
        table_rows = []
        
        for line in lines:
            stripped = line.strip()
            
            # Check for table rows
            if '|' in stripped and stripped.startswith('|') and stripped.endswith('|'):
                if not in_table:
                    in_table = True
                    table_rows = []
                # Skip separator rows
                if not re.match(r'^\|[\s\-:]+\|$', stripped):
                    cells = [cell.strip() for cell in stripped.split('|')[1:-1]]
                    table_rows.append(cells)
                continue
            
            # Process table if we were in one
            if in_table:
                if table_rows:
                    result.append('<table class="table table-bordered" style="width: 100%; margin: 15px 0;">')
                    if table_rows:
                        result.append('<thead><tr>')
                        for cell in table_rows[0]:
                            result.append(f'<th style="padding: 10px; background: #0087cb; color: white;">{cell}</th>')
                        result.append('</tr></thead>')
                        result.append('<tbody>')
                        for row in table_rows[1:]:
                            result.append('<tr>')
                            for cell in row:
                                result.append(f'<td style="padding: 10px;">{cell}</td>')
                            result.append('</tr>')
                        result.append('</tbody></table>')
                in_table = False
                table_rows = []
            
            # Check for code block placeholder (must be checked before other HTML tags)
            if '__CODE_BLOCK_' in stripped:
                # Extract and add placeholder as-is (will be replaced later)
                result.append(stripped)
                continue
            
            # Check if it's already HTML
            if stripped.startswith('<'):
                result.append(stripped)
            elif stripped:
                result.append(f'<p>{stripped}</p>')
            else:
                result.append('')
        
        # Handle table at end of file
        if in_table and table_rows:
            result.append('<table class="table table-bordered" style="width: 100%; margin: 15px 0;">')
            if table_rows:
                result.append('<thead><tr>')
                for cell in table_rows[0]:
                    result.append(f'<th style="padding: 10px; background: #0087cb; color: white;">{cell}</th>')
                result.append('</tr></thead>')
                result.append('<tbody>')
                for row in table_rows[1:]:
                    result.append('<tr>')
                    for cell in row:
                        result.append(f'<td style="padding: 10px;">{cell}</td>')
                    result.append('</tr>')
                result.append('</tbody></table>')
        
        html = '\n'.join(result)
        
        # Restore code blocks BEFORE processing lists
        for i, code_block in enumerate(code_blocks):
            html = html.replace(f'__CODE_BLOCK_{i}__', code_block)
        
        # Lists (unordered) - process after code blocks are restored
        html = re.sub(r'<p>^- (.*?)</p>', r'<li>\1</li>', html, flags=re.MULTILINE)
        # Wrap consecutive list items
        html = re.sub(r'(<li>.*?</li>(?:\s*<li>.*?</li>)*)', r'<ul>\1</ul>', html, flags=re.DOTALL)
        
        # Lists (ordered)
        html = re.sub(r'<p>(\d+)\. (.*?)</p>', r'<li>\2</li>', html, flags=re.MULTILINE)
        # Wrap consecutive ordered list items
        html = re.sub(r'(<li>.*?</li>(?:\s*<li>.*?</li>)*)', r'<ol>\1</ol>', html, flags=re.DOTALL)
        
        # Final cleanup: remove any p tags that wrap pre tags
        html = re.sub(r'<p>\s*(<pre>.*?</pre>)\s*</p>', r'\1', html, flags=re.DOTALL)
        html = re.sub(r'<p>(<pre>.*?</pre>)</p>', r'\1', html, flags=re.DOTALL)
        
        return html
