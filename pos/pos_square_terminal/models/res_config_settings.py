# -*- coding: utf-8 -*-
# Copyright 2025 Rafaël Daoud
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl).

from odoo import models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    def action_open_square_settings(self):
        """Open Square settings (online payments or POS terminals)."""
        Provider = self.env["payment.provider"].sudo()
        square = Provider.search([("code", "=", "square")], limit=2)
        action = self.env["ir.actions.act_window"]._for_xml_id(
            "pos_square_terminal.action_square_payment_provider"
        )
        if len(square) == 1:
            action["view_mode"] = "form"
            action["res_id"] = square.id
        return action
