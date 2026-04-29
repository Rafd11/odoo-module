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
from odoo.exceptions import ValidationError, AccessError
import json
import base64


class HelpdeskRestAPIController(http.Controller):
    """REST API Controller for Helpdesk Ticket Discuss Messages"""

    def _prepare_message_data(self, message):
        """Prepare message data for JSON response"""
        return {
            'id': message.id,
            'ticket_id': message.ticket_id.id,
            'ticket_number': message.ticket_id.ticket_number,
            'date': message.date.isoformat() if message.date else None,
            'message_type': message.message_type,
            'message': message.message,
            'user_id': {
                'id': message.user_id.id,
                'name': message.user_id.name,
            } if message.user_id else None,
            'attachments': [
                {
                    'id': att.id,
                    'name': att.name,
                    'mimetype': att.mimetype,
                    'file_size': att.file_size,
                    'url': '/web/content/%s' % att.id,
                }
                for att in message.attachment_ids
            ],
        }

    @http.route('/api/helpdesk/ticket/<int:ticket_id>/messages', type='http', auth='user', methods=['GET'], csrf=False)
    def get_ticket_messages(self, ticket_id, **kwargs):
        """Get all messages for a ticket
        
        GET /api/helpdesk/ticket/{ticket_id}/messages
        
        Returns:
            JSON list of messages
        """
        try:
            ticket = request.env['helpdesk.ticket'].browse(ticket_id)
            if not ticket.exists():
                return request.make_response(
                    json.dumps({'error': 'Ticket not found'}),
                    headers=[('Content-Type', 'application/json')],
                    status=404
                )
            
            # Check access rights
            if not ticket.check_access_rights('read', raise_exception=False):
                return request.make_response(
                    json.dumps({'error': 'Access denied'}),
                    headers=[('Content-Type', 'application/json')],
                    status=403
                )
            
            messages = request.env['helpdesk.ticket.message'].search([
                ('ticket_id', '=', ticket_id)
            ], order='date desc, id desc')
            
            result = {
                'success': True,
                'ticket_id': ticket_id,
                'ticket_number': ticket.ticket_number,
                'count': len(messages),
                'messages': [self._prepare_message_data(msg) for msg in messages]
            }
            
            return request.make_response(
                json.dumps(result),
                headers=[('Content-Type', 'application/json')]
            )
            
        except Exception as e:
            return request.make_response(
                json.dumps({'error': str(e)}),
                headers=[('Content-Type', 'application/json')],
                status=500
            )

    @http.route('/api/helpdesk/ticket/<int:ticket_id>/messages', type='http', auth='user', methods=['POST'], csrf=False)
    def create_ticket_message(self, ticket_id, **kwargs):
        """Create a new message for a ticket
        
        POST /api/helpdesk/ticket/{ticket_id}/messages
        
        Body (JSON):
            {
                "message": "Message content",
                "message_type": "customer" | "team",
                "date": "2026-01-29T10:00:00" (optional),
                "attachment_ids": [1, 2, 3] (optional - attachment IDs)
            }
        
        Returns:
            JSON object with created message data
        """
        try:
            ticket = request.env['helpdesk.ticket'].browse(ticket_id)
            if not ticket.exists():
                return request.make_response(
                    json.dumps({'error': 'Ticket not found'}),
                    headers=[('Content-Type', 'application/json')],
                    status=404
                )
            
            # Check access rights
            if not ticket.check_access_rights('read', raise_exception=False):
                return request.make_response(
                    json.dumps({'error': 'Access denied'}),
                    headers=[('Content-Type', 'application/json')],
                    status=403
                )
            
            # Parse JSON body
            try:
                data = json.loads(request.httprequest.data.decode('utf-8'))
            except:
                data = kwargs
            
            # Validate required fields
            if not data.get('message'):
                return request.make_response(
                    json.dumps({'error': 'Message is required'}),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )
            
            message_type = data.get('message_type', 'team')
            if message_type not in ['customer', 'team']:
                return request.make_response(
                    json.dumps({'error': 'message_type must be "customer" or "team"'}),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )
            
            # Create message
            message_vals = {
                'ticket_id': ticket_id,
                'message': data.get('message'),
                'message_type': message_type,
                'user_id': request.env.user.id,
            }
            
            if data.get('date'):
                message_vals['date'] = data.get('date')
            
            if data.get('attachment_ids'):
                message_vals['attachment_ids'] = [(6, 0, data.get('attachment_ids'))]
            
            message = request.env['helpdesk.ticket.message'].create(message_vals)
            
            result = {
                'success': True,
                'message': self._prepare_message_data(message)
            }
            
            return request.make_response(
                json.dumps(result),
                headers=[('Content-Type', 'application/json')],
                status=201
            )
            
        except ValidationError as e:
            return request.make_response(
                json.dumps({'error': str(e)}),
                headers=[('Content-Type', 'application/json')],
                status=400
            )
        except Exception as e:
            return request.make_response(
                json.dumps({'error': str(e)}),
                headers=[('Content-Type', 'application/json')],
                status=500
            )

    @http.route('/api/helpdesk/ticket/<int:ticket_id>/messages/<int:message_id>', type='http', auth='user', methods=['GET'], csrf=False)
    def get_ticket_message(self, ticket_id, message_id, **kwargs):
        """Get a specific message for a ticket
        
        GET /api/helpdesk/ticket/{ticket_id}/messages/{message_id}
        
        Returns:
            JSON object with message data
        """
        try:
            ticket = request.env['helpdesk.ticket'].browse(ticket_id)
            if not ticket.exists():
                return request.make_response(
                    json.dumps({'error': 'Ticket not found'}),
                    headers=[('Content-Type', 'application/json')],
                    status=404
                )
            
            message = request.env['helpdesk.ticket.message'].browse(message_id)
            if not message.exists() or message.ticket_id.id != ticket_id:
                return request.make_response(
                    json.dumps({'error': 'Message not found'}),
                    headers=[('Content-Type', 'application/json')],
                    status=404
                )
            
            # Check access rights
            if not ticket.check_access_rights('read', raise_exception=False):
                return request.make_response(
                    json.dumps({'error': 'Access denied'}),
                    headers=[('Content-Type', 'application/json')],
                    status=403
                )
            
            result = {
                'success': True,
                'message': self._prepare_message_data(message)
            }
            
            return request.make_response(
                json.dumps(result),
                headers=[('Content-Type', 'application/json')]
            )
            
        except Exception as e:
            return request.make_response(
                json.dumps({'error': str(e)}),
                headers=[('Content-Type', 'application/json')],
                status=500
            )

    @http.route('/api/helpdesk/ticket/<int:ticket_id>/messages/<int:message_id>', type='http', auth='user', methods=['PUT'], csrf=False)
    def update_ticket_message(self, ticket_id, message_id, **kwargs):
        """Update a message for a ticket
        
        PUT /api/helpdesk/ticket/{ticket_id}/messages/{message_id}
        
        Body (JSON):
            {
                "message": "Updated message content",
                "message_type": "customer" | "team" (optional),
                "date": "2026-01-29T10:00:00" (optional),
                "attachment_ids": [1, 2, 3] (optional)
            }
        
        Returns:
            JSON object with updated message data
        """
        try:
            ticket = request.env['helpdesk.ticket'].browse(ticket_id)
            if not ticket.exists():
                return request.make_response(
                    json.dumps({'error': 'Ticket not found'}),
                    headers=[('Content-Type', 'application/json')],
                    status=404
                )
            
            message = request.env['helpdesk.ticket.message'].browse(message_id)
            if not message.exists() or message.ticket_id.id != ticket_id:
                return request.make_response(
                    json.dumps({'error': 'Message not found'}),
                    headers=[('Content-Type', 'application/json')],
                    status=404
                )
            
            # Check access rights
            if not message.check_access_rights('write', raise_exception=False):
                return request.make_response(
                    json.dumps({'error': 'Access denied'}),
                    headers=[('Content-Type', 'application/json')],
                    status=403
                )
            
            # Parse JSON body
            try:
                data = json.loads(request.httprequest.data.decode('utf-8'))
            except:
                data = kwargs
            
            # Prepare update values
            update_vals = {}
            if 'message' in data:
                update_vals['message'] = data['message']
            if 'message_type' in data:
                if data['message_type'] not in ['customer', 'team']:
                    return request.make_response(
                        json.dumps({'error': 'message_type must be "customer" or "team"'}),
                        headers=[('Content-Type', 'application/json')],
                        status=400
                    )
                update_vals['message_type'] = data['message_type']
            if 'date' in data:
                update_vals['date'] = data['date']
            if 'attachment_ids' in data:
                update_vals['attachment_ids'] = [(6, 0, data['attachment_ids'])]
            
            if update_vals:
                message.write(update_vals)
            
            result = {
                'success': True,
                'message': self._prepare_message_data(message)
            }
            
            return request.make_response(
                json.dumps(result),
                headers=[('Content-Type', 'application/json')]
            )
            
        except ValidationError as e:
            return request.make_response(
                json.dumps({'error': str(e)}),
                headers=[('Content-Type', 'application/json')],
                status=400
            )
        except Exception as e:
            return request.make_response(
                json.dumps({'error': str(e)}),
                headers=[('Content-Type', 'application/json')],
                status=500
            )

    @http.route('/api/helpdesk/ticket/<int:ticket_id>/messages/<int:message_id>', type='http', auth='user', methods=['DELETE'], csrf=False)
    def delete_ticket_message(self, ticket_id, message_id, **kwargs):
        """Delete a message for a ticket
        
        DELETE /api/helpdesk/ticket/{ticket_id}/messages/{message_id}
        
        Returns:
            JSON object with success status
        """
        try:
            ticket = request.env['helpdesk.ticket'].browse(ticket_id)
            if not ticket.exists():
                return request.make_response(
                    json.dumps({'error': 'Ticket not found'}),
                    headers=[('Content-Type', 'application/json')],
                    status=404
                )
            
            message = request.env['helpdesk.ticket.message'].browse(message_id)
            if not message.exists() or message.ticket_id.id != ticket_id:
                return request.make_response(
                    json.dumps({'error': 'Message not found'}),
                    headers=[('Content-Type', 'application/json')],
                    status=404
                )
            
            # Check access rights
            if not message.check_access_rights('unlink', raise_exception=False):
                return request.make_response(
                    json.dumps({'error': 'Access denied'}),
                    headers=[('Content-Type', 'application/json')],
                    status=403
                )
            
            message.unlink()
            
            result = {
                'success': True,
                'message': 'Message deleted successfully'
            }
            
            return request.make_response(
                json.dumps(result),
                headers=[('Content-Type', 'application/json')]
            )
            
        except Exception as e:
            return request.make_response(
                json.dumps({'error': str(e)}),
                headers=[('Content-Type', 'application/json')],
                status=500
            )

    @http.route('/api/helpdesk/ticket/<int:ticket_id>/messages/upload', type='http', auth='user', methods=['POST'], csrf=False)
    def upload_attachment(self, ticket_id, **kwargs):
        """Upload an attachment for a ticket message
        
        POST /api/helpdesk/ticket/{ticket_id}/messages/upload
        
        Form data:
            - file: The file to upload
            - name: (optional) Custom name for the attachment
        
        Returns:
            JSON object with attachment data
        """
        try:
            ticket = request.env['helpdesk.ticket'].browse(ticket_id)
            if not ticket.exists():
                return request.make_response(
                    json.dumps({'error': 'Ticket not found'}),
                    headers=[('Content-Type', 'application/json')],
                    status=404
                )
            
            # Check access rights
            if not ticket.check_access_rights('read', raise_exception=False):
                return request.make_response(
                    json.dumps({'error': 'Access denied'}),
                    headers=[('Content-Type', 'application/json')],
                    status=403
                )
            
            # Get uploaded file
            file = request.httprequest.files.get('file')
            if not file:
                return request.make_response(
                    json.dumps({'error': 'No file provided'}),
                    headers=[('Content-Type', 'application/json')],
                    status=400
                )
            
            # Read file content
            file_content = file.read()
            file_name = kwargs.get('name') or file.filename or 'attachment'
            
            # Create attachment
            attachment = request.env['ir.attachment'].create({
                'name': file_name,
                'datas': base64.b64encode(file_content),
                'res_model': 'helpdesk.ticket.message',
                'res_id': False,  # Will be linked when message is created
            })
            
            result = {
                'success': True,
                'attachment': {
                    'id': attachment.id,
                    'name': attachment.name,
                    'mimetype': attachment.mimetype,
                    'file_size': attachment.file_size,
                    'url': '/web/content/%s' % attachment.id,
                }
            }
            
            return request.make_response(
                json.dumps(result),
                headers=[('Content-Type', 'application/json')],
                status=201
            )
            
        except Exception as e:
            return request.make_response(
                json.dumps({'error': str(e)}),
                headers=[('Content-Type', 'application/json')],
                status=500
            )
