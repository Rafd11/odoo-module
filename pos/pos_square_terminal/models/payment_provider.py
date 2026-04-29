# -*- coding: utf-8 -*-
# Copyright 2025 Rafaël Daoud
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

import json
import logging
import ssl
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

from odoo import api, fields, models
from odoo.exceptions import UserError

from odoo.addons.payment import utils as payment_utils

_logger = logging.getLogger(__name__)

SQUARE_API_BASE = "https://connect.squareup.com"
SQUARE_API_VERSION = "2024-11-20"


def _format_square_error(http_code=None, body=None, fallback="Unknown error"):
    """Build a clear error message from Square API response."""
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
        parts.append("Check that your access token is valid, not expired, and has the required scopes.")
    elif code == "NOT_FOUND":
        parts.append("Check the Application ID, location ID, or resource ID.")
    elif code == "INVALID_REQUEST":
        parts.append("Check the request format and required fields.")
    return " — ".join(parts)


class PaymentProvider(models.Model):
    _inherit = "payment.provider"

    code = fields.Selection(
        selection_add=[("square", "Square")],
        ondelete={"square": "set default"},
    )
    square_application_id = fields.Char(
        string="Square Application ID",
        help="Application ID from Square Developer Dashboard (used by Web Payments SDK on the frontend).",
        required_if_provider="square",
    )
    square_access_token = fields.Char(
        string="Square Access Token",
        help="Access token from Square Developer Dashboard (sandbox or production).",
        required_if_provider="square",
        groups="base.group_system",
    )
    square_location_id = fields.Char(
        string="Square Location ID",
        help="Optional. Default location is used if empty.",
    )

    @api.model
    def _get_payment_method_information(self):
        res = super()._get_payment_method_information()
        res["square"] = {"mode": "unique", "domain": [("type", "=", "bank")]}
        return res

    def _compute_feature_support_fields(self):
        super()._compute_feature_support_fields()
        self.filtered(lambda p: p.code == "square").update({
            "support_express_checkout": False,
            "support_manual_capture": False,
            "support_refund": "partial",
            "support_tokenization": False,
        })

    def _get_default_payment_method_codes(self):
        default_codes = super()._get_default_payment_method_codes()
        if self.code != "square":
            return default_codes
        return ["card"]

    def _should_build_inline_form(self, is_validation=False):
        if self.code == "square":
            return False
        return super()._should_build_inline_form(is_validation=is_validation)

    def action_square_test_connection(self):
        """Test Square credentials by calling the Locations API."""
        self.ensure_one()
        if self.code != "square":
            raise UserError("This action is only for Square providers.")
        token = (self.square_access_token or "").strip()
        if not token:
            raise UserError("Please set the Square Access Token first.")
        url = "%s/v2/locations" % SQUARE_API_BASE
        headers = {
            "Square-Version": SQUARE_API_VERSION,
            "Authorization": "Bearer %s" % token,
            "Content-Type": "application/json",
        }
        try:
            req = Request(url, headers=headers, method="GET")
            with urlopen(req, context=ssl.create_default_context(), timeout=15) as r:
                data = json.loads(r.read().decode("utf-8"))
        except HTTPError as e:
            try:
                body = json.loads(e.read().decode("utf-8"))
            except Exception:
                body = None
            err_msg = _format_square_error(http_code=e.code, body=body, fallback="Request failed.")
            _logger.warning("Square test connection HTTP error: %s", err_msg)
            raise UserError(err_msg)
        except (URLError, OSError, ValueError) as e:
            _logger.exception("Square test connection failed")
            raise UserError("Connection failed: %s" % e)
        if data.get("errors"):
            err_msg = _format_square_error(body=data, fallback="Unknown error")
            raise UserError(err_msg)
        locations = data.get("locations") or []
        count = len(locations)
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Square connection OK",
                "message": "Credentials are valid. %s location(s) found." % count,
                "type": "success",
                "sticky": False,
            },
        }
