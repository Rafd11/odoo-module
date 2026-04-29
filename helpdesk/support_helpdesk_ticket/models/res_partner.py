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


class ResPartner(models.Model):
    _inherit = 'res.partner'

    helpdesk_consent = fields.Boolean(
        string='Helpdesk Data Processing Consent',
        help='Indicates whether the contact has consented to the processing of their data for helpdesk purposes.',
    )
    helpdesk_consent_date = fields.Datetime(
        string='Helpdesk Consent Date',
        help='Date when the contact provided consent for helpdesk data processing.',
    )
    helpdesk_consent_source = fields.Selection(
        [
            ('portal', 'Customer Portal'),
            ('manual', 'Manual'),
            ('import', 'Data Import'),
        ],
        string='Helpdesk Consent Source',
        help='Source from which helpdesk consent was obtained.',
    )
    helpdesk_anonymized = fields.Boolean(
        string='Helpdesk Data Anonymized',
        help='True if personal data related to this contact has been anonymized in helpdesk tickets.',
        readonly=True,
    )

    def set_helpdesk_consent(self, consent=True, source='manual'):
        """Set or revoke helpdesk consent for the partner.

        :param consent: Boolean indicating whether consent is granted.
        :param source: Source of the consent (portal, manual, import).
        """
        for partner in self:
            values = {
                'helpdesk_consent': bool(consent),
                'helpdesk_consent_source': source or 'manual',
            }
            if consent:
                values['helpdesk_consent_date'] = fields.Datetime.now()
            partner.write(values)

    def _helpdesk_anonymize_personal_data(self):
        """Anonymize personal data related to this partner in helpdesk tickets.

        This keeps ticket records for reporting purposes while removing
        or neutralizing personal data, supporting the GDPR right to be forgotten
        within the helpdesk context.
        """
        HelpdeskTicket = self.env['helpdesk.ticket'].sudo()
        for partner in self:
            if partner.helpdesk_anonymized:
                continue

            tickets = HelpdeskTicket.search([('partner_id', '=', partner.id)])
            anonymized_label = _('Anonymized Customer')
            now = fields.Datetime.now()

            for ticket in tickets:
                # Only anonymize once per ticket
                if getattr(ticket, 'personal_data_anonymized', False):
                    continue

                note_suffix = _('\n\n[Customer personal data anonymized on %s]') % now
                internal_note = (ticket.internal_note or '') + note_suffix

                ticket_vals = {
                    'name': ticket.name or _('Anonymized Ticket %s') % (ticket.ticket_number or ticket.id),
                    'description': False,
                    'feedback': False,
                    'partner_name': anonymized_label,
                    'partner_email': False,
                    'partner_phone': False,
                    'internal_note': internal_note,
                }

                # Mark ticket as anonymized if the field exists
                if 'personal_data_anonymized' in ticket._fields:
                    ticket_vals['personal_data_anonymized'] = True

                ticket.write(ticket_vals)

            partner.write({
                'helpdesk_anonymized': True,
            })

