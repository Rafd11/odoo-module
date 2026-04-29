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

import logging

from odoo import models, fields, api, _
from odoo.exceptions import AccessError, ValidationError

_logger = logging.getLogger(__name__)


class HelpdeskTicketModelLink(models.Model):
    _name = 'helpdesk.ticket.model.link'
    _description = 'Helpdesk Ticket Model Link'
    _rec_name = 'res_name'
    _order = 'id desc'

    _sql_constraints = [
        ('uniq_ticket_model_res', 'unique(ticket_id, model_name, res_id)', 'This record is already linked to the ticket.'),
    ]

    ticket_id = fields.Many2one(
        'helpdesk.ticket',
        string='Ticket',
        required=True,
        ondelete='cascade',
        index=True
    )
    model_name = fields.Char(
        string='Model',
        required=True,
        help='Technical name of the Odoo model'
    )
    res_id = fields.Integer(
        string='Record ID',
        required=True,
        help='ID of the linked record'
    )
    # Reference field - simplified approach
    res_ref = fields.Reference(
        selection='_selection_res_ref_models',
        string='Linked Record',
        required=True,
        help='Select a model and record to link to this ticket'
    )
    res_name = fields.Char(
        string='Record Name',
        compute='_compute_res_name',
        store=True,
        help='Name of the linked record'
    )
    access_url = fields.Char(
        string='Access URL',
        compute='_compute_access_url',
        help='URL to access the linked record'
    )
    
    # Related data display fields
    related_data_summary = fields.Text(
        string='Related Data Summary',
        compute='_compute_related_data_summary',
        help='Summary of related data from the linked record'
    )
    
    # Access logging
    access_log_ids = fields.One2many(
        'helpdesk.model.link.access.log',
        'link_id',
        string='Access Logs',
        readonly=True,
        help='History of access attempts for this link'
    )
    access_log_count = fields.Integer(
        string='Access Log Count',
        compute='_compute_access_log_count',
        help='Number of access log entries'
    )

    @api.depends('res_ref')
    def _compute_res_name(self):
        """Compute the name of the linked record"""
        for link in self:
            if link.res_ref:
                try:
                    link.res_name = link.res_ref.display_name or str(link.res_ref)
                except Exception:
                    link.res_name = _('Invalid Record')
            else:
                link.res_name = False

    @api.depends('res_ref')
    def _compute_access_url(self):
        """Compute the URL to access the linked record"""
        for link in self:
            if link.res_ref:
                try:
                    link.access_url = '/web#id=%s&model=%s' % (link.res_ref.id, link.res_ref._name)
                except Exception:
                    link.access_url = False
            else:
                link.access_url = False

    @api.onchange('res_ref')
    def _onchange_res_ref(self):
        """Update model_name and res_id when res_ref changes"""
        for link in self:
            if link.res_ref:
                link.model_name = link.res_ref._name
                link.res_id = link.res_ref.id
            else:
                link.model_name = False
                link.res_id = False

    def action_open_linked_record(self):
        """Open the linked record in current tab"""
        self.ensure_one()
        if not self.res_ref:
            raise ValidationError(_('No linked record selected.'))
        
        self._log_access('open', 'success')
        
        return {
            'type': 'ir.actions.act_window',
            'res_model': self.model_name,
            'res_id': self.res_id,
            'view_mode': 'form',
            'target': 'current',
            'context': {
                'from_ticket_id': self.ticket_id.id,
                'from_ticket_number': self.ticket_id.ticket_number,
            },
        }
    
    def action_open_linked_record_new_tab(self):
        """Open linked record in new tab"""
        self.ensure_one()
        if not self.res_ref:
            raise ValidationError(_('No linked record selected.'))
        
        self._log_access('open', 'success')
        
        return {
            'type': 'ir.actions.act_url',
            'url': self.access_url,
            'target': 'new',
        }
    
    def action_view_access_logs(self):
        """View access logs for this link"""
        self.ensure_one()
        return {
            'name': _('Access Logs'),
            'type': 'ir.actions.act_window',
            'res_model': 'helpdesk.model.link.access.log',
            'view_mode': 'tree,form',
            'domain': [('link_id', '=', self.id)],
            'context': {'default_link_id': self.id},
        }
    
    def action_remove_link(self):
        """Remove/unlink this link"""
        self.ensure_one()
        ticket_id = self.ticket_id.id
        self.unlink()
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Link Removed'),
                'message': _('The link has been removed successfully.'),
                'type': 'success',
                'sticky': False,
            }
        }
    
    def action_validate_link(self):
        """Validate link and check if record still exists"""
        self.ensure_one()
        if not self.res_ref:
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Link Invalid'),
                    'message': _('No linked record selected.'),
                    'type': 'danger',
                    'sticky': True,
                }
            }
        
        try:
            if self.res_ref.exists():
                self._log_access('validate', 'success')
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Link Valid'),
                        'message': _('The linked record exists and is accessible.'),
                        'type': 'success',
                        'sticky': False,
                    }
                }
            else:
                self._log_access('validate', 'not_found', _('Record does not exist'))
                return {
                    'type': 'ir.actions.client',
                    'tag': 'display_notification',
                    'params': {
                        'title': _('Link Invalid'),
                        'message': _('The linked record does not exist.'),
                        'type': 'danger',
                        'sticky': True,
                    }
                }
        except Exception as e:
            self._log_access('validate', 'error', str(e))
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': _('Link Invalid'),
                    'message': _('Error validating link: %s') % str(e),
                    'type': 'danger',
                    'sticky': True,
                }
            }
    
    @api.model
    def action_bulk_validate(self, link_ids):
        """Validate multiple links"""
        links = self.browse(link_ids)
        valid_count = 0
        invalid_count = 0
        
        for link in links:
            try:
                if link.res_ref and link.res_ref.exists():
                    link._log_access('validate', 'success')
                    valid_count += 1
                else:
                    link._log_access('validate', 'not_found', _('Record does not exist'))
                    invalid_count += 1
            except Exception:
                invalid_count += 1
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Validation Complete'),
                'message': _('Valid: %d, Invalid: %d') % (valid_count, invalid_count),
                'type': 'success' if invalid_count == 0 else 'warning',
                'sticky': False,
            }
        }
    
    @api.model
    def action_bulk_remove(self, link_ids):
        """Remove multiple links"""
        links = self.browse(link_ids)
        count = len(links)
        links.unlink()
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Links Removed'),
                'message': _('%d link(s) removed successfully.') % count,
                'type': 'success',
                'sticky': False,
            }
        }

    @api.depends('access_log_ids')
    def _compute_access_log_count(self):
        """Compute access log count"""
        for link in self:
            link.access_log_count = len(link.access_log_ids)
    
    @api.depends('res_ref')
    def _compute_related_data_summary(self):
        """Compute related data summary for quick display"""
        for link in self:
            if not link.res_ref:
                link.related_data_summary = False
                continue
            
            try:
                record = link.res_ref
                
                if not record.exists():
                    link.related_data_summary = _('Record deleted')
                    continue
                
                # Try to get useful summary fields based on common patterns
                summary_parts = []
                
                # Common fields to display
                if hasattr(record, 'name') and record.name:
                    summary_parts.append(_('Name: %s') % record.name)
                if hasattr(record, 'state') and record.state:
                    state_field = record._fields.get('state')
                    if state_field and hasattr(state_field, 'selection'):
                        state_label = dict(state_field.selection).get(record.state, record.state)
                        summary_parts.append(_('State: %s') % state_label)
                    else:
                        summary_parts.append(_('State: %s') % record.state)
                if hasattr(record, 'date') and record.date:
                    summary_parts.append(_('Date: %s') % record.date)
                if hasattr(record, 'amount_total') and record.amount_total:
                    summary_parts.append(_('Amount: %s') % record.amount_total)
                if hasattr(record, 'partner_id') and record.partner_id:
                    summary_parts.append(_('Partner: %s') % record.partner_id.name)
                
                link.related_data_summary = '\n'.join(summary_parts) if summary_parts else _('No additional information available')
            except Exception:
                link.related_data_summary = _('Unable to load related data')

    # ==================== Reference field helpers ====================
    @api.model
    def _selection_res_ref_models(self):
        """
        Reference field selection: Returns models that users can link to tickets.
        """
        available = []
        
        # Common models that are typically linked to tickets
        common_models = [
            ('res.partner', 'Partner'),
            ('res.users', 'User'),
            ('sale.order', 'Sale Order'),
            ('account.move', 'Invoice'),
            ('purchase.order', 'Purchase Order'),
            ('project.task', 'Task'),
            ('project.project', 'Project'),
            ('crm.lead', 'Lead/Opportunity'),
            ('stock.picking', 'Delivery Order'),
            ('account.payment', 'Payment'),
            ('helpdesk.ticket', 'Helpdesk Ticket'),
        ]
        
        # Check access rights for common models
        for model_name, model_label in common_models:
            try:
                # Skip if model doesn't exist in registry
                if model_name not in self.env:
                    continue
                
                # Check if user has read access
                try:
                    self.env[model_name].check_access_rights('read', raise_exception=False)
                    available.append((model_name, model_label))
                except AccessError:
                    continue
            except Exception as e:
                _logger.debug('Skipping model %s: %s', model_name, str(e))
                continue
        
        # Also add other non-transient models that user has access to (limit to avoid too many options)
        try:
            models = self.env['ir.model'].search([
                ('transient', '=', False),
                ('model', 'not in', [m[0] for m in common_models])
            ], limit=50)
            
            for m in models:
                try:
                    if m.model not in self.env:
                        continue
                    
                    try:
                        self.env[m.model].check_access_rights('read', raise_exception=False)
                        available.append((m.model, m.name))
                    except AccessError:
                        continue
                except Exception as e:
                    _logger.debug('Skipping model %s: %s', m.model, str(e))
                    continue
        except Exception as e:
            _logger.warning('Error loading additional models: %s', str(e))
        
        # Sort by label for better UX
        available.sort(key=lambda x: x[1])
        
        return available

    @api.model_create_multi
    def create(self, vals_list):
        """Create with proper handling of res_ref field"""
        for vals in vals_list:
            res_ref = vals.get('res_ref')
            
            # Extract model_name and res_id from res_ref if provided
            if res_ref:
                if isinstance(res_ref, str):
                    # Format: "model,id"
                    parts = res_ref.split(',', 1)
                    if len(parts) == 2:
                        vals['model_name'] = parts[0].strip()
                        vals['res_id'] = int(parts[1].strip())
                    else:
                        raise ValidationError(_('Invalid linked record reference format.'))
                elif hasattr(res_ref, '_name'):  # It's a recordset
                    vals['model_name'] = res_ref._name
                    vals['res_id'] = res_ref.id
                else:
                    raise ValidationError(_('Invalid linked record reference type.'))
                
                # Validate the record exists and user has access
                model_name = vals.get('model_name')
                res_id = vals.get('res_id')
                
                if model_name and res_id:
                    if model_name not in self.env:
                        raise ValidationError(_('Invalid model: %s') % model_name)
                    
                    try:
                        model = self.env[model_name]
                        model.check_access_rights('read')
                        
                        record = model.browse(res_id)
                        if not record.exists():
                            raise ValidationError(_('Linked record does not exist (ID: %s).') % res_id)
                        
                        record.check_access_rule('read')
                    except AccessError as e:
                        raise AccessError(_('You do not have permission to link to this record: %s') % str(e))
        
        # Create records
        records = super().create(vals_list)
        
        # Log successful creation
        for record in records:
            if record.res_ref:
                try:
                    record._log_access('create', 'success')
                except Exception:
                    pass
        
        return records

    def write(self, vals):
        """Override write to handle res_ref updates"""
        if 'res_ref' in vals:
            res_ref = vals['res_ref']
            if res_ref:
                if isinstance(res_ref, str):
                    parts = res_ref.split(',', 1)
                    if len(parts) == 2:
                        vals['model_name'] = parts[0].strip()
                        vals['res_id'] = int(parts[1].strip())
                    else:
                        raise ValidationError(_('Invalid linked record reference format.'))
                elif hasattr(res_ref, '_name'):
                    vals['model_name'] = res_ref._name
                    vals['res_id'] = res_ref.id
            else:
                vals['model_name'] = False
                vals['res_id'] = False
        
        return super().write(vals)
    
    def _log_access(self, access_type, status, error_message=None):
        """
        Log access attempt.
        
        :param access_type: Type of access ('create', 'read', 'open', 'validate')
        :param status: Status ('success', 'denied', 'error', 'not_found')
        :param error_message: Error message if access failed
        """
        for link in self:
            if not link.model_name or not link.res_id:
                return
            
            # Get IP address from request if available
            ip_address = None
            try:
                request = self.env.context.get('request')
                if request:
                    ip_address = request.httprequest.environ.get('REMOTE_ADDR')
            except Exception:
                pass
            
            try:
                self.env['helpdesk.model.link.access.log'].create({
                    'link_id': link.id,
                    'user_id': self.env.user.id,
                    'access_type': access_type,
                    'model_name': link.model_name,
                    'res_id': link.res_id,
                    'status': status,
                    'error_message': error_message,
                    'ip_address': ip_address,
                })
            except Exception:
                # Don't fail if logging fails
                pass
