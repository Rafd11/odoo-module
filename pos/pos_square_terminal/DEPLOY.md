# Deploy / upgrade POS Square Terminal on server

After copying the module to the server (e.g. `ct105`), run the following so the payment flow and device code button work.

## 1. Upgrade the module

From the Odoo root (or with correct python/odoo-bin path):

```bash
# Replace with your Odoo command and config
./odoo-bin -c /path/to/odoo.conf -u pos_square_terminal --stop-after-init
```

Or from the UI: **Apps** → search **POS Square Terminal** → **Upgrade**.

## 2. Restart Odoo

Restart the Odoo service so new assets (JS/XML) are loaded:

```bash
sudo systemctl restart odoo
# or
sudo service odoo restart
```

## 3. Clear browser cache for POS

- Hard refresh: **Ctrl+Shift+R** (Windows/Linux) or **Cmd+Shift+R** (Mac).
- Or clear cache for the site, then reopen Point of Sale.

## 4. Verify

- **Device code**: Settings → Square → POS Terminal payment methods → open your Square Terminal method. You should see **Create device code (pair new terminal)** next to the Device ID field.
- **Payment**: In POS, add items, go to payment, select **Square Terminal** and tap Pay. You should see “Connecting to Square…”, then “Waiting for payment on terminal…” and the physical terminal should show the amount. Only after paying on the terminal does Odoo show “Payment successful”.
