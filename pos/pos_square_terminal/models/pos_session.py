# -*- coding: utf-8 -*-
# Copyright 2025 Odoo Community Association (OCA)
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import models


class PosSession(models.Model):
    _inherit = "pos.session"

    def _loader_params_pos_payment_method(self):
        res = super()._loader_params_pos_payment_method()
        fields = res.get("search_params", {}).get("fields", [])
        if "use_square_terminal" not in fields:
            fields = list(fields) + ["use_square_terminal"]
            res.setdefault("search_params", {})["fields"] = fields
        return res
