# -*- coding: utf-8 -*-
# Copyright 2025 Rafaël Daoud
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import json
import logging
import ssl
import uuid
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from odoo import http
from odoo.http import request

_logger = logging.getLogger(__name__)

SQUARE_API_BASE = "https://connect.squareup.com"
SQUARE_API_VERSION = "2024-11-20"


class PaymentSquareController(http.Controller):
    """Square payment provider: create payment from Web Payments token, checkout page."""

    @http.route(
        "/payment/square/create_payment",
        type="http",
        auth="public",
        methods=["POST"],
        csrf=False,
    )
    def square_create_payment(self, reference=None, source_id=None, **kwargs):
        if not reference or not source_id:
            return request.redirect("/payment/pay?error=missing_params")
        tx_sudo = (
            request.env["payment.transaction"]
            .sudo()
            .search([("reference", "=", reference), ("provider_code", "=", "square")], limit=1)
        )
        if not tx_sudo or tx_sudo.state not in ("draft", "pending"):
            return request.redirect("/payment/pay?error=invalid_tx")
        provider = tx_sudo.provider_id
        token = (provider.square_access_token or "").strip()
        if not token:
            return request.redirect("/payment/pay?error=provider_misconfigured")
        amount_cents = int(round(float(tx_sudo.amount) * 100))
        currency = (tx_sudo.currency_id.name or "USD").upper()
        idempotency_key = str(uuid.uuid4())
        payload = {
            "source_id": source_id,
            "idempotency_key": idempotency_key[:45],
            "amount_money": {"amount": amount_cents, "currency": currency},
            "reference_id": reference[:40],
            "autocomplete": True,
        }
        if provider.square_location_id:
            payload["location_id"] = provider.square_location_id.strip()
        url = "%s/v2/payments" % SQUARE_API_BASE
        headers = {
            "Square-Version": SQUARE_API_VERSION,
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
            with urlopen(req, context=ssl.create_default_context(), timeout=20) as r:
                data = json.loads(r.read().decode("utf-8"))
            payment = data.get("payment") or {}
            status = payment.get("status")
            notification_data = {
                "reference": reference,
                "status": status,
                "payment_id": payment.get("id"),
            }
            if data.get("errors"):
                err = data["errors"][0]
                notification_data["status"] = "FAILED"
                notification_data["error_message"] = err.get("detail", err.get("code", "Unknown error"))
            tx_sudo._handle_notification_data("square", notification_data)
        except HTTPError as e:
            err_msg = "Square API error (%s)" % e.code
            try:
                body = json.loads(e.read().decode("utf-8"))
                if body.get("errors"):
                    err_msg = body["errors"][0].get("detail", err_msg)
            except Exception:
                pass
            _logger.warning("Square create_payment HTTP error: %s", err_msg)
            notification_data = {
                "reference": reference,
                "status": "FAILED",
                "error_message": err_msg,
            }
            tx_sudo._handle_notification_data("square", notification_data)
        except (URLError, OSError, ValueError) as e:
            _logger.exception("Square create_payment failed")
            tx_sudo._handle_notification_data("square", {
                "reference": reference,
                "status": "FAILED",
                "error_message": str(e),
            })
        base = request.httprequest.url_root.rstrip("/")
        landing = (tx_sudo.landing_route or "/payment/confirmation").lstrip("/")
        return request.redirect("%s/%s" % (base, landing))

    @http.route(
        "/payment/square/checkout",
        type="http",
        auth="public",
        methods=["GET"],
        website=True,
    )
    def square_checkout(self, reference=None, return_url=None, **kwargs):
        if not reference:
            return request.redirect("/payment/pay?error=missing_reference")
        tx_sudo = (
            request.env["payment.transaction"]
            .sudo()
            .search([("reference", "=", reference), ("provider_code", "=", "square")], limit=1)
        )
        if not tx_sudo:
            return request.redirect("/payment/pay?error=invalid_tx")
        provider = tx_sudo.provider_id
        if not provider.square_application_id:
            return request.redirect("/payment/pay?error=provider_misconfigured")
        amount_display = "%s %s" % (tx_sudo.amount, tx_sudo.currency_id.symbol or tx_sudo.currency_id.name)
        return request.render("pos_square_terminal.square_checkout_page", {
            "reference": reference,
            "return_url": return_url or "",
            "amount_display": amount_display,
            "application_id": provider.square_application_id,
            "location_id": provider.square_location_id or "",
            "amount_minor": int(round(tx_sudo.amount * 100)),
            "currency": tx_sudo.currency_id.name.upper(),
            "state": provider.state,
        })
