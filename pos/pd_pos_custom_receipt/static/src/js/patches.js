/**
 * POS custom receipt patches: add helpers used by the customized templates.
 * We monkey-patch OWL components via prototype extension because templates refer to
 * methods that don't exist in core (parseDiscount, getCurrentDate/Time, etc.).
 */

/** @odoo-module **/

import { OrderReceipt } from "@point_of_sale/app/screens/receipt_screen/receipt/order_receipt";
import { Orderline } from "@point_of_sale/app/generic_components/orderline/orderline";
import { OrderWidget } from "@point_of_sale/app/generic_components/order_widget/order_widget";
import { OrderSummary } from "@point_of_sale/app/screens/product_screen/order_summary/order_summary";
import { PosOrderline } from "@point_of_sale/app/models/pos_order_line";
import { patch } from "@web/core/utils/patch";

// Patch OrderReceipt with helpers used by the custom template
if (OrderReceipt) {
    const ORp = OrderReceipt.prototype;
    // Point the component to our custom template name without overriding the core one.
    OrderReceipt.template = "pos_custom_receipt_ssm.OrderReceipt";
    if (!ORp.parseDiscount) {
        ORp.parseDiscount = function (unitPrice) {
            try {
                if (!unitPrice) return 0;
                const cleaned = String(unitPrice)
                    .replace(/[₹$€Rs]/g, "")
                    .replace(/,/g, "")
                    .replace(/\s+/g, "")
                    .replace(/^-/g, "");
                return parseFloat(cleaned) || 0;
            } catch (e) {
                return 0;
            }
        };
    }
    if (!ORp._num) {
        ORp._num = function (v) {
            if (v === undefined || v === null) return 0;
            const n = parseFloat(String(v).replace(/[₹$€Rs,]/g, "").trim());
            return Number.isNaN(n) ? 0 : n;
        };
    }
    if (!ORp.computeDiscountFromMRP) {
        ORp.computeDiscountFromMRP = function (lines) {
            if (!Array.isArray(lines)) return 0;
            let total = 0;
            for (const l of lines) {
                // Use _mrp directly from the line data
                const mrp = this._num(l?._mrp ?? 0);
                const up = this._num(l?.unitPrice);
                const qty = this._num(l?.qty);
                if (mrp > 0 && qty > 0) {
                    const diff = mrp - up;
                    total += (diff > 0 ? diff : 0) * qty;
                }
            }
            return total;
        };
    }
    if (!ORp.computeMRPSubtotal) {
        ORp.computeMRPSubtotal = function (lines) {
            if (!Array.isArray(lines)) return 0;
            let total = 0;
            for (const l of lines) {
                // Sum of (MRP * qty) for all items
                const mrp = this._num(l?._mrp ?? 0);
                const qty = this._num(l?.qty);
                if (mrp > 0 && qty > 0) {
                    total += mrp * qty;
                }
            }
            return total;
        };
    }
    if (!ORp.getCurrentDate) {
        ORp.getCurrentDate = function () {
            const now = new Date();
            return now.toLocaleDateString();
        };
    }
    if (!ORp.getCurrentTime) {
        ORp.getCurrentTime = function () {
            const now = new Date();
            return now.toLocaleTimeString();
        };
    }
}

