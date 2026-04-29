# -*- coding: utf-8 -*-
# Copyright 2025 Rafaël, Cursor
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import fields, models


class SquareDeviceCodeWizard(models.TransientModel):
    _name = "square.device.code.wizard"
    _description = "Square Terminal device code for pairing"

    payment_method_id = fields.Many2one(
        "pos.payment.method",
        string="Payment method",
        required=True,
        ondelete="cascade",
    )
    code = fields.Char(string="Device code", readonly=True)
    pair_by = fields.Char(string="Expires at", readonly=True)
