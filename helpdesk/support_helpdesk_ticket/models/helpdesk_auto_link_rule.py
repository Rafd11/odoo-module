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

import re
import logging
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class HelpdeskAutoLinkRule(models.Model):
    _name = 'helpdesk.auto.link.rule'
    _description = 'Auto-Link Rule'
    _order = 'sequence, id'

    name = fields.Char(
        string='Rule Name',
        required=True,
        help='Name of the auto-linking rule'
    )
    description = fields.Text(
        string='Description',
        help='Description of what this rule does'
    )
    active = fields.Boolean(
        string='Active',
        default=True,
        help='Whether this rule is active'
    )
    sequence = fields.Integer(
        string='Priority',
        default=10,
        help='Lower number = higher priority. Rules are evaluated in order.'
    )
    
    # Model configuration
    target_model = fields.Char(
        string='Target Model',
        required=True,
        help='Technical name of the model to link (e.g., sale.order, account.move)'
    )
    model_display_name = fields.Char(
        string='Model Display Name',
        compute='_compute_model_display_name',
        help='Display name of the target model'
    )
    
    # Pattern configuration
    pattern_type = fields.Selection(
        [
            ('regex', 'Regular Expression'),
            ('prefix', 'Prefix Pattern'),
            ('suffix', 'Suffix Pattern'),
            ('contains', 'Contains Pattern'),
        ],
        string='Pattern Type',
        required=True,
        default='prefix',
        help='Type of pattern matching'
    )
    pattern = fields.Char(
        string='Pattern',
        required=True,
        help='Pattern to match (e.g., "SO" for sale orders, "INV" for invoices)'
    )
    pattern_regex = fields.Char(
        string='Regular Expression',
        help='Regular expression pattern (for regex type). Use groups to capture the record identifier.'
    )
    case_sensitive = fields.Boolean(
        string='Case Sensitive',
        default=False,
        help='Whether pattern matching is case sensitive'
    )
    
    # Search configuration
    search_field = fields.Char(
        string='Search Field',
        default='name',
        help='Field name to search in the target model (default: name)'
    )
    search_domain = fields.Text(
        string='Additional Domain',
        help='Additional domain to filter search results (e.g., [("state", "!=", "cancel")])'
    )
    
    # Conditions
    condition_domain = fields.Text(
        string='Condition Domain',
        help='Domain expression. Rule executes only if ticket matches this domain.'
    )
    priority_filter = fields.Selection(
        [
            ('0', 'Low'),
            ('1', 'Medium'),
            ('2', 'High'),
            ('3', 'Urgent'),
            ('all', 'All Priorities'),
        ],
        string='Priority Filter',
        default='all',
        help='Priority level this rule applies to'
    )
    category_ids = fields.Many2many(
        'helpdesk.category',
        'helpdesk_auto_link_rule_category_rel',
        'rule_id',
        'category_id',
        string='Categories',
        help='Categories this rule applies to (leave empty for all)'
    )
    
    # Execution tracking
    execution_count = fields.Integer(
        string='Execution Count',
        default=0,
        readonly=True,
        help='Number of links created by this rule'
    )
    last_execution_date = fields.Datetime(
        string='Last Execution',
        readonly=True,
        help='Date and time of last rule execution'
    )

    # ==================== UI Helper Actions ====================

    def action_test_rule(self):
        """UI action: basic validation / dry-run hook for the rule.

        Currently this just logs that a test was triggered; it can be
        extended to run against sample tickets.
        """
        for rule in self:
            _logger.info('Helpdesk auto-link rule "%s" (ID: %s) test triggered from UI.', rule.name, rule.id)
        return True

    @api.depends('target_model')
    def _compute_model_display_name(self):
        """Compute model display name"""
        for rule in self:
            if rule.target_model:
                try:
                    model = self.env['ir.model'].search([('model', '=', rule.target_model)], limit=1)
                    rule.model_display_name = model.name if model else rule.target_model
                except Exception:
                    rule.model_display_name = rule.target_model
            else:
                rule.model_display_name = False

    @api.constrains('target_model', 'pattern', 'pattern_type')
    def _check_pattern_configuration(self):
        """Validate pattern configuration"""
        for rule in self:
            if rule.pattern_type == 'regex' and not rule.pattern_regex:
                raise ValidationError(_('Regular expression pattern is required for regex type.'))
            if rule.pattern_type != 'regex' and not rule.pattern:
                raise ValidationError(_('Pattern is required for non-regex types.'))

    def _evaluate_condition(self, ticket):
        """Evaluate if ticket matches rule conditions"""
        self.ensure_one()
        
        if not self.active:
            return False
        
        # Check priority filter
        if self.priority_filter != 'all' and ticket.priority != self.priority_filter:
            return False
        
        # Check category filter
        if self.category_ids and ticket.category_id not in self.category_ids:
            return False
        
        # Evaluate domain condition
        if self.condition_domain:
            try:
                import ast
                domain = ast.literal_eval(self.condition_domain)
                if not ticket.filtered_domain(domain):
                    return False
            except (ValueError, SyntaxError):
                return False
        
        return True

    def _extract_references(self, text):
        """
        Extract model references from text based on rule pattern.
        Returns list of (identifier, match_text) tuples.
        """
        self.ensure_one()
        
        if not text:
            return []
        
        references = []
        flags = 0 if self.case_sensitive else re.IGNORECASE
        
        if self.pattern_type == 'regex':
            # Use regex pattern
            pattern = self.pattern_regex
            try:
                matches = re.finditer(pattern, text, flags)
                for match in matches:
                    # Use first group if available, otherwise full match
                    identifier = match.group(1) if match.groups() else match.group(0)
                    references.append((identifier, match.group(0)))
            except re.error as e:
                _logger.warning('Invalid regex pattern %s: %s', pattern, str(e))
        
        elif self.pattern_type == 'prefix':
            # Match pattern followed by alphanumeric identifier
            pattern = r'\b' + re.escape(self.pattern) + r'[\s\-_]?([A-Z0-9]+)\b'
            matches = re.finditer(pattern, text, flags)
            for match in matches:
                references.append((match.group(1), match.group(0)))
        
        elif self.pattern_type == 'suffix':
            # Match alphanumeric identifier followed by pattern
            pattern = r'\b([A-Z0-9]+)[\s\-_]?' + re.escape(self.pattern) + r'\b'
            matches = re.finditer(pattern, text, flags)
            for match in matches:
                references.append((match.group(1), match.group(0)))
        
        elif self.pattern_type == 'contains':
            # Match pattern anywhere in identifier
            pattern = r'\b([A-Z0-9]*' + re.escape(self.pattern) + r'[A-Z0-9]*)\b'
            matches = re.finditer(pattern, text, flags)
            for match in matches:
                references.append((match.group(1), match.group(0)))
        
        return references

    def _find_record(self, identifier):
        """
        Find record in target model matching the identifier.
        Returns recordset or False.
        """
        self.ensure_one()
        
        if not self.target_model or self.target_model not in self.env:
            return False
        
        model = self.env[self.target_model]
        search_field = self.search_field or 'name'
        
        # Build search domain
        domain = [(search_field, 'ilike', identifier)]
        
        # Add additional domain if specified
        if self.search_domain:
            try:
                import ast
                additional_domain = ast.literal_eval(self.search_domain)
                domain = ['&'] + domain + additional_domain
            except (ValueError, SyntaxError):
                pass
        
        # Search for exact match first
        records = model.search(domain, limit=10)
        
        # Try to find exact match
        for record in records:
            field_value = getattr(record, search_field, '')
            if field_value and identifier.upper() in str(field_value).upper():
                # Check for exact match (case-insensitive)
                if str(field_value).upper() == identifier.upper():
                    return record
                # Check if identifier is at the start/end
                field_upper = str(field_value).upper()
                id_upper = identifier.upper()
                if field_upper.startswith(id_upper) or field_upper.endswith(id_upper):
                    return record
        
        # Return first match if no exact match found
        return records[0] if records else False

    def create_link(self, ticket, identifier, match_text=None):
        """
        Create link for ticket if record found.
        Returns created link or False.
        """
        self.ensure_one()
        
        # Check conditions
        if not self._evaluate_condition(ticket):
            return False
        
        # Find record
        record = self._find_record(identifier)
        if not record:
            return False
        
        # Check if link already exists
        existing = self.env['helpdesk.ticket.model.link'].search([
            ('ticket_id', '=', ticket.id),
            ('model_name', '=', self.target_model),
            ('res_id', '=', record.id)
        ], limit=1)
        
        if existing:
            return False
        
        # Create link
        try:
            link = self.env['helpdesk.ticket.model.link'].create({
                'ticket_id': ticket.id,
                'model_name': self.target_model,
                'res_id': record.id,
            })
            
            # Update execution tracking
            self.write({
                'execution_count': self.execution_count + 1,
                'last_execution_date': fields.Datetime.now()
            })
            
            return link
        except Exception as e:
            _logger.error('Error creating auto-link for rule %s: %s', self.name, str(e))
            return False

    def process_ticket(self, ticket):
        """
        Process ticket and create auto-links based on rule patterns.
        Returns list of created links.
        """
        self.ensure_one()
        
        created_links = []
        
        # Extract text from ticket
        text_parts = []
        if ticket.name:
            text_parts.append(ticket.name)
        if ticket.description:
            # Strip HTML tags for text extraction
            import re as re_module
            text = re_module.sub(r'<[^>]+>', '', ticket.description)
            text_parts.append(text)
        if ticket.reference:
            text_parts.append(ticket.reference)
        
        text = ' '.join(text_parts)
        
        # Extract references
        references = self._extract_references(text)
        
        # Create links for each reference
        for identifier, match_text in references:
            link = self.create_link(ticket, identifier, match_text)
            if link:
                created_links.append(link)
        
        return created_links

    def action_test_rule(self):
        """Test rule on sample text"""
        self.ensure_one()
        return {
            'name': _('Test Auto-Link Rule'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.auto.link.rule.test.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_rule_id': self.id},
        }
