# POS Square Terminal

Odoo 19 addon to accept **in-person card payments** with **Square Terminal** from Point of Sale. The customer pays on the Square device; receipts can be printed from POS as usual.

## Features

- Configure one or more POS payment methods to use a Square Terminal.
- From the POS payment screen, select the Square method and validate: the amount is sent to the terminal, and the POS waits until the customer completes payment on the device.
- Standard POS receipt printing after payment (Odoo receipt, not the terminal’s).

## Requirements

- Odoo 19.0
- **point_of_sale**
- Square account and a Square Terminal device
- Square API **access token** and **device ID** (see below)

## Configuration

1. **Square Developer Dashboard**
   - Go to [Square Developer](https://developer.squareup.com/), create or open an application.
   - Get an **Access Token** (sandbox for testing, production for live).
   - Under **Terminal**, register your terminal and note the **Device ID** (or list devices via API).
   - Optionally note your **Location ID** (used by the Terminal API).

2. **Odoo**
   - Install the app **POS Square Terminal**.
   - Go to **Point of Sale → Configuration → Payment Methods**.
   - Create or edit a payment method:
     - Check **Use Square Terminal**.
     - Set **Square Access Token** (sandbox or production).
     - Set **Square Device ID**.
     - Set **Square Location ID** if required by your Square account.
   - Assign the payment method to the desired POS(s).

## Usage

1. Open a POS session.
2. Add products and go to the payment screen.
3. Select the **Square Terminal** payment method and the amount.
4. Validate: the amount is sent to the Square Terminal; the customer pays on the device (card, etc.).
5. When the payment is completed on the terminal, the POS records the payment and you can print the receipt as usual.

## Technical notes

- The addon uses Square’s **Terminal API** (`Create Terminal Checkout`, `Get Terminal Checkout`). No IoT box required.
- Amount is sent in the currency of the POS (default USD); amount is converted to cents for the API.
- If the import path for `PaymentScreen` or the RPC helper differs in your Odoo 19 version, adjust the JS import in `static/src/js/PaymentScreen.js` (e.g. `@point_of_sale/js/...` vs `@point_of_sale/app/...`).
- Access token is stored on the payment method and used only server-side; it is not sent to the POS frontend.

## License

LGPL-3.0