// Patch Orderline with helpers used by the custom orderline template
if (Orderline) {
    const OLp = Orderline.prototype;
    // Point to our custom template for orderline
    Orderline.template = "pos_custom_receipt_ssm.Orderline";
    // Allow an optional 'index' prop so our templates can pass S.No without validation errors
    // Also extend line shape to include our custom MRP fields
    try {
        const originalLineShape = Orderline.props.line.shape;
        Orderline.props = { 
            ...Orderline.props, 
            index: { type: Number, optional: true },
            line: {
                shape: {
                    ...originalLineShape,
                    lst_price: { type: Number, optional: true },
                    default_code: { type: String, optional: true },
                    _mrp: { type: Number, optional: true },
                    _lineIndex: { type: Number, optional: true }
                }
            }
        };
    } catch (e) {
        // ignore if props structure differs across versions
        console.warn('Could not extend Orderline props:', e);
    }
    if (!OLp.parseDigitsValue) {
        OLp.parseDigitsValue = function (v) {
            const n = parseFloat(v);
            if (Number.isNaN(n)) return 0;
            return n.toFixed(2);
        };
    }
    if (!OLp.parseSignleValue) {
        OLp.parseSignleValue = function (v) {
            if (v === undefined || v === null) return 0;
            const n = parseFloat(String(v).replace(/[₹$€Rs,]/g, "").trim());
            return Number.isNaN(n) ? 0 : n.toFixed(2);
        };
    }
    if (!OLp.parsePrice) {
        OLp.parsePrice = function (v) {
            const n = parseFloat(String(v).replace(/[₹$€Rs,]/g, "").trim());
            return Number.isNaN(n) ? 0 : n.toFixed(2);
        };
    }
    // Integer-only parser for values like product.default_code
    if (!OLp.parseIntValue) {
        OLp.parseIntValue = function (v) {
            if (v === undefined || v === null) return 0;
            try {
                // Extract first integer substring, e.g., "ABC123X" -> 123
                const m = String(v).match(/-?\d+/);
                if (!m) return 0;
                return parseInt(m[0], 10) || 0;
            } catch (e) {
                return 0;
            }
        };
    }
}

// Use our custom OrderWidget template too
if (OrderWidget) {
    OrderWidget.template = "pos_custom_receipt_ssm.OrderWidget";
    // Provide a merge helper for templates to enrich line display data with product info (e.g., default_code)
    const OWp = OrderWidget.prototype;
    if (!OWp._merge) {
        OWp._merge = function (line) {
            try {
                const product = line.get_product?.() || line.product_id?.raw || {};
                const display = line.getDisplayData ? line.getDisplayData() : {};
                const code = product.default_code || product.barcode || "";
                
                // Use default_code as MRP if it's a valid number, otherwise use lst_price
                const codeAsNumber = parseFloat(code);
                let mrp = 0;
                if (!isNaN(codeAsNumber) && codeAsNumber > 0) {
                    mrp = codeAsNumber;
                } else {
                    mrp = product.lst_price || 0;
                }
                
                return Object.assign({}, display, { default_code: code, _mrp: mrp, lst_price: product.lst_price || 0 });
            } catch (e) {
                return line?.getDisplayData?.() || {};
            }
        };
    }
}

// Light-touch patch: decorate OrderSummary's template context so Orderline gets index and default_code.
if (OrderSummary) {
    const OS = OrderSummary.prototype;
    // Provide helpers the template can call via JS expressions.
    if (!OS._enrichDisplay) {
        OS._enrichDisplay = function (line) {
            try {
                const product = line.get_product?.() || line.product_id?.raw || {};
                const display = line.getDisplayData ? line.getDisplayData() : {};
                return Object.assign({}, display, { default_code: product.default_code });
            } catch (e) {
                return line?.getDisplayData?.() || {};
            }
        };
    }
    if (!OS._lineIndex) {
        OS._lineIndex = function (line) {
            try {
                return this.currentOrder.lines.indexOf(line);
            } catch (e) {
                return 0;
            }
        };
    }
}

// Patch PosOrderline.getDisplayData to include MRP (lst_price) and default_code
patch(PosOrderline.prototype, {
    getDisplayData() {
        const data = super.getDisplayData();
        // Add lst_price (MRP) and default_code (Internal Reference) to the display data
        data.lst_price = this.product_id?.lst_price || 0;
        data.default_code = this.product_id?.default_code || "";
        
        // Use default_code as MRP if it's a valid number, otherwise use lst_price
        const codeAsNumber = parseFloat(data.default_code);
        if (!isNaN(codeAsNumber) && codeAsNumber > 0) {
            data._mrp = codeAsNumber;
        } else {
            data._mrp = data.lst_price;
        }
        
        // Add line index for display
        if (this.order_id && this.order_id.lines) {
            const sortedLines = this.order_id.getSortedOrderlines ? this.order_id.getSortedOrderlines() : this.order_id.lines;
            data._lineIndex = sortedLines.findIndex(l => l.uuid === this.uuid);
        } else {
            data._lineIndex = 0;
        }
        
        return data;
    }
});
