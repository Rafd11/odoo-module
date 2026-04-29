# -*- coding: utf-8 -*-
{
    "name": "Square (POS Terminal & Online Payments)",
    "version": "18.0.2.0.0",
    "category": "Accounting/Payment Providers",
    "summary": "Square Terminal in POS and Square online payments (website).",
    "description": """
        One addon for Square: POS Terminal and Payment Provider.
        - **POS Terminal**: Pay with Square Terminal from Point of Sale; print receipts; refunds in-POS.
        - **Online payments**: Accept card payments on your website with Square Web Payments SDK.
        Configure in Settings → Square (online payments and POS Terminal payment methods).
    """,
    "author": "Rafaël Daoud",
    "license": "LGPL-3",
    "depends": ["point_of_sale", "payment"],
    "data": [
        "security/ir.model.access.csv",
        "views/payment_square_templates.xml",
        "data/payment_provider_data.xml",
        "views/pos_payment_method_views.xml",
        "views/pos_payment_views.xml",
        "views/pos_order_views.xml",
        "views/payment_provider_views.xml",
        "views/square_settings_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "pos_square_terminal/static/src/js/PaymentScreen.js",
            "pos_square_terminal/static/src/xml/PaymentScreen.xml",
            "pos_square_terminal/static/src/js/ReceiptScreen.js",
            "pos_square_terminal/static/src/xml/ReceiptScreen.xml",
            "pos_square_terminal/static/src/xml/OrderReceipt.xml",
        ],
        "web.assets_frontend": [
            "pos_square_terminal/static/src/js/square_checkout.js",
        ],
    },
    "post_init_hook": "post_init_hook",
    "uninstall_hook": "uninstall_hook",
    "installable": True,
    "auto_install": False,
    "application": False,
}
