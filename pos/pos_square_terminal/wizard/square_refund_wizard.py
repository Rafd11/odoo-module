# -*- coding: utf-8 -*-
# Copyright 2025 Rafaël, Cursor
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import api, fields, models
from odoo.exceptions import UserError


class SquareRefundWizard(models.TransientModel):
    _name = "square.refund.wizard"
    _description = "Refund Square Terminal payment"

    pos_payment_id = fields.Many2one(
        "pos.payment",
        string="POS Payment",
        required=True,
        ondelete="cascade",
    )
    amount = fields.Monetary(
        string="Amount to refund",
        required=True,
        currency_field="currency_id",
    )
    currency_id = fields.Many2one(
        "res.currency",
        related="pos_payment_id.currency_id",
        readonly=True,
    )
    reason = fields.Char(string="Reason", default="Odoo POS refund")

    def action_refund(self):
        self.ensure_one()
        pay = self.pos_payment_id
        if not pay.square_payment_id:
            raise UserError("This payment has no Square payment ID (not a Square Terminal payment).")
        method = pay.payment_method_id
        if not method or not method.use_square_terminal:
            raise UserError("Payment method is not a Square Terminal method.")
        result = method._square_refund_payment(
            method.square_access_token or "",
            pay.square_payment_id,
            self.amount,
            self.currency_id.name or "CAD",
            self.reason or "",
        )
        if result.get("error"):
            raise UserError(result["error"])
        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "title": "Refund submitted",
                "message": "Square refund has been requested.",
                "type": "success",
                "sticky": False,
            },
        }
