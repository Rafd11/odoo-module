# -*- coding: utf-8 -*-
# Copyright 2025 Rafaël, Cursor
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models
from odoo.exceptions import UserError


class PosPayment(models.Model):
    _inherit = "pos.payment"

    square_payment_id = fields.Char(
        string="Square Payment ID",
        help="Square payment ID for this payment (used for refunds and receipts).",
    )

    def action_refund_square(self):
        """Open Square refund wizard for this payment."""
        self.ensure_one()
        if not self.square_payment_id:
            raise UserError(
                "This payment has no Square payment ID (not a Square Terminal payment)."
            )
        if not self.payment_method_id or not self.payment_method_id.use_square_terminal:
            raise UserError("Payment method is not a Square Terminal method.")
        wizard = self.env["square.refund.wizard"].create({
            "pos_payment_id": self.id,
            "amount": self.amount,
            "reason": "Odoo POS refund",
        })
        return {
            "type": "ir.actions.act_window",
            "name": "Refund Square payment",
            "res_model": "square.refund.wizard",
            "res_id": wizard.id,
            "view_mode": "form",
            "target": "new",
        }

    def action_print_receipt_square(self):
        """Send receipt to the Square Terminal for this payment."""
        self.ensure_one()
        if not self.square_payment_id:
            raise UserError(
                "This payment has no Square payment ID (not a Square Terminal payment)."
            )
        method = self.payment_method_id
        if not method or not method.use_square_terminal:
            raise UserError("Payment method is not a Square Terminal method.")
        result = method._square_issue_receipt(
            self.square_payment_id,
            device_id=method.square_device_id,
            print_only=True,
        )
        if result.get("error"):
            raise UserError(result["error"])
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Receipt sent",
                "message": "Receipt has been sent to the Square Terminal.",
                "type": "success",
                "sticky": False,
            },
        }
