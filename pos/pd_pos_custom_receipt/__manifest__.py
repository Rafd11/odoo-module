# -*- coding: utf-8 -*-
{
    'name': 'POS Custom Receipt',
    'summary': 'Professional receipt customization with enhanced layout, detailed order lines, and modern styling',
    'description': """
POS Custom Receipt - Professional Receipt Layout
=================================================

Transform your Odoo Point of Sale receipts with a professional, customizable layout.

Key Features:
-------------
* Enhanced receipt header with date and time display
* Tabular order lines with columns: No | Item | Qty | MRP | Disc | Net
* Detailed subtotal and discount calculations
* Total item count summary
* Clear payment details and change display
* Professional SCSS styling
* Improved partner form display
* Non-intrusive template inheritance

Technical Highlights:
--------------------
* Uses Odoo template inheritance (no core file modifications)
* JavaScript patches for extended functionality
* Custom XML templates for receipt rendering
* SCSS stylesheets for professional appearance
* Clean, maintainable architecture

Perfect for retail businesses seeking professional, detailed receipts.
    """,
    'version': '19.0.1.0.0',
    'category': 'Point of Sale',
    'author': 'ProcessDrive India Pvt Ltd',
    'website': 'https://www.processdrive.com/odoo',
    'support': 'odoo@processdrive.com',
    'maintainer': 'ProcessDrive',
    'license': 'LGPL-3',
    
    # Dependencies
    'depends': ['point_of_sale'],
    
    # Data files
    'data': [],
    
    # Assets
    'assets': {
        'point_of_sale._assets_pos': [
            'pd_pos_custom_receipt/static/src/js/patches.js',
            'pd_pos_custom_receipt/static/src/xml/order_receipt.xml',
            'pd_pos_custom_receipt/static/src/xml/orderline.xml',
            'pd_pos_custom_receipt/static/src/xml/order_widget.xml',
            'pd_pos_custom_receipt/static/src/scss/receipt.scss',
            'pd_pos_custom_receipt/static/src/scss/partner_form.scss',
        ],
    },
    
    
    'currency': 'EUR',
    'price': 0.00,
    "installable": True,
    "application": False,
    
    'images': ['static/description/banner.png',]
}
