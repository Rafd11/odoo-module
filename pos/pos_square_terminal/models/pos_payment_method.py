# -*- coding: utf-8 -*-
# Copyright 2025 Rafaël, Cursor
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import json
import logging
import ssl
import uuid
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from odoo import api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

SQUARE_API_BASE = "https://connect.squareup.com"
SQUARE_API_VERSION = "2024-11-20"


def _square_error_message(http_code=None, body=None, fallback="Unknown error"):
    """Build error message with Square code, category, detail and reasoning."""
    parts = []
    if http_code:
        parts.append("HTTP %s" % http_code)
    code = detail = category = None
    if body and isinstance(body, dict) and body.get("errors"):
        err = body["errors"][0]
        code = err.get("code")
        detail = err.get("detail") or fallback
        category = err.get("category")
    else:
        detail = fallback
    if code:
        parts.append("Square code: %s" % code)
    if category:
        parts.append("Category: %s" % category)
    parts.append(detail)
    if code == "UNAUTHORIZED":
        parts.append("Check that your access token is valid and has TERMINAL_API scope.")
    elif code == "NOT_FOUND":
        parts.append("Check the device ID and location ID.")
    return " — ".join(parts)


class PosPaymentMethod(models.Model):
    _inherit = "pos.payment.method"

    use_square_terminal = fields.Boolean(
        string="Use Square Terminal",
        help="When enabled, payments with this method are processed on a Square Terminal device.",
    )
    square_access_token = fields.Char(
        string="Square Access Token",
        help="Square API access token (from Square Developer Dashboard). Use sandbox token for testing.",
    )
    square_device_id = fields.Char(
        string="Square Device ID",
        help="The Square Terminal device ID that will receive the payment request.",
    )
    square_location_id = fields.Char(
        string="Square Location ID",
        help="Optional. Square location ID; if empty, the default location of the token is used.",
    )

    @api.model
    def _load_pos_data_fields(self, config_id):
        """Odoo 18: ensure Square Terminal field is loaded so POS frontend can use it."""
        res = super()._load_pos_data_fields(config_id)
        if "use_square_terminal" not in res:
            res = list(res) + ["use_square_terminal"]
        return res

    @api.onchange("use_square_terminal")
    def _onchange_use_square_terminal(self):
        if self.use_square_terminal and "use_payment_terminal" in self._fields:
            self.use_payment_terminal = True  # so POS calls sendPaymentRequest and waits for terminal
        if not self.use_square_terminal:
            self.square_access_token = False
            self.square_device_id = False
            self.square_location_id = False

    def write(self, vals):
        if vals.get("use_square_terminal") and "use_payment_terminal" in self._fields:
            vals["use_payment_terminal"] = True
        return super().write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get("use_square_terminal") and "use_payment_terminal" in self._fields:
                vals["use_payment_terminal"] = True
        return super().create(vals_list)

    def action_square_terminal_test_connection(self):
        """Test Square Terminal credentials: token via Locations API, then list devices if device_id set."""
        self.ensure_one()
        if not self.use_square_terminal:
            raise UserError("Enable 'Use Square Terminal' first.")
        token = (self.square_access_token or "").strip()
        if not token:
            raise UserError("Please set the Square Access Token first.")
        headers = {
            "Square-Version": SQUARE_API_VERSION,
            "Authorization": "Bearer %s" % token,
            "Content-Type": "application/json",
        }
        ctx = ssl.create_default_context()
        # 1) Verify token with Locations API
        url_locations = "%s/v2/locations" % SQUARE_API_BASE
        try:
            req = Request(url_locations, headers=headers, method="GET")
            with urlopen(req, context=ctx, timeout=15) as r:
                data = json.loads(r.read().decode("utf-8"))
        except HTTPError as e:
            try:
                body = json.loads(e.read().decode("utf-8"))
            except Exception:
                body = None
            err_msg = _square_error_message(http_code=e.code, body=body, fallback="Request failed.")
            _logger.warning("Square terminal test HTTP error: %s", err_msg)
            raise UserError(err_msg)
        except (URLError, OSError, ValueError) as e:
            _logger.exception("Square terminal test failed")
            raise UserError("Connection failed: %s" % e)
        if data.get("errors"):
            raise UserError(_square_error_message(body=data, fallback="Unknown error"))
        locations = data.get("locations") or []
        device_ok = False
        device_id = (self.square_device_id or "").strip()
        if device_id:
            # 2) List devices to verify device_id is known to Square
            url_devices = "%s/v2/devices" % SQUARE_API_BASE
            try:
                req = Request(url_devices, headers=headers, method="GET")
                with urlopen(req, context=ctx, timeout=15) as r:
                    dev_data = json.loads(r.read().decode("utf-8"))
            except HTTPError as e:
                try:
                    body = json.loads(e.read().decode("utf-8"))
                except Exception:
                    body = None
                err_msg = _square_error_message(http_code=e.code, body=body, fallback="Devices request failed.")
                raise UserError(err_msg)
            if not dev_data.get("errors"):
                devices = dev_data.get("devices") or []
                # Square returns id as "device:XXX"; dashboard may show XXX or "device:XXX"
                def _normalize_id(raw):
                    if not raw:
                        return ""
                    s = (raw or "").strip().lower()
                    return s[7:] if s.startswith("device:") else s
                want = _normalize_id(device_id)
                device_ok = any(_normalize_id(d.get("id")) == want for d in devices)
        message = "Credentials are valid. %s location(s) found." % len(locations)
        if device_id:
            message += " Device ID: %s." % ("recognized" if device_ok else "not found in your account (check Device ID)")
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Square Terminal connection OK",
                "message": message,
                "type": "success" if (not device_id or device_ok) else "warning",
                "sticky": False,
            },
        }

    def action_create_square_device_code(self):
        """Create a Square Terminal API device code for pairing. Opens wizard with code."""
        self.ensure_one()
        if not self.use_square_terminal:
            raise UserError("Enable 'Use Square Terminal' first.")
        token = (self.square_access_token or "").strip()
        if not token:
            raise UserError("Square access token not set.")
        url = "%s/v2/devices/codes" % SQUARE_API_BASE
        headers = {
            "Square-Version": SQUARE_API_VERSION,
            "Authorization": "Bearer %s" % token,
            "Content-Type": "application/json",
        }
        location_id = (self.square_location_id or "").strip() or None
        payload = {
            "idempotency_key": str(uuid.uuid4()),
            "device_code": {
                "name": "Odoo POS",
                "product_type": "TERMINAL_API",
            },
        }
        if location_id:
            payload["device_code"]["location_id"] = location_id
        try:
            req = Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            ctx = ssl.create_default_context()
            with urlopen(req, context=ctx, timeout=15) as r:
                data = json.loads(r.read().decode("utf-8"))
        except HTTPError as e:
            try:
                body = json.loads(e.read().decode("utf-8"))
            except Exception:
                body = None
            err_msg = _square_error_message(http_code=e.code, body=body, fallback="Request failed.")
            _logger.warning("Square create device code HTTP error: %s", err_msg)
            raise UserError(err_msg)
        except (URLError, OSError, ValueError) as e:
            _logger.exception("Square create device code failed")
            raise UserError("Connection failed: %s" % e) from e
        dc = data.get("device_code") or {}
        if data.get("errors"):
            raise UserError(_square_error_message(body=data, fallback="Unknown error"))
        wizard = self.env["square.device.code.wizard"].create({
            "payment_method_id": self.id,
            "code": dc.get("code", ""),
            "pair_by": dc.get("pair_by"),
        })
        return {
            "type": "ir.actions.act_window",
            "name": "Pair Square Terminal",
            "res_model": "square.device.code.wizard",
            "res_id": wizard.id,
            "view_mode": "form",
            "target": "new",
        }

    def _square_refund_payment(self, token, payment_id, amount, currency, reason=""):
        """Call Square Payments API to refund. Returns dict with refund_id/status or error."""
        self.ensure_one()
        amount_cents = int(round(float(amount) * 100))
        currency = (currency or "CAD").upper()
        url = "%s/v2/refunds" % SQUARE_API_BASE
        headers = {
            "Square-Version": SQUARE_API_VERSION,
            "Authorization": "Bearer %s" % (token or self.square_access_token or "").strip(),
            "Content-Type": "application/json",
        }
        payload = {
            "idempotency_key": str(uuid.uuid4())[:45],
            "payment_id": str(payment_id),
            "amount_money": {"amount": amount_cents, "currency": currency},
            "reason": (reason or "Odoo POS refund")[:192],
        }
        try:
            req = Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            ctx = ssl.create_default_context()
            with urlopen(req, context=ctx, timeout=15) as r:
                data = json.loads(r.read().decode("utf-8"))
        except HTTPError as e:
            try:
                body = json.loads(e.read().decode("utf-8"))
            except Exception:
                body = None
            return {"error": _square_error_message(http_code=e.code, body=body, fallback="Refund failed")}
        except (URLError, OSError, ValueError) as e:
            _logger.exception("Square refund failed")
            return {"error": str(e)}
        if data.get("errors"):
            return {"error": _square_error_message(body=data, fallback="Refund failed")}
        ref = data.get("refund") or {}
        return {"refund_id": ref.get("id"), "status": ref.get("status", "PENDING")}

    def _square_issue_receipt(self, payment_id, device_id=None, print_only=True):
        """Send receipt to Square Terminal. Returns dict with action_id/status or error."""
        self.ensure_one()
        token = (self.square_access_token or "").strip()
        dev_id = (device_id or self.square_device_id or "").strip()
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
            req = Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers=headers,
                method="POST",
            )
            ctx = ssl.create_default_context()
            with urlopen(req, context=ctx, timeout=15) as r:
                data = json.loads(r.read().decode("utf-8"))
        except HTTPError as e:
            try:
                body = json.loads(e.read().decode("utf-8"))
            except Exception:
                body = None
            return {"error": _square_error_message(http_code=e.code, body=body, fallback="Issue receipt failed")}
        except (URLError, OSError, ValueError) as e:
            _logger.exception("Square issue_receipt failed")
            return {"error": str(e)}
        if data.get("errors"):
            return {"error": _square_error_message(body=data, fallback="Issue receipt failed")}
        action = data.get("action") or {}
        return {"action_id": action.get("id"), "status": action.get("status", "PENDING")}
