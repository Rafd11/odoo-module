# -*- coding: utf-8 -*-
# Copyright 2025 Rafaël, Cursor
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models
from odoo.exceptions import UserError


class PosOrder(models.Model):
    _inherit = "pos.order"

    has_square_payment = fields.Boolean(
        string="Has Square payment",
        compute="_compute_has_square_payment",
        help="True if this order has at least one payment made with Square Terminal.",
    )

    def _compute_has_square_payment(self):
        for order in self:
            order.has_square_payment = bool(
                order.payment_ids.filtered("square_payment_id")
            )

    def action_refund_square(self):
        """Open Square refund wizard for this order's first Square payment (for old orders / back office)."""
        self.ensure_one()
        payment = self.env["pos.payment"].search(
            [("pos_order_id", "=", self.id), ("square_payment_id", "!=", False)],
            limit=1,
        )
        if not payment:
            raise UserError(
                "This order has no Square Terminal payment. Refund from the payment list or use another method."
            )
        return payment.action_refund_square()
