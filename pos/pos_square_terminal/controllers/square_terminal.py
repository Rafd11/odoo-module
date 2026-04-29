# -*- coding: utf-8 -*-
# Copyright 2025 Rafaël, Cursor
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


def _urlopen_json(method, url, data=None, headers=None, timeout=15):
    """Open URL and return parsed JSON. data is dict for POST body."""
    req_headers = {"Content-Type": "application/json", **(headers or {})}
    req = Request(url, data=json.dumps(data).encode("utf-8") if data else None, headers=req_headers, method=method)
    ctx = ssl.create_default_context()
    with urlopen(req, context=ctx, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def _urlopen_get_json(url, headers=None, timeout=10):
    req = Request(url, headers=headers or {}, method="GET")
    ctx = ssl.create_default_context()
    with urlopen(req, context=ctx, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


class PosSquareTerminalController(http.Controller):
    """Create Square Terminal checkouts and poll status for POS."""

    @http.route(
        "/pos_square_terminal/create_checkout",
        type="json",
        auth="user",
        methods=["POST"],
    )
    def create_checkout(self, amount, currency, payment_method_id, reference=None, note=None):
        """
        Create a Square Terminal checkout. Amount in monetary units (e.g. 25.50 for $25.50).
        Optional note (e.g. order line summary) is shown on the terminal and receipt.
        Returns { "checkout_id": "...", "status": "PENDING" } or { "error": "..." }.
        """
        if not amount or amount <= 0:
            return {"error": "Invalid amount"}
        payment_method = (
            request.env["pos.payment.method"]
            .sudo()
            .browse(int(payment_method_id))
        )
        if not payment_method.exists() or not payment_method.use_square_terminal:
            return {"error": "Invalid or non-Square payment method"}
        token = (payment_method.square_access_token or "").strip()
        device_id = (payment_method.square_device_id or "").strip()
        if not token or not device_id:
            return {"error": "Square access token and device ID must be set"}
        # Square amount in cents (integer)
        amount_cents = int(round(float(amount) * 100))
        # Use company currency if not provided (e.g. CAD for Canadian merchants)
        if not currency and payment_method.company_id and payment_method.company_id.currency_id:
            currency = (payment_method.company_id.currency_id.name or "USD").upper()
        currency = (currency or "USD").upper()
        idempotency_key = str(uuid.uuid4())
        reference_id = reference or ("pos-%s" % idempotency_key[:8])
        checkout_note = (note or "Odoo POS").strip()[:500] or "Odoo POS"
        payload = {
            "idempotency_key": idempotency_key,
            "checkout": {
                "amount_money": {"amount": amount_cents, "currency": currency},
                "device_options": {"device_id": device_id},
                "reference_id": reference_id[:50],
                "note": checkout_note,
            },
        }
        if payment_method.square_location_id:
            payload["checkout"]["location_id"] = payment_method.square_location_id.strip()
        url = "%s/v2/terminals/checkouts" % SQUARE_API_BASE
        headers = {
            "Square-Version": SQUARE_API_VERSION,
            "Authorization": "Bearer %s" % token,
        }
        try:
            data = _urlopen_json("POST", url, data=payload, headers=headers, timeout=15)
            checkout = data.get("checkout") or {}
            return {
                "checkout_id": checkout.get("id"),
                "status": checkout.get("status", "PENDING"),
            }
        except HTTPError as e:
            err_msg = "Square API error (%s)" % e.code
            try:
                body = json.loads(e.read().decode("utf-8"))
                if body.get("errors"):
                    err_msg = body["errors"][0].get("detail", err_msg)
            except Exception:
                pass
            _logger.warning("Square create_checkout HTTP error: %s", err_msg)
            return {"error": err_msg}
        except (URLError, OSError, ValueError) as e:
            _logger.exception("Square create_checkout failed")
            return {"error": str(e)}

    @http.route(
        "/pos_square_terminal/checkout_status",
        type="json",
        auth="user",
        methods=["POST"],
    )
    def checkout_status(self, checkout_id, payment_method_id):
        """
        Get Square Terminal checkout status. Returns { "status": "COMPLETED"|"PENDING"|"CANCELED"|... } or { "error": "..." }.
        """
        if not checkout_id:
            return {"error": "Missing checkout_id"}
        payment_method = (
            request.env["pos.payment.method"]
            .sudo()
            .browse(int(payment_method_id or 0))
        )
        if not payment_method.exists() or not payment_method.use_square_terminal:
            return {"error": "Invalid payment method"}
        token = (payment_method.square_access_token or "").strip()
        if not token:
            return {"error": "Square access token not set"}
        url = "%s/v2/terminals/checkouts/%s" % (SQUARE_API_BASE, checkout_id)
        headers = {
            "Square-Version": SQUARE_API_VERSION,
            "Authorization": "Bearer %s" % token,
        }
        try:
            data = _urlopen_get_json(url, headers=headers, timeout=10)
            checkout = data.get("checkout") or {}
            result = {"status": checkout.get("status", "UNKNOWN")}
            if checkout.get("payment_ids"):
                result["payment_ids"] = checkout["payment_ids"]
            return result
        except HTTPError as e:
            err_msg = "Square API error (%s)" % e.code
            try:
                body = json.loads(e.read().decode("utf-8"))
                if body.get("errors"):
                    err_msg = body["errors"][0].get("detail", err_msg)
            except Exception:
                pass
            _logger.warning("Square checkout_status HTTP error: %s", err_msg)
            return {"error": err_msg}
        except (URLError, OSError, ValueError) as e:
            _logger.exception("Square checkout_status failed")
            return {"error": str(e)}

    @http.route(
        "/pos_square_terminal/create_device_code",
        type="json",
        auth="user",
        methods=["POST"],
    )
    def create_device_code(self, payment_method_id, location_id=None, name=None):
        """Create a Square Terminal API device code for pairing. Returns code and pair_by."""
        payment_method = (
            request.env["pos.payment.method"]
            .sudo()
            .browse(int(payment_method_id))
        )
        if not payment_method.exists() or not payment_method.use_square_terminal:
            return {"error": "Invalid or non-Square payment method"}
        token = (payment_method.square_access_token or "").strip()
        if not token:
            return {"error": "Square access token not set"}
        url = "%s/v2/devices/codes" % SQUARE_API_BASE
        headers = {
            "Square-Version": SQUARE_API_VERSION,
            "Authorization": "Bearer %s" % token,
            "Content-Type": "application/json",
        }
        payload = {
            "idempotency_key": str(uuid.uuid4()),
            "device_code": {
                "name": name or "Odoo POS",
                "product_type": "TERMINAL_API",
            },
        }
        if location_id:
            payload["device_code"]["location_id"] = str(location_id).strip()
        try:
            data = _urlopen_json("POST", url, data=payload, headers=headers, timeout=15)
            dc = data.get("device_code") or {}
            return {
                "code": dc.get("code"),
                "pair_by": dc.get("pair_by"),
                "id": dc.get("id"),
                "status": dc.get("status", "UNPAIRED"),
            }
        except HTTPError as e:
            err_msg = "Square API error (%s)" % e.code
            try:
                body = json.loads(e.read().decode("utf-8"))
                if body.get("errors"):
                    err_msg = body["errors"][0].get("detail", err_msg)
            except Exception:
                pass
            _logger.warning("Square create_device_code HTTP error: %s", err_msg)
            return {"error": err_msg}
        except (URLError, OSError, ValueError) as e:
            _logger.exception("Square create_device_code failed")
            return {"error": str(e)}

    @http.route(
        "/pos_square_terminal/cancel_checkout",
        type="json",
        auth="user",
        methods=["POST"],
    )
    def cancel_checkout(self, checkout_id, payment_method_id):
        """Cancel a PENDING or IN_PROGRESS Square Terminal checkout."""
        if not checkout_id:
            return {"error": "Missing checkout_id"}
        payment_method = (
            request.env["pos.payment.method"]
            .sudo()
            .browse(int(payment_method_id or 0))
        )
        if not payment_method.exists() or not payment_method.use_square_terminal:
            return {"error": "Invalid payment method"}
        token = (payment_method.square_access_token or "").strip()
        if not token:
            return {"error": "Square access token not set"}
        url = "%s/v2/terminals/checkouts/%s/cancel" % (SQUARE_API_BASE, checkout_id)
        headers = {
            "Square-Version": SQUARE_API_VERSION,
            "Authorization": "Bearer %s" % token,
            "Content-Type": "application/json",
        }
        try:
            data = _urlopen_json("POST", url, data={}, headers=headers, timeout=10)
            checkout = data.get("checkout") or {}
            return {"status": checkout.get("status", "CANCELED")}
        except HTTPError as e:
            err_msg = "Square API error (%s)" % e.code
            try:
                body = json.loads(e.read().decode("utf-8"))
                if body.get("errors"):
                    err_msg = body["errors"][0].get("detail", err_msg)
            except Exception:
                pass
            _logger.warning("Square cancel_checkout HTTP error: %s", err_msg)
            return {"error": err_msg}
        except (URLError, OSError, ValueError) as e:
            _logger.exception("Square cancel_checkout failed")
            return {"error": str(e)}

    @http.route(
        "/pos_square_terminal/refund_payment",
        type="json",
        auth="user",
        methods=["POST"],
    )
    def refund_payment(self, payment_id, amount, currency, payment_method_id, reason=None):
        """Refund a Square payment (Payments API Refund). amount in monetary units."""
        if not payment_id or not amount or amount <= 0:
            return {"error": "Invalid payment_id or amount"}
        payment_method = (
            request.env["pos.payment.method"]
            .sudo()
            .browse(int(payment_method_id or 0))
        )
        if not payment_method.exists() or not payment_method.use_square_terminal:
            return {"error": "Invalid payment method"}
        token = (payment_method.square_access_token or "").strip()
        if not token:
            return {"error": "Square access token not set"}
        amount_cents = int(round(float(amount) * 100))
        currency = (currency or "CAD").upper()
        url = "%s/v2/refunds" % SQUARE_API_BASE
        headers = {
            "Square-Version": SQUARE_API_VERSION,
            "Authorization": "Bearer %s" % token,
            "Content-Type": "application/json",
        }
        payload = {
            "idempotency_key": str(uuid.uuid4())[:45],
            "payment_id": str(payment_id),
            "amount_money": {"amount": amount_cents, "currency": currency},
            "reason": (reason or "Odoo POS refund")[:192],
        }
        try:
            data = _urlopen_json("POST", url, data=payload, headers=headers, timeout=15)
            ref = data.get("refund") or {}
            return {"refund_id": ref.get("id"), "status": ref.get("status", "PENDING")}
        except HTTPError as e:
            err_msg = "Square API error (%s)" % e.code
            try:
                body = json.loads(e.read().decode("utf-8"))
                if body.get("errors"):
                    err_msg = body["errors"][0].get("detail", err_msg)
            except Exception:
                pass
            _logger.warning("Square refund_payment HTTP error: %s", err_msg)
            return {"error": err_msg}
        except (URLError, OSError, ValueError) as e:
            _logger.exception("Square refund_payment failed")
            return {"error": str(e)}

    @http.route(
        "/pos_square_terminal/issue_receipt",
        type="json",
        auth="user",
        methods=["POST"],
    )
    def issue_receipt(self, payment_id, payment_method_id, device_id=None, print_only=True):
        """Send a receipt request to the Square Terminal (CreateTerminalAction RECEIPT)."""
        if not payment_id:
            return {"error": "Missing payment_id"}
        payment_method = (
            request.env["pos.payment.method"]
            .sudo()
            .browse(int(payment_method_id or 0))
        )
        if not payment_method.exists() or not payment_method.use_square_terminal:
            return {"error": "Invalid payment method"}
        token = (payment_method.square_access_token or "").strip()
        dev_id = (device_id or payment_method.square_device_id or "").strip()
        if not token or not dev_id:
            return {"error": "Square access token and device ID must be set"}
        url = "%s/v2/terminals/actions" % SQUARE_API_BASE
        headers = {
            "Square-Version": SQUARE_API_VERSION,
            "Authorization": "Bearer %s" % token,
            "Content-Type": "application/json",
        }
        payload = {
            "idempotency_key": str(uuid.uuid4()),
            "action": {
                "device_id": dev_id,
                "type": "RECEIPT",
                "receipt_options": {
                    "payment_id": str(payment_id),
                    "print_only": bool(print_only),
                },
            },
        }
        try:
            data = _urlopen_json("POST", url, data=payload, headers=headers, timeout=15)
            action = data.get("action") or {}
            return {"action_id": action.get("id"), "status": action.get("status", "PENDING")}
        except HTTPError as e:
            err_msg = "Square API error (%s)" % e.code
            try:
                body = json.loads(e.read().decode("utf-8"))
                if body.get("errors"):
                    err_msg = body["errors"][0].get("detail", err_msg)
            except Exception:
                pass
            _logger.warning("Square issue_receipt HTTP error: %s", err_msg)
            return {"error": err_msg}
        except (URLError, OSError, ValueError) as e:
            _logger.exception("Square issue_receipt failed")
            return {"error": str(e)}

    @http.route(
        "/pos_square_terminal/refund_order_square",
        type="json",
        auth="user",
        methods=["POST"],
    )
    def refund_order_square(self, order_id, amount=None, reason=None):
        """Refund the first Square payment of this order via Square API. No redirect.
        amount: optional, in monetary units; default = full payment amount.
        reason: optional string.
        """
        if not order_id:
            return {"error": "Missing order_id"}
        order = request.env["pos.order"].sudo().browse(int(order_id))
        if not order.exists():
            return {"error": "Order not found"}
        payment = (
            request.env["pos.payment"]
            .sudo()
            .search([("pos_order_id", "=", order.id), ("square_payment_id", "!=", False)], limit=1)
        )
        if not payment:
            return {"error": "No Square Terminal payment found for this order"}
        refund_amount = amount if amount is not None and amount > 0 else payment.amount
        currency = (payment.currency_id and payment.currency_id.name) or order.currency_id.name or "CAD"
        return self.refund_payment(
            payment_id=payment.square_payment_id,
            amount=refund_amount,
            currency=currency,
            payment_method_id=payment.payment_method_id.id,
            reason=reason or "Odoo POS refund",
        )

    @http.route(
        "/pos_square_terminal/refund_wizard_url",
        type="json",
        auth="user",
        methods=["POST"],
    )
    def refund_wizard_url(self, order_id):
        """Return URL to open the Square refund wizard for the first Square payment of this order."""
        if not order_id:
            return {"error": "Missing order_id"}
        order = request.env["pos.order"].sudo().browse(int(order_id))
        if not order.exists():
            return {"error": "Order not found"}
        payment = (
            request.env["pos.payment"]
            .sudo()
            .search([("pos_order_id", "=", order.id), ("square_payment_id", "!=", False)], limit=1)
        )
        if not payment:
            return {"error": "No Square Terminal payment found for this order"}
        wizard = request.env["square.refund.wizard"].sudo().create({
            "pos_payment_id": payment.id,
            "amount": payment.amount,
            "reason": "Odoo POS refund",
        })
        base = request.httprequest.url_root.rstrip("/")
        url = "%s/web#id=%s&model=square.refund.wizard&view_type=form" % (base, wizard.id)
        return {"url": url}

    @http.route(
        "/pos_square_terminal/order_square_payments",
        type="json",
        auth="user",
        methods=["POST"],
    )
    def order_square_payments(self, order_id):
        """Return list of Square payments for this pos.order (for receipt screen buttons)."""
        if not order_id:
            return {"payments": []}
        order = request.env["pos.order"].sudo().browse(int(order_id))
        if not order.exists():
            return {"payments": []}
        payments = (
            request.env["pos.payment"]
            .sudo()
            .search([("pos_order_id", "=", order.id), ("square_payment_id", "!=", False)])
        )
        return {
            "payments": [
                {
                    "payment_id": p.square_payment_id,
                    "payment_method_id": p.payment_method_id.id,
                    "amount": p.amount,
                }
                for p in payments
            ]
        }
