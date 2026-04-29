==================
POS Custom Receipt
==================

Professional receipt customization with enhanced layout, detailed order lines, and modern styling.

Features
========

* **Enhanced Receipt Header**: Date and time display at the top-right
* **Tabular Order Lines**: Clean layout with No | Item | Qty | MRP | Disc | Net columns
* **Detailed Calculations**: Accurate subtotal and discount computation
* **Item Count Summary**: Total number of items in each order
* **Payment Details**: Clear breakdown of payment methods and change
* **Professional Styling**: Modern SCSS styling for better presentation
* **Partner Form Enhancement**: Improved customer information display
* **Non-Intrusive**: Template inheritance without core file modifications

Installation
============

1. Download and extract the module to your Odoo addons directory
2. Add the addons path to your ``odoo.conf`` if not already included
3. Restart your Odoo server
4. Go to **Apps** menu and click **Update Apps List**
5. Search for **"POS Custom Receipt"**
6. Click **Install**

Configuration
=============

No configuration needed! Once installed, the custom receipt layout automatically applies to all POS sessions.

Usage
=====

The module automatically enhances your POS receipts with:

* Professional tabular layout for order lines
* Date and time information
* Detailed price breakdowns
* Enhanced payment information

Technical Details
=================

:Module Name: pos_custom_receipt
:Version: 18.0.1.0.0
:Category: Point of Sale
:License: LGPL-3
:Dependencies: point_of_sale
:Compatibility: Odoo 18.0 Community & Enterprise

How It Works
============

This module uses Odoo's template inheritance system:

* Extends ``point_of_sale.OrderReceipt`` and ``point_of_sale.Orderline``
* Adds JavaScript patches for helper methods
* Injects custom styles via SCSS
* Follows Odoo best practices for maintainability

Support
=======

For support, feature requests, or bug reports:

* Email: odoo@processdrive.com
* Maintainer: ProcessDrive

Credits
=======

Contributors
------------

* ProcessDrive

Maintainer
----------

This module is maintained by ProcessDrive.
