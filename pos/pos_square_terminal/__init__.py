# -*- coding: utf-8 -*-
from . import models
from . import controllers
from . import wizard


def post_init_hook(env):
    import odoo.addons.payment as payment
    payment.setup_provider(env, "square")
    menu = env.ref("pos_square_terminal.menu_square_settings_root", raise_if_not_found=False)
    settings_root = env.ref("base.menu_administration", raise_if_not_found=False)
    if menu and settings_root and menu.parent_id != settings_root:
        menu.parent_id = settings_root


def uninstall_hook(env):
    import odoo.addons.payment as payment
    payment.reset_payment_provider(env, "square")
