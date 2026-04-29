# -*- coding: utf-8 -*-
# Copyright 2025 Rafaël Daoud
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import json
import logging
import ssl
import uuid
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from werkzeug.urls import url_join

from odoo import _, models
from odoo.exceptions import ValidationError
from odoo.addons.payment import utils as payment_utils

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    def _get_specific_processing_values(self, processing_values):
        res = super()._get_specific_processing_values(processing_values)
        if self.provider_code != "square":
            return res
        self.ensure_one()
        return res

    def _get_specific_rendering_values(self, processing_values):
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != "square":
            return res
        self.ensure_one()
        return_url = url_join(
            self.provider_id.get_base_url(),
            self.landing_route or "",
        )
        res.update({
            "reference": self.reference,
            "return_url": return_url,
            "checkout_url": url_join(
                self.provider_id.get_base_url(),
                "/payment/square/checkout",
            ),
        })
        return res

    def _get_tx_from_notification_data(self, provider_code, notification_data):
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != "square" or len(tx) == 1:
            return tx
        reference = notification_data.get("reference")
        if reference:
            tx = self.search([
                ("reference", "=", reference),
                ("provider_code", "=", "square"),
            ], limit=1)
        if not tx:
            raise ValidationError(_(
                "Square: No transaction found matching reference %s.",
                reference,
            ))
        return tx

    def _process_notification_data(self, notification_data):
        super()._process_notification_data(notification_data)
        if self.provider_code != "square":
            return
        self.ensure_one()
        status = notification_data.get("status")
        self.provider_reference = notification_data.get("payment_id") or self.provider_reference
        if status == "COMPLETED":
            self._set_done()
        elif status in ("CANCELED", "FAILED"):
            self._set_canceled()
        else:
            err_msg = notification_data.get("error_message") or _(
                "Square returned status: %s",
                status or "unknown",
            )
            self._set_error(err_msg)

    def _send_refund_request(self, amount_to_refund=None):
        refund_tx = super()._send_refund_request(amount_to_refund=amount_to_refund)
        if self.provider_code != "square":
            return refund_tx
        refund_amount = payment_utils.to_minor_currency_units(
            -refund_tx.amount, refund_tx.currency_id
        )
        payload = {
            "idempotency_key": str(uuid.uuid4()),
            "amount_money": {
                "amount": int(refund_amount),
                "currency": self.currency_id.name,
            },
            "payment_id": self.provider_reference,
        }
        url = "https://connect.squareup.com/v2/refunds"
        token = self.provider_id.square_access_token
        headers = {
            "Square-Version": "2024-11-20",
            "Authorization": "Bearer %s" % token,
            "Content-Type": "application/json",
        }
        try:
            req = Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            with urlopen(req, context=ssl.create_default_context(), timeout=15) as r:
                data = json.loads(r.read().decode("utf-8"))
            if data.get("refund"):
                refund_tx._set_done()
            else:
                refund_tx._set_error(_("Square refund failed"))
        except (HTTPError, URLError, ValueError) as e:
            _logger.exception("Square refund failed")
            refund_tx._set_error("Square: " + str(e))
        return refund_tx
